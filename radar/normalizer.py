"""Normalización: país, modalidad, países habilitados, experiencia e idioma (RF-NOR-*)."""

from __future__ import annotations

import re

from radar.config import Config
from radar.locations import WORLDWIDE_TERMS, countries_in, regions_in
from radar.models import Job, RawJob
from radar.text import detect_language, find_terms, normalize

_MODALIDADES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("hibrido", ("hibrido", "hibrida", "hybrid", "semipresencial")),
    ("remoto", ("remoto", "remota", "home office", "teletrabajo", "trabajo a distancia",
                "remote", "100 remoto")),
    ("presencial", ("presencial", "on site", "onsite", "en oficina")),
)

# Frases que introducen una restricción geográfica: "solo residentes en España".
_RESTRICCION = re.compile(
    r"(?:residentes?|residir|residencia|radicad[oa]s?|ubicad[oa]s?|con base|vivir|vivas|"
    r"solo para|exclusivo para|desde)\s+(?:en\s+)?(?:la\s+|el\s+)?([a-z0-9 ]{2,40})"
)
_REGION_ABIERTA = re.compile(
    r"(?:remoto|remota|desde|residentes? en|cualquier pais de|para)\s+(?:[a-z]+\s+){0,2}?"
    r"(latam|latinoamerica|america latina|hispanoamerica|sudamerica|cono sur)"
)

_RANGO = re.compile(r"(\d{1,2})\s*(?:a|-|y)\s*(\d{1,2})\s*anos?\b")
_MINIMO = re.compile(r"(?:\+\s*|mas de\s+|minimo\s+(?:de\s+)?|al menos\s+)(\d{1,2})\s*anos?\b")
_MINIMO_SUFIJO = re.compile(r"(\d{1,2})\s*\+?\s*anos? de experiencia")
_SIN_EXPERIENCIA = re.compile(r"sin experiencia|no se requiere experiencia|primer empleo")


def detect_modalidad(text: str) -> str:
    for modalidad, terms in _MODALIDADES:
        if find_terms(text, terms):
            return modalidad
    return "sin_especificar"


def detect_experiencia(text: str) -> tuple[int | None, int | None]:
    """(mínimo, máximo) de años de experiencia, o None si no se menciona (RF-NOR-05)."""
    hits: list[tuple[int, int, int | None]] = []  # (posición, mínimo, máximo)
    for m in _RANGO.finditer(text):
        hits.append((m.start(), int(m.group(1)), int(m.group(2))))
    for regex in (_MINIMO, _MINIMO_SUFIJO):
        for m in regex.finditer(text):
            hits.append((m.start(), int(m.group(1)), None))
    # Más de 15 "años" casi siempre es la edad ("de 18 a 25 años"), no la experiencia.
    hits = [h for h in hits if h[1] <= 15]
    if hits:
        _, minimo, maximo = min(hits, key=lambda h: h[0])
        return minimo, maximo
    if _SIN_EXPERIENCIA.search(text):
        return 0, 0
    return None, None


def detect_paises_habilitados(texto: str, ubicacion: str) -> set[str]:
    """Países desde los que se puede tomar la oferta (RF-NOR-04).

    Devuelve {"*"} si está abierta a cualquier país y un conjunto vacío si la
    oferta no lo dice. Nunca lo supone. Una restricción explícita ("solo
    residentes en Chile") tiene prioridad sobre "remoto desde cualquier lugar".
    """
    habilitados: set[str] = set(regions_in(ubicacion))
    for m in _REGION_ABIERTA.finditer(texto):
        habilitados |= regions_in(m.group(1))
    for m in _RESTRICCION.finditer(texto):
        paises = countries_in(m.group(1))
        if paises:
            habilitados.add(paises[0])
    if not habilitados and find_terms(texto, WORLDWIDE_TERMS):
        return {"*"}
    return habilitados


def normalize_job(raw: RawJob, config: Config) -> Job:
    ubicacion = normalize(raw.ubicacion)
    titulo = normalize(raw.titulo)
    descripcion = normalize(raw.descripcion)
    texto = f"{titulo} {ubicacion} {descripcion}"

    paises_ubicacion = countries_in(ubicacion)
    paises_texto = countries_in(f"{titulo} {descripcion}")
    pais = (paises_ubicacion or paises_texto or [None])[0]

    job = Job(
        raw=raw,
        pais=pais,
        modalidad=detect_modalidad(texto),
        # Si la fuente informa los países, valen más que lo deducido del texto.
        paises_habilitados=set(raw.paises) or detect_paises_habilitados(texto, ubicacion),
        idioma=detect_language(f"{titulo} {descripcion}"),
    )
    job.exp_min, job.exp_max = detect_experiencia(texto)

    abierta = "*" in job.paises_habilitados or bool(job.paises_habilitados & config.mercados)
    job.fuera_de_mercado = pais is not None and pais not in config.mercados and not abierta
    return job
