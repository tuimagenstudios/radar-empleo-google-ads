"""Adzuna: API oficial con registro gratuito (developer.adzuna.com).

Cubre España (`es`) y México (`mx`) entre los mercados objetivo. Necesita
ADZUNA_APP_ID y ADZUNA_APP_KEY en el entorno (.env o GitHub Secrets).
"""

from __future__ import annotations

import os
import re
import time

import requests

from radar.collectors.base import Collector
from radar.collectors.getonbrd import USER_AGENT, html_a_texto
from radar.models import RawJob

API = "https://api.adzuna.com/v1/api/jobs/{pais}/search/{pagina}"
NOMBRE_PAIS = {"es": "España", "mx": "México"}
ENV = ("ADZUNA_APP_ID", "ADZUNA_APP_KEY")


def salario(r: dict, moneda: str) -> str:
    if str(r.get("salary_is_predicted", "0")) == "1":
        return ""  # Adzuna lo estima; no lo mostramos como si fuera real
    minimo, maximo = r.get("salary_min"), r.get("salary_max")
    if not minimo and not maximo:
        return ""
    if minimo and maximo and round(minimo) != round(maximo):
        return f"{moneda} {round(minimo):,}–{round(maximo):,} / año".replace(",", ".")
    return f"{moneda} {round(minimo or maximo):,} / año".replace(",", ".")


def a_raw_job(r: dict, pais: str, fuente: str) -> RawJob:
    lugar = ((r.get("location") or {}).get("display_name") or "").strip()
    nombre_pais = NOMBRE_PAIS.get(pais, pais.upper())
    if nombre_pais.lower() not in lugar.lower():
        lugar = f"{lugar}, {nombre_pais}" if lugar else nombre_pais
    return RawJob(
        fuente=fuente,
        titulo=html_a_texto(r.get("title")),
        url=r.get("redirect_url", ""),
        empresa=((r.get("company") or {}).get("display_name") or "").strip(),
        ubicacion=lugar,
        descripcion=html_a_texto(r.get("description")),
        salario=salario(r, "EUR" if pais == "es" else "MXN"),
        id_externo=f"{pais}-{r.get('id', '')}",
        publicada=r.get("created", ""),
    )


class AdzunaCollector(Collector):
    requiere_env = ENV

    def __init__(self, fuente, config, session: requests.Session | None = None,
                 pausa: float = 1.0):
        super().__init__(fuente, config)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.pausa = pausa

    def fetch(self) -> list[RawJob]:
        app_id, app_key = (os.environ[k] for k in ENV)
        vistos: dict[str, RawJob] = {}
        for pais in self.fuente.get("paises", ["es", "mx"]):
            for consulta in self.fuente.get("consultas", ["google ads"]):
                try:
                    resp = self.session.get(
                        API.format(pais=pais, pagina=1),
                        params={"app_id": app_id, "app_key": app_key, "what": consulta,
                                "max_days_old": int(self.fuente.get("dias_max", 30)),
                                "results_per_page": 50, "sort_by": "date",
                                "content-type": "application/json"},
                        timeout=20,
                    )
                except requests.RequestException as exc:
                    # Los errores de red incluyen la URL, que lleva las claves.
                    raise RuntimeError(redactar(str(exc))) from None
                if resp.status_code >= 400:
                    # Nunca mostrar la URL completa: lleva las claves.
                    raise RuntimeError(f"Adzuna {pais} respondió {resp.status_code}")
                for r in resp.json().get("results", []):
                    job = a_raw_job(r, pais, self.nombre)
                    vistos.setdefault(job.id_externo, job)
                time.sleep(self.pausa)
        return list(vistos.values())


def redactar(texto: str) -> str:
    """Oculta app_id/app_key si aparecieran en un mensaje de error."""
    return re.sub(r"(app_(?:id|key)=)[^&\s]+", r"\1***", texto)
