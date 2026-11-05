"""Mensajes de Telegram con la voz de la marca (sección 7 del diseño, RF-NOT-*)."""

from __future__ import annotations

import html
import time
from dataclasses import dataclass
from datetime import datetime

import requests

from radar.classifier import nombre_pais
from radar.locations import BY_CODE, LATAM
from radar.models import Clasificacion, Job

API = "https://api.telegram.org/bot{token}/{method}"
MAX_CHARS = 4096
_MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
_MODALIDAD = {"remoto": "Remoto", "hibrido": "Híbrido", "presencial": "Presencial",
              "sin_especificar": "Modalidad sin especificar"}


def esc(text: str | None) -> str:
    """Escapa texto para el modo HTML de Telegram (RF-NOT-04)."""
    return html.escape(text or "", quote=False)


def paises_txt(job: Job) -> str:
    h = job.paises_habilitados
    if "*" in h:
        return "Cualquier país"
    if h >= LATAM:
        extra = sorted(h - LATAM)
        return "LATAM" + "".join(f" + {nombre_pais(c)}" for c in extra)
    if h:
        return "Solo " + ", ".join(sorted(nombre_pais(c) for c in h))
    return "Países sin especificar"


def experiencia_txt(job: Job) -> str:
    if job.exp_min is None:
        return "sin especificar"
    if job.exp_min == 0 and not job.exp_max:
        return "sin experiencia"
    if job.exp_max is not None and job.exp_max != job.exp_min:
        return f"{job.exp_min}–{job.exp_max} años"
    return f"{job.exp_min}+ años"


def format_job(job: Job) -> str:
    r = job.raw
    clase = job.clasificacion or Clasificacion.REVISAR
    bandera = BY_CODE[job.pais].flag + " " if job.pais in BY_CODE else ""
    titulo = f"{clase.emoji} <b>{esc(r.titulo)}</b>"
    if r.empresa:
        titulo += f" — {esc(r.empresa)}"
    lineas = [
        titulo,
        "",
        f"🌍 {bandera}{_MODALIDAD[job.modalidad]} · {esc(paises_txt(job))}",
    ]
    if job.terminos:
        lineas.append(f"🧩 {esc(' · '.join(job.terminos[:5]))}")
    lineas += [
        f"🎓 Experiencia: {experiencia_txt(job)}",
        f"💰 Salario: {esc(r.salario) or 'no publicado'}",
        "",
        f"<i>Por qué: {esc(job.motivo)}</i>",
    ]
    return "\n".join(lineas)[:MAX_CHARS]


def format_header(jobs: list[Job], errores: dict[str, str], fecha: datetime) -> str:
    """Cabecera con etiqueta HUD de la marca (docs/marca.md)."""
    dia = f"{fecha.day} {_MESES[fecha.month - 1]}"
    estado = "FUENTES ONLINE" if not errores else f"{len(errores)} FUENTE(S) CON ERROR"
    if not jobs:
        hud = f"RADAR // {dia} · SIN NOVEDADES · {estado}"
        cuerpo = "Sin ofertas nuevas hoy."
    else:
        verdes = sum(j.clasificacion == Clasificacion.ENCAJE for j in jobs)
        amarillas = len(jobs) - verdes
        hud = f"RADAR // {dia} · {len(jobs)} NUEVAS · {estado}"
        cuerpo = f"🟢 {verdes} · 🟡 {amarillas}"
    lineas = [f"<code>{hud}</code>", "", cuerpo]
    for fuente, error in errores.items():
        lineas.append(f"⚠ {esc(fuente)} no respondió: {esc(error[:120])}")
    return "\n".join(lineas)


def ordenar(jobs: list[Job]) -> list[Job]:
    """Primero 🟢, después 🟡; dentro de cada grupo, por puntaje (RF-NOT-06)."""
    return sorted(jobs, key=lambda j: (j.clasificacion != Clasificacion.ENCAJE, -j.puntaje))


@dataclass
class Mensaje:
    texto: str
    url: str | None = None


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str, pausa: float = 0.1,
                 session: requests.Session | None = None):
        self.token, self.chat_id, self.pausa = token, chat_id, pausa
        self.session = session or requests.Session()

    def enviar(self, mensaje: Mensaje) -> None:
        payload: dict = {
            "chat_id": self.chat_id,
            "text": mensaje.texto,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if mensaje.url:
            payload["reply_markup"] = {
                "inline_keyboard": [[{"text": "🔗 Ver oferta", "url": mensaje.url}]]
            }
        for intento in range(3):
            resp = self.session.post(API.format(token=self.token, method="sendMessage"),
                                     json=payload, timeout=20)
            if resp.status_code == 429:  # límite de Telegram (RF-NOT-05)
                espera = resp.json().get("parameters", {}).get("retry_after", 2 ** intento)
                time.sleep(float(espera))
                continue
            resp.raise_for_status()
            time.sleep(self.pausa)
            return
        resp.raise_for_status()


class ConsoleNotifier:
    """Modo de prueba: muestra los mensajes en vez de enviarlos (RF-EJE-02)."""

    def __init__(self) -> None:
        self.enviados: list[Mensaje] = []

    def enviar(self, mensaje: Mensaje) -> None:
        self.enviados.append(mensaje)
        print(mensaje.texto)
        if mensaje.url:
            print(f"[🔗 Ver oferta → {mensaje.url}]")
        print("-" * 40)
