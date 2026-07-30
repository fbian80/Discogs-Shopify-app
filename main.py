import os
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Variables de entorno configuradas en Render
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN", "")
DISCOGS_USERNAME = os.getenv("DISCOGS_USERNAME", "")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "")


def get_shopify_access_token():
    """Genera un token de acceso dinámico en Shopify usando Client Credentials."""
    clean_store = SHOPIFY_STORE_URL.replace("https://", "").replace("/", "").strip()
    url = f"https://{clean_store}/admin/oauth/access_token"

    payload = {
        "client_id": SHOPIFY_CLIENT_ID,
        "client_secret": SHOPIFY_CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    }

    res = requests.post(url, json=payload, headers=headers, timeout=15)

    if res.status_code == 200:
        return res.json().get("access_token")
    else:
        raise Exception(
            f"Error al obtener token de Shopify ({res.status_code}): {res.text}"
        )


@app.get("/", response_class=HTMLResponse)
async def get_collection(request: Request):
    """Obtiene la colección de Discogs y la muestra en la plantilla HTML."""
    if not DISCOGS_USERNAME or not DISCOGS_TOKEN:
        return HTMLResponse(
            content="<h3>Configuración incompleta:</h3><p>Falta 'DISCOGS_USERNAME' o 'DISCOGS_TOKEN' en Render.</p>"
        )

    url = f"https://
