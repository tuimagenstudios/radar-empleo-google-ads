"""Himalayas: API pública de búsqueda, sin cuenta ni clave (RF-REC-06).

Documentación: https://himalayas.app/api
La búsqueda admite filtrar por país del candidato, así que solo se piden las
ofertas remotas que se pueden tomar desde el país base. Se usa con respeto:
pocas consultas por ejecución y pausa entre pedidos.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime, timedelta

import requests

from radar.collectors.base import Collector
from radar.collectors.getonbrd import USER_AGENT, html_a_texto
from radar.locations import BY_CODE, LATAM
from radar.models import RawJob

API = "https://himalayas.app/jobs/api/search"
log = logging.getLogger("radar")


class LimiteDeConsultas(Exception):
    """Himalayas respondió 429: demasiadas consultas seguidas."""

# Himalayas da los países en inglés. Solo hacen falta los que difieren del español.
_EN_A_CODIGO = {"mexico": "MX", "peru": "PE", "panama": "PA", "dominican republic": "DO",
                "spain": "ES", "united states": "US"}
_NIVEL = {"entry-level": "Junior", "senior": "Senior", "manager": "Senior",
          "director": "Director", "executive": "Director", "lead": "Lead"}
# Con esta cantidad de países de LATAM habilitados se la trata como "remoto LATAM".
_MINIMO_LATAM = 10


def codigo_pais(nombre: str) -> str | None:
    clave = nombre.strip().lower()
    if clave in _EN_A_CODIGO:
        return _EN_A_CODIGO[clave]
    return next((c.code for c in BY_CODE.values() if c.name.lower() == clave), None)


def paises(restricciones: list[str]) -> tuple[str, ...]:
    """Códigos de los países habilitados; ("*",) si no hay restricción.

    Los países que el radar no conoce (Brasil, Egipto...) se omiten.
    """
    if not restricciones:
        return ("*",)
    codigos = {c for c in map(codigo_pais, restricciones) if c}
    if len(codigos & LATAM) >= _MINIMO_LATAM:
        codigos |= LATAM
    return tuple(sorted(codigos))


def ubicacion(restricciones: list[str]) -> str:
    if not restricciones:
        return "Remoto 100%, desde cualquier lugar"
    if len(set(paises(restricciones)) & LATAM) >= _MINIMO_LATAM:
        return "Remoto LATAM"
    return "Remoto · " + ", ".join(restricciones)


def nivel(seniority: list[str]) -> str:
    """El nivel más alto que pide la oferta; "Mid-level" queda sin especificar."""
    niveles = [_NIVEL[s.lower()] for s in seniority or [] if s.lower() in _NIVEL]
    altos = [n for n in niveles if n != "Junior"]
    return (altos or niveles or [""])[0]


def salario(j: dict) -> str:
    try:  # la API a veces los entrega como texto
        minimo, maximo = (int(float(j.get(k) or 0)) for k in ("minSalary", "maxSalary"))
    except (TypeError, ValueError):
        return ""
    if not minimo and not maximo:
        return ""
    periodo = {"hourly": "hora", "monthly": "mes", "annual": "año", "yearly": "año"}.get(
        str(j.get("salaryPeriod") or "").lower(), "")
    moneda = j.get("currency") or "USD"
    monto = (f"{minimo:,}–{maximo:,}" if minimo and maximo and minimo != maximo
             else f"{(minimo or maximo):,}").replace(",", ".")
    return f"{moneda} {monto} / {periodo}" if periodo else f"{moneda} {monto}"


def a_raw_job(j: dict, fuente: str) -> RawJob:
    restricciones = j.get("locationRestrictions") or []
    publicada = ""
    if j.get("pubDate"):
        publicada = datetime.fromtimestamp(int(j["pubDate"]), UTC).isoformat()
    return RawJob(
        fuente=fuente,
        titulo=(j.get("title") or "").strip(),
        url=j.get("guid") or j.get("applicationLink") or "",
        empresa=(j.get("companyName") or "").strip(),
        ubicacion=ubicacion(restricciones),
        descripcion=html_a_texto(j.get("description") or j.get("excerpt")),
        salario=salario(j),
        id_externo=j.get("guid") or "",
        publicada=publicada,
        nivel=nivel(j.get("seniority") or []),
        paises=paises(restricciones),
    )


class HimalayasCollector(Collector):
    def __init__(self, fuente, config, session: requests.Session | None = None,
                 pausa: float = 3.0):
        super().__init__(fuente, config)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.pausa = pausa

    def _buscar(self, consulta: str) -> list[dict]:
        items: list[dict] = []
        for pagina in range(1, int(self.fuente.get("paginas_max", 2)) + 1):
            resp = self.session.get(
                API,
                params={"q": consulta, "country": self.config.pais_base, "page": pagina},
                timeout=20,
            )
            if resp.status_code == 429:
                raise LimiteDeConsultas
            resp.raise_for_status()
            datos = resp.json()
            lote = datos.get("jobs", [])
            items += lote
            time.sleep(self.pausa)
            if not lote or len(items) >= int(datos.get("totalCount") or 0):
                break
        return items

    def fetch(self) -> list[RawJob]:
        limite = datetime.now(UTC) - timedelta(days=int(self.fuente.get("dias_max", 30)))
        vistos: dict[str, RawJob] = {}
        for n, consulta in enumerate(self.fuente.get("consultas", ["google ads"])):
            try:
                encontrados = self._buscar(consulta)
            except LimiteDeConsultas:
                if n == 0:
                    raise RuntimeError("Himalayas: límite de consultas alcanzado") from None
                # Se conserva lo ya leído; el resto entra en la próxima ejecución.
                log.warning("Himalayas cortó en %r por límite de consultas", consulta)
                break
            for j in encontrados:
                clave = j.get("guid") or j.get("applicationLink")
                if not clave or clave in vistos:
                    continue
                publicada = j.get("pubDate")
                if publicada and datetime.fromtimestamp(int(publicada), UTC) < limite:
                    continue
                vistos[clave] = a_raw_job(j, self.nombre)
        return list(vistos.values())
