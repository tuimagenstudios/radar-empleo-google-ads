"""Get on Board: API pública, sin cuenta ni clave (RF-REC-06).

Documentación: https://www.getonbrd.com/api-doc
Se usa con respeto: pocas consultas por ejecución, pausa entre pedidos y un
User-Agent que identifica al proyecto.
"""

from __future__ import annotations

import html
import re
import time
from datetime import UTC, datetime, timedelta

import requests

from radar.collectors.base import Collector
from radar.models import RawJob

API = "https://www.getonbrd.com/api/v0/search/jobs"
USER_AGENT = "radar-empleo-google-ads/0.1 (+https://github.com/tuimagenstudios/radar-empleo-google-ads)"

# IDs de /api/v0/seniorities. "Expert" se trata como senior.
SENIORITY = {"1": "Sin experiencia", "2": "Junior", "3": "Semi Senior", "4": "Senior",
             "5": "Senior"}
INTERNSHIP_MODALITY = "4"

_TAGS = re.compile(r"<[^>]+>")


def html_a_texto(fragmento: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAGS.sub(" ", fragmento or ""))).strip()


def ubicacion(attrs: dict) -> str:
    """Traduce la modalidad de Get on Board a un texto que entiende el normalizador."""
    paises = [c for c in attrs.get("countries") or [] if c and c.lower() != "remote"]
    lugar = ", ".join(paises)
    zona = attrs.get("remote_zone")
    modalidad = attrs.get("remote_modality")
    if modalidad == "fully_remote":
        # Get on Board: "remoto 100 %" = se puede trabajar desde cualquier lugar.
        return f"Remoto {zona}" if zona else "Remoto 100%, desde cualquier lugar"
    if modalidad in ("remote_local", "temporarily_remote"):
        return f"Remoto, solo residentes en {lugar}" if lugar else "Remoto"
    if modalidad == "hybrid":
        return f"Híbrido, {lugar}" if lugar else "Híbrido"
    if modalidad == "no_remote":
        return f"Presencial, {lugar}" if lugar else "Presencial"
    return lugar


def salario(attrs: dict) -> str:
    minimo, maximo = attrs.get("min_salary"), attrs.get("max_salary")
    if not minimo and not maximo:
        return ""
    if minimo and maximo and minimo != maximo:
        return f"USD {minimo:,}–{maximo:,} / mes".replace(",", ".")
    return f"USD {(minimo or maximo):,} / mes".replace(",", ".")


def a_raw_job(item: dict, fuente: str) -> RawJob:
    a = item["attributes"]
    empresa = (((a.get("company") or {}).get("data") or {}).get("attributes") or {})
    seniority = str(((a.get("seniority") or {}).get("data") or {}).get("id", ""))
    modalidad = str(((a.get("modality") or {}).get("data") or {}).get("id", ""))
    nivel = SENIORITY.get(seniority, "")
    if modalidad == INTERNSHIP_MODALITY:
        nivel = f"{nivel} Pasantía".strip()
    secciones = ("description", "functions", "desirable", "projects", "benefits")
    descripcion = " ".join(html_a_texto(a.get(s)) for s in secciones if a.get(s))
    publicada = ""
    if a.get("published_at"):
        publicada = datetime.fromtimestamp(a["published_at"], UTC).isoformat()
    return RawJob(
        fuente=fuente,
        titulo=html.unescape(a.get("title", "")).strip(),
        url=(item.get("links") or {}).get("public_url")
            or f"https://www.getonbrd.com/jobs/{item['id']}",
        empresa=empresa.get("name", ""),
        ubicacion=ubicacion(a),
        descripcion=descripcion,
        salario=salario(a),
        id_externo=item["id"],
        publicada=publicada,
        nivel=nivel,
    )


class GetOnBoardCollector(Collector):
    def __init__(self, fuente, config, session: requests.Session | None = None,
                 pausa: float = 0.5):
        super().__init__(fuente, config)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.pausa = pausa

    def _buscar(self, consulta: str) -> list[dict]:
        items: list[dict] = []
        for pagina in range(1, int(self.fuente.get("paginas_max", 2)) + 1):
            resp = self.session.get(
                API,
                params={"query": consulta, "per_page": 50, "page": pagina,
                        "expand": '["company"]'},
                timeout=20,
            )
            resp.raise_for_status()
            datos = resp.json()
            items += datos.get("data", [])
            time.sleep(self.pausa)
            if pagina >= (datos.get("meta") or {}).get("total_pages", 1):
                break
        return items

    def fetch(self) -> list[RawJob]:
        limite = datetime.now(UTC) - timedelta(days=int(self.fuente.get("dias_max", 30)))
        vistos: dict[str, RawJob] = {}
        for consulta in self.fuente.get("consultas", ["google ads"]):
            for item in self._buscar(consulta):
                if item["id"] in vistos:
                    continue
                publicada = item["attributes"].get("published_at")
                if publicada and datetime.fromtimestamp(publicada, UTC) < limite:
                    continue
                vistos[item["id"]] = a_raw_job(item, self.nombre)
        return list(vistos.values())
