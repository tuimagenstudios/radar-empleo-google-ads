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
import html as html_lib
import logging
import os
import re
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

def _texto(fragmento: str) -> str:
    sin_etiquetas = re.sub(r"<[^>]+>", " ", fragmento)
    return html_lib.unescape(re.sub(r"\s+", " ", sin_etiquetas)).strip()


def analizar_bumeran(correo: Correo, fuente: str) -> list[RawJob]:
    """Las alertas de Bumeran traen una tarjeta por aviso: <a href> con un <h3> (título) y,
    debajo, párrafos con empresa, lugar, carga horaria y modalidad (RF-REC-03)."""
    ofertas: list[RawJob] = []
    for h3 in re.finditer(r"<h3[^>]*>(.*?)</h3>", correo.html, flags=re.S):
        titulo = _texto(h3.group(1))
        enlaces = re.findall(r'<a[^>]+href="([^"]+)"', correo.html[: h3.start()])
        if not titulo or not enlaces:
            continue
        # La tarjeta termina donde empieza el siguiente <a> o <h3>.
        resto = correo.html[h3.end():]
        corte = re.search(r"<a[^>]+href=|<h3", resto)
        tarjeta = resto[: corte.start()] if corte else resto
        parrafos = [_texto(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", tarjeta, flags=re.S)]
        parrafos = [p for p in parrafos if p]
        empresa = parrafos[0] if parrafos else ""
        ubicacion = parrafos[1] if len(parrafos) > 1 else ""
        extras = " · ".join(parrafos[2:4])
        previo = correo.html[max(0, h3.start() - 1500): h3.start()]
        publicada = next((_texto(t) for t in re.findall(r"(Publicado[^<]*)<", previo)), "")
        ofertas.append(RawJob(
            fuente=fuente, titulo=titulo, url=enlaces[-1], empresa=empresa,
            ubicacion=ubicacion, descripcion=extras, publicada=publicada,
            id_externo=f"bumeran:{titulo}:{empresa}",
        ))
    return ofertas


def analizar_sin_ofertas(correo: Correo, fuente: str) -> list[RawJob]:
    """Computrabajo solo manda un aviso con la cantidad de vacantes y un botón: no trae las
    ofertas, así que no hay nada que leer. Se registra y se sigue."""
    log.info("Correo %s de %s sin ofertas en el cuerpo: se saltea", correo.id,
             dominio(correo.remitente))
    return []


# dominio del remitente → función que extrae las ofertas del correo.
ANALIZADORES: dict[str, Analizador] = {
    "bumeran.com": analizar_bumeran,
    "bumeran.com.ar": analizar_bumeran,
    "computrabajo.com": analizar_sin_ofertas,
}


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
