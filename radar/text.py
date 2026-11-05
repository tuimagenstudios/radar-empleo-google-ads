"""Normalización de texto y búsqueda de términos (RF-CLA-01)."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

_ACRONYM_DOTS = re.compile(r"\b(?:[A-Za-z]\.){2,}")
_DASHES = re.compile(r"[‐-―]")
_NOT_ALLOWED = re.compile(r"[^a-z0-9+\-]+")
_SPACES = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    """Minúsculas, sin acentos, sin signos. "S.E.M." -> "sem", "años" -> "anos"."""
    if not text:
        return ""
    text = _ACRONYM_DOTS.sub(lambda m: m.group(0).replace(".", ""), text)
    text = _DASHES.sub("-", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = _NOT_ALLOWED.sub(" ", text.lower())
    return _SPACES.sub(" ", text).strip()


def term_pattern(term: str) -> re.Pattern[str]:
    """Patrón que busca el término como palabra completa sobre texto normalizado."""
    return re.compile(r"(?<![a-z0-9])" + re.escape(normalize(term)) + r"(?![a-z0-9])")


def find_terms(normalized_text: str, terms: Iterable[str]) -> list[str]:
    """Devuelve los términos presentes, en el orden de la lista y sin repetir."""
    found: list[str] = []
    for term in terms:
        if term not in found and term_pattern(term).search(normalized_text):
            found.append(term)
    # "trafficker" sobra si ya está "trafficker digital".
    return [t for t in found if not any(t != o and term_pattern(t).search(o) for o in found)]


_ES_WORDS = {"de", "la", "el", "en", "y", "para", "con", "los", "las", "una", "que", "por", "del"}
_EN_WORDS = {"the", "and", "for", "with", "you", "our", "to", "of", "we", "are", "will", "your"}


def detect_language(normalized_text: str) -> str:
    """Detección simple de idioma: "es", "en" o "desconocido" (RF-NOR-08)."""
    words = normalized_text.split()
    es = sum(w in _ES_WORDS for w in words)
    en = sum(w in _EN_WORDS for w in words)
    # Hacen falta varias palabras en inglés: "Head of Marketing" no vuelve inglesa una oferta.
    if en >= 3 and en > es:
        return "en"
    return "es" if es else "desconocido"
