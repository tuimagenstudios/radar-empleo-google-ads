"""Autoriza al Radar a LEER tu Gmail y guarda el permiso en .env (se usa una sola vez).

Uso: python -m radar.gmail_auth

Necesita GMAIL_CLIENT_ID y GMAIL_CLIENT_SECRET en .env (cliente OAuth de tipo
"Aplicación de escritorio" en Google Cloud). Abre el navegador para que aceptes el
permiso de solo lectura, recibe la respuesta en localhost y escribe
GMAIL_REFRESH_TOKEN en .env. Ningún secreto se muestra en pantalla.
"""

from __future__ import annotations

import http.server
import re
import secrets
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import requests
from dotenv import dotenv_values

SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
PUERTO = 8765


def guardar_en_env(ruta: Path, clave: str, valor: str) -> None:
    texto = ruta.read_text(encoding="utf-8") if ruta.exists() else ""
    linea = f"{clave}={valor}"
    if re.search(rf"(?m)^{clave}=.*$", texto):
        texto = re.sub(rf"(?m)^{clave}=.*$", lambda _: linea, texto)
    else:
        texto = texto.rstrip("\n") + f"\n{linea}\n"
    ruta.write_text(texto, encoding="utf-8")


def main() -> int:
    env_path = Path(".env")
    env = dotenv_values(env_path)
    client_id, client_secret = env.get("GMAIL_CLIENT_ID"), env.get("GMAIL_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Faltan GMAIL_CLIENT_ID y GMAIL_CLIENT_SECRET en .env (ver docs/guia-gmail.md).")
        return 2

    estado = secrets.token_urlsafe(16)
    redirect = f"http://127.0.0.1:{PUERTO}/"
    resultado: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            if params.get("state") == estado:
                resultado.update(params)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Listo. Ya podés cerrar esta pestaña.</h2>".encode())

        def log_message(self, *args):
            pass

    servidor = http.server.HTTPServer(("127.0.0.1", PUERTO), Handler)
    hilo = threading.Thread(target=servidor.handle_request, daemon=True)
    hilo.start()

    url = AUTH_URL + "?" + urllib.parse.urlencode({
        "client_id": client_id, "redirect_uri": redirect, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "state": estado,
    })
    print("Abriendo el navegador para que autorices el acceso de SOLO LECTURA a Gmail...")
    webbrowser.open(url)
    hilo.join(timeout=300)
    servidor.server_close()

    if "code" not in resultado:
        print("No llegó la autorización (¿cerraste la pestaña o pasaron 5 minutos?).")
        return 1
    resp = requests.post(TOKEN_URL, data={
        "code": resultado["code"], "client_id": client_id, "client_secret": client_secret,
        "redirect_uri": redirect, "grant_type": "authorization_code",
    }, timeout=20)
    refresh = resp.json().get("refresh_token") if resp.ok else None
    if not refresh:
        print(f"Google no devolvió el permiso (código {resp.status_code}).")
        return 1
    guardar_en_env(env_path, "GMAIL_REFRESH_TOKEN", refresh)
    print("Permiso guardado en .env como GMAIL_REFRESH_TOKEN. No se mostró en pantalla.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
