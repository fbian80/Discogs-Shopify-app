import os
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Variables de entorno en Render
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN", "")
DISCOGS_USERNAME = os.getenv("DISCOGS_USERNAME", "")
SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL", "")
SHOPIFY_CLIENT_ID = os.getenv("SHOPIFY_CLIENT_ID", "")
SHOPIFY_CLIENT_SECRET = os.getenv("SHOPIFY_CLIENT_SECRET", "")

SHOPIFY_API_VERSION = "2025-10"


def get_shopify_access_token():
    """Solicita el token mediante Client Credentials enviando los parámetros en el body."""
    clean_store = SHOPIFY_STORE_URL.replace("https://", "").replace("/", "").strip()

    # Endpoint directo de la API Admin de Shopify
    url = f"https://{clean_store}/admin/oauth/access_token"

    payload = {
        "client_id": SHOPIFY_CLIENT_ID,
        "client_secret": SHOPIFY_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }

    headers = {
        "Content-Type": "application/x-www-fo