import os
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Configuración mediante variables de entorno
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN", "")
DISCOGS_USERNAME = os.getenv("DISCOGS_USERNAME", "")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN", "")

@app.get("/", response_class=HTMLResponse)
async def get_collection(request: Request):
    """Obtiene la colección de Discogs y la muestra en la app web."""
    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/collection/folders/0/releases?per_page=50&sort=added&sort_order=desc"
    headers = {
        "User-Agent": "MusicalesSanJoseSync/1.0",
        "Authorization": f"Discogs token={DISCOGS_TOKEN}"
    }
    
    response = requests.get(url, headers=headers)
    items = []
    
    if response.status_code == 200:
        data = response.json()
        for release in data.get("releases", []):
            info = release.get("basic_information", {})
            items.append({
                "id": release.get("id"),
                "instance_id": release.get("instance_id"),
                "title": info.get("title"),
                "artist": info.get("artists", [{}])[0].get("name", "Artista Desconocido"),
                "year": info.get("year", "N/A"),
                "cover_image": info.get("cover_image"),
                "format": info.get("formats", [{}])[0].get("name", "Vinilo"),
                "genres": ", ".join(info.get("genres", [])),
            })
            
    return templates.TemplateResponse("index.html", {"request": request, "items": items})


@app.post("/sync-item")
async def sync_item(
    release_id: str = Form(...),
    title: str = Form(...),
    artist: str = Form(...),
    price: str = Form(...),
    cover_image: str = Form(...),
    genres: str = Form(...)
):
    """Crea el producto directamente en Shopify."""
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    product_data = {
        "product": {
            "title": f"{artist} - {title}",
            "body_html": f"<p><strong>Artista:</strong> {artist}</p><p><strong>Álbum:</strong> {title}</p><p><strong>Género:</strong> {genres}</p>",
            "vendor": artist,
            "product_type": "Música / Vinilos",
            "tags": genres,
            "variants": [
                {
                    "price": price,
                    "sku": f"DISCOGS-{release_id}",
                    "inventory_management": "shopify",
                    "inventory_quantity": 1
                }
            ],
            "images": [{"src": cover_image}] if cover_image else []
        }
    }
    
    res = requests.post(url, json=product_data, headers=headers)
    
    if res.status_code in [200, 201]:
        return {"status": "success", "message": f"'{artist} - {title}' publicado con éxito en Shopify."}
    else:
        return {"status": "error", "message": res.text}
