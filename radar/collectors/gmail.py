"""Alertas de empleo por correo, leídas con la API de Gmail (RF-REC-02).

- Permiso de SOLO LECTURA (`gmail.readonly`, RNF-SEG-02): no etiqueta ni modifica
  correos. Lee las alertas de los últimos días y la base evita los repetidos.
- Solo pide correos de los remitentes de los portales configurados: nunca recorre
  el resto de la bandeja.
- Cada portal tiene su analizador (`ANALIZADORES`). Un correo de un remitente sin
  analizador se registra y se saltea, sin frenar la ejecución (RF-ERR-06).

Credenciales en el entorno: GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET y GMAIL_REFRESH_TOKEN.
El refresh token se obtiene una sola vez con `python -m radar.gmail_auth`.
"""

from __future__ import annotations

import base64
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass

import requests

from radar.collectors.base import Collector
from radar.models import RawJob

log = logging.getLogger("radar")

TOKEN_URL = "https://oauth2.googleapis.com/token"
API = "https://gmail.googleapis.com/gmail/v1/users/me"
ENV = ("GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN")


@dataclass
class Correo:
    id: str
    remitente: str
    asunto: str
    html: str
    texto: str


Analizador = Callable[[Correo, str], list[RawJob]]

# dominio del remitente → función que extrae las ofertas del correo.
# Se completan con correos reales en tests/fixtures/ (RF-REC-03).
ANALIZADORES: dict[str, Analizador] = {}


def dominio(remitente: str) -> str:
    direccion = remitente.rsplit("<", 1)[-1].rstrip(">").strip().lower()
    host = direccion.rsplit("@", 1)[-1]
    partes = host.split(".")
    # "alertas.bumeran.com.ar" → "bumeran.com.ar"; "mail.indeed.com" → "indeed.com"
    corte = 3 if len(partes) >= 3 and len(partes[-1]) == 2 and partes[-2] in {"com", "co"} \
        else 2
    return ".".join(partes[-corte:])


def _decodificar(data: str) -> str:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")


def _cuerpos(payload: dict) -> tuple[str, str]:
    """Devuelve (html, texto) recorriendo las partes MIME."""
    html = texto = ""
    pendientes = [payload]
    while pendientes:
        parte = pendientes.pop()
        pendientes.extend(parte.get("parts") or [])
        data = (parte.get("body") or {}).get("data")
        if not data:
            continue
        if parte.get("mimeType") == "text/html" and not html:
            html = _decodificar(data)
        elif parte.get("mimeType") == "text/plain" and not texto:
            texto = _decodificar(data)
    return html, texto


def a_correo(mensaje: dict) -> Correo:
    payload = mensaje.get("payload") or {}
    headers = {h["name"].lower(): h["value"] for h in payload.get("headers") or []}
    html, texto = _cuerpos(payload)
    return Correo(mensaje["id"], headers.get("from", ""), headers.get("subject", ""),
                  html, texto)


class GmailCollector(Collector):
    requiere_env = ENV

    def __init__(self, fuente, config, session: requests.Session | None = None):
        super().__init__(fuente, config)
        self.session = session or requests.Session()

    def _token(self) -> str:
        resp = self.session.post(TOKEN_URL, data={
            "client_id": os.environ["GMAIL_CLIENT_ID"],
            "client_secret": os.environ["GMAIL_CLIENT_SECRET"],
            "refresh_token": os.environ["GMAIL_REFRESH_TOKEN"],
            "grant_type": "refresh_token",
        }, timeout=20)
        if resp.status_code >= 400:
            # invalid_grant = token vencido o revocado (RF-ERR-04)
            raise RuntimeError("Gmail rechazó el acceso: renová el permiso con "
                               "python -m radar.gmail_auth")
        return resp.json()["access_token"]

    def consulta(self) -> str:
        remitentes = " OR ".join(self.fuente.get("remitentes", []))
        return f"from:({remitentes}) newer_than:{int(self.fuente.get('dias', 3))}d"

    def fetch(self) -> list[RawJob]:
        cabecera = {"Authorization": f"Bearer {self._token()}"}
        resp = self.session.get(f"{API}/messages", headers=cabecera, timeout=20,
                                params={"q": self.consulta(), "maxResults": 100})
        resp.raise_for_status()
        jobs: list[RawJob] = []
        for ref in resp.json().get("messages", []):
            r = self.session.get(f"{API}/messages/{ref['id']}", headers=cabecera,
                                 params={"format": "full"}, timeout=20)
            r.raise_for_status()
            correo = a_correo(r.json())
            analizador = ANALIZADORES.get(dominio(correo.remitente))
            if analizador is None:
                log.warning("Sin analizador para %s (correo %s): se saltea",
                            dominio(correo.remitente), correo.id)
                continue
            try:
                jobs += analizador(correo, self.nombre)
            except Exception:  # un formato nuevo no frena al resto (RF-ERR-06)
                log.exception("No se pudo analizar el correo %s", correo.id)
        return jobs
