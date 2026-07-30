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
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "")

def get_shopify_token():
    """Genera dinámicamente el token shpat_ usando Client Credentials Grant."""
    url = f"https://{SHOPIFY_STORE_URL}/admin/oauth/access_token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": SHOPIFY_CLIENT_ID,
        "client_secret": SHOPIFY_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    res = requests.post(url, data=payload, headers=headers, timeout=10)
    if res.status_code == 200:
        return res.json().get("access_token")
    else:
        raise Exception(f"Error generando token de Shopify ({res.status_code}): {res.text}")

@app.get("/", response_class=HTMLResponse)
async def get_collection(request: Request):
    """Obtiene la colección de Discogs y la muestra en la app web."""
    if not DISCOGS_USERNAME or not DISCOGS_TOKEN:
        return HTMLResponse(
            content="<h3>Error de configuración:</h3><p>Falta configurar 'DISCOGS_USERNAME' o 'DISCOGS_TOKEN' en Render.</p>"
        )

    url = f"https://api.discogs.com/users/{DISCOGS_USERNAME}/collection/folders/0/releases?per_page=50&sort=added&sort_order=desc"
    headers = {
        "User-Agent": "MusicalesSanJoseSync/1.0",
        "Authorization": f"Discogs token={DISCOGS_TOKEN}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return HTMLResponse(
                content=f"<h3>Error al conectar con Discogs ({response.status_code}):</h3><p>{response.text}</p>"
            )
            
        data = response.json()
        items = []
        
        for release in data.get("releases", []):
            info = release.get("basic_information", {})
            artists = info.get("artists", [])
            artist_name = artists[0].get("name", "Artista Desconocido") if artists else "Artista Desconocido"
            formats = info.get("formats", [])
            format_name = formats[0].get("name", "Vinilo") if formats else "Vinilo"
            
            items.append({
                "id": release.get("id"),
                "instance_id": release.get("instance_id"),
                "title": info.get("title", "Sin título"),
                "artist": artist_name,
                "year": info.get("year", "N/A"),
                "cover_image": info.get("cover_image", ""),
                "format": format_name,
                "genres": ", ".join(info.get("genres", [])),
            })
                
        return templates.TemplateResponse(request=request, name="index.html", context={"items": items})

    except Exception as e:
        return HTMLResponse(content=f"<h3>Error inesperado en el servidor:</h3><p>{str(e)}</p>")


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
    try:
        # 1. Obtener el token de acceso actualizado dinámicamente
        shopify_token = get_shopify_token()
        
        # 2. Publicar el producto en Shopify
        url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products.json"
        headers = {
            "X-Shopify-Access-Token": shopify_token,
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
        
        res = requests.post(url, json=product_data, headers=headers, timeout=10)
        
        if res.status_code in [200, 201]:
            return {"status": "success", "message": f"'{artist} - {title}' publicado con éxito en Shopify."}
        else:
            return {"status": "error", "message": f"Error de Shopify ({res.status_code}): {res.text}"}
            
    except Exception as e:
        return {"status": "error", "message": f"Excepción al sincronizar: {str(e)}"}
