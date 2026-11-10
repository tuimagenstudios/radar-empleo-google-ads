"""Remotive: API pública de empleos remotos, sin cuenta ni clave (RF-REC-06).

Documentación: https://remotive.com/remote-jobs/api
Remotive pide como máximo unas 4 consultas por día y que el aviso enlace a su
página: el radar hace una consulta por término y guarda el enlace original.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

import requests

from radar.collectors.base import Collector
from radar.collectors.getonbrd import USER_AGENT, html_a_texto
from radar.collectors.jobicy import _es_vieja
from radar.models import RawJob

API = "https://remotive.com/api/remote-jobs"


def a_raw_job(j: dict, fuente: str) -> RawJob:
    lugar = " ".join(str(j.get("candidate_required_location") or "").split())
    return RawJob(
        fuente=fuente,
        titulo=html_a_texto(j.get("title")),
        url=j.get("url", ""),
        empresa=html_a_texto(j.get("company_name")),
        ubicacion=f"Remoto {lugar}".strip(),
        descripcion=html_a_texto(j.get("description")),
        salario=html_a_texto(j.get("salary")),
        id_externo=str(j.get("id", "")),
        publicada=str(j.get("publication_date") or ""),
    )


class RemotiveCollector(Collector):
    def __init__(self, fuente, config, session: requests.Session | None = None,
                 pausa: float = 2.0):
        super().__init__(fuente, config)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.pausa = pausa

    def fetch(self) -> list[RawJob]:
        limite = datetime.now(UTC) - timedelta(days=int(self.fuente.get("dias_max", 30)))
        vistos: dict[str, RawJob] = {}
        for consulta in self.fuente.get("consultas", ["google ads"]):
            resp = self.session.get(API, params={"search": consulta, "limit": 50}, timeout=20)
            resp.raise_for_status()
            for j in resp.json().get("jobs", []):
                job = a_raw_job(j, self.nombre)
                if job.id_externo in vistos or _es_vieja(job.publicada, limite):
                    continue
                vistos[job.id_externo] = job
            time.sleep(self.pausa)
        return list(vistos.values())
