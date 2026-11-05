"""Huella de deduplicación entre portales (RF-DED-01)."""

from __future__ import annotations

import hashlib
import re

from radar.models import RawJob
from radar.text import normalize

_PARENTESIS = re.compile(r"\([^)]*\)|\[[^\]]*\]")
_SINONIMOS = {"jr": "junior", "sr": "senior", "ssr": "semi senior"}
_GENERICAS = {"remoto", "remota", "hibrido", "presencial", "urgente", "a", "de", "en", "-", "y"}
_SUFIJOS_EMPRESA = {"sa", "srl", "sas", "sl", "sau", "inc", "llc", "ltda", "spa"}


def _palabras(texto: str, descartar: set[str]) -> list[str]:
    palabras = (_SINONIMOS.get(p, p) for p in normalize(_PARENTESIS.sub(" ", texto)).split())
    return [p for p in palabras if p not in descartar]


def huella(raw: RawJob) -> str:
    """La misma oferta publicada en dos portales genera la misma huella."""
    titulo = " ".join(_palabras(raw.titulo, _GENERICAS))
    empresa = " ".join(_palabras(raw.empresa, _SUFIJOS_EMPRESA))
    return hashlib.sha1(f"{titulo}|{empresa}".encode()).hexdigest()[:16]
