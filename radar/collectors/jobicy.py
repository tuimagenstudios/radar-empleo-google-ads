"""Jobicy: API pública de empleos remotos, sin cuenta ni clave (RF-REC-06).

Documentación: https://jobicy.com/jobs-rss-feed
Jobicy pide no consultar más que unas pocas veces por día: el radar hace una
consulta por combinación de región y etiqueta, dos veces al día.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import requests

from radar.collectors.base import Collector
from radar.collectors.getonbrd import USER_AGENT, html_a_texto
from radar.models import RawJob

API = "https://jobicy.com/api/v2/remote-jobs"

# "Any" y "Midweight" no dicen nada útil para el clasificador.
_NIVEL_IGNORADO = {"any", "midweight", ""}


def salario(j: dict) -> str:
    minimo, maximo = j.get("salaryMin"), j.get("salaryMax")
    if not minimo and not maximo:
        return ""
    periodo = {"hourly": "hora", "monthly": "mes", "yearly": "año"}.get(
        str(j.get("salaryPeriod") or "").lower(), "")
    moneda = j.get("salaryCurrency") or "USD"
    monto = (f"{int(minimo):,}–{int(maximo):,}" if minimo and maximo and minimo != maximo
             else f"{int(minimo or maximo):,}").replace(",", ".")
    return f"{moneda} {monto} / {periodo}" if periodo else f"{moneda} {monto}"


def a_raw_job(j: dict, fuente: str) -> RawJob:
    nivel = str(j.get("jobLevel") or "").strip()
    geo = " ".join(str(j.get("jobGeo") or "").split())
    return RawJob(
        fuente=fuente,
        titulo=html_a_texto(j.get("jobTitle")),
        url=j.get("url", ""),
        empresa=html_a_texto(j.get("companyName")),
        ubicacion=f"Remoto {geo}".strip(),
        descripcion=html_a_texto(j.get("jobDescription") or j.get("jobExcerpt")),
        salario=salario(j),
        id_externo=str(j.get("id", "")),
        publicada=str(j.get("pubDate") or ""),
        nivel="" if nivel.lower() in _NIVEL_IGNORADO else nivel,
    )


def _es_vieja(publicada: str, limite: datetime) -> bool:
    try:
        fecha = datetime.fromisoformat(publicada)
    except ValueError:
        return False
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=UTC)
    return fecha < limite


class JobicyCollector(Collector):
    def __init__(self, fuente, config, session: requests.Session | None = None,
                 pausa: float = 1.5):
        super().__init__(fuente, config)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.pausa = pausa

    def fetch(self) -> list[RawJob]:
        limite = datetime.now(UTC) - timedelta(days=int(self.fuente.get("dias_max", 30)))
        vistos: dict[str, RawJob] = {}
        for region in self.fuente.get("regiones", ["latam"]):
            for consulta in self.fuente.get("consultas", ["google ads"]):
                resp = self.session.get(
                    API, params={"count": 50, "geo": region, "tag": consulta}, timeout=20)
                resp.raise_for_status()
                for j in resp.json().get("jobs", []):
                    job = a_raw_job(j, self.nombre)
                    if job.id_externo in vistos or _es_vieja(job.publicada, limite):
                        continue
                    vistos[job.id_externo] = job
                time.sleep(self.pausa)
        return list(vistos.values())
