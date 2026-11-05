"""Diccionario de países, ciudades, gentilicios y regiones (RF-CFG-04).

Se omiten a propósito los alias ambiguos: "Córdoba" (AR/ES), "Valencia" (ES/VE),
"Santa Cruz" (BO/AR), "San José" (CR/EE. UU.), "Cuenca", "Mérida", "Trujillo",
"San Juan", "Florida", "usa" (verbo) y el gentilicio "español", que casi siempre
se refiere al idioma.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from radar.text import normalize


@dataclass(frozen=True)
class Country:
    code: str
    name: str
    flag: str
    aliases: tuple[str, ...]


COUNTRIES: tuple[Country, ...] = (
    Country("AR", "Argentina", "🇦🇷", ("argentina", "argentino", "buenos aires",
                                         "caba", "rosario", "mendoza", "la plata",
                                         "mar del plata")),
    Country("BO", "Bolivia", "🇧🇴", ("bolivia", "boliviano", "la paz", "cochabamba")),
    Country("CL", "Chile", "🇨🇱", ("chile", "chileno", "santiago de chile", "santiago",
                                     "valparaiso", "vina del mar")),
    Country("CO", "Colombia", "🇨🇴", ("colombia", "colombiano", "bogota", "medellin", "cali",
                                        "barranquilla", "bucaramanga")),
    Country("CR", "Costa Rica", "🇨🇷", ("costa rica", "costarricense")),
    Country("CU", "Cuba", "🇨🇺", ("cuba", "cubano", "la habana")),
    Country("DO", "República Dominicana", "🇩🇴", ("republica dominicana", "dominicano",
                                                    "santo domingo")),
    Country("EC", "Ecuador", "🇪🇨", ("ecuador", "ecuatoriano", "quito", "guayaquil")),
    Country("ES", "España", "🇪🇸", ("espana", "madrid", "barcelona", "sevilla", "bilbao",
                                      "malaga", "zaragoza", "alicante", "palma de mallorca")),
    Country("GQ", "Guinea Ecuatorial", "🇬🇶", ("guinea ecuatorial", "malabo")),
    Country("GT", "Guatemala", "🇬🇹", ("guatemala", "guatemalteco")),
    Country("HN", "Honduras", "🇭🇳", ("honduras", "hondureno", "tegucigalpa", "san pedro sula")),
    Country("MX", "México", "🇲🇽", ("mexico", "mexicano", "cdmx", "ciudad de mexico",
                                      "guadalajara", "monterrey", "puebla", "queretaro",
                                      "tijuana")),
    Country("NI", "Nicaragua", "🇳🇮", ("nicaragua", "nicaraguense", "managua")),
    Country("PA", "Panamá", "🇵🇦", ("panama", "panameno")),
    Country("PE", "Perú", "🇵🇪", ("peru", "peruano", "lima", "arequipa")),
    Country("PY", "Paraguay", "🇵🇾", ("paraguay", "paraguayo", "asuncion")),
    Country("SV", "El Salvador", "🇸🇻", ("el salvador", "salvadoreno", "san salvador")),
    Country("UY", "Uruguay", "🇺🇾", ("uruguay", "uruguayo", "montevideo")),
    Country("VE", "Venezuela", "🇻🇪", ("venezuela", "venezolano", "caracas", "maracaibo")),
    # Fuera del mercado objetivo: se detectan para poder descartarlos (RF-NOR-07).
    Country("US", "Estados Unidos", "🇺🇸", ("estados unidos", "eeuu", "ee uu",
                                              "united states", "miami", "new york",
                                              "nueva york", "texas", "california")),
    Country("PR", "Puerto Rico", "🇵🇷", ("puerto rico", "puertorriqueno")),
)

BY_CODE: dict[str, Country] = {c.code: c for c in COUNTRIES}

LATAM: frozenset[str] = frozenset(
    {"AR", "BO", "CL", "CO", "CR", "CU", "DO", "EC", "GT", "HN", "MX", "NI", "PA", "PE",
     "PY", "SV", "UY", "VE"}
)
CONO_SUR: frozenset[str] = frozenset({"AR", "CL", "UY", "PY"})

REGIONS: dict[str, frozenset[str]] = {
    "latam": LATAM,
    "latinoamerica": LATAM,
    "america latina": LATAM,
    "hispanoamerica": LATAM,
    "sudamerica": frozenset({"AR", "BO", "CL", "CO", "EC", "PE", "PY", "UY", "VE"}),
    "cono sur": CONO_SUR,
}

WORLDWIDE_TERMS: tuple[str, ...] = (
    "cualquier pais", "cualquier parte del mundo", "desde cualquier lugar",
    "desde cualquier parte", "anywhere", "worldwide", "remoto global", "100 remoto global",
)


def _alias_regex() -> re.Pattern[str]:
    pairs = sorted(
        ((normalize(a), c.code) for c in COUNTRIES for a in c.aliases),
        key=lambda p: -len(p[0]),
    )
    _ALIAS_TO_CODE.update(dict(pairs))
    alternation = "|".join(re.escape(a) for a, _ in pairs)
    return re.compile(r"(?<![a-z0-9])(" + alternation + r")(?![a-z0-9])")


_ALIAS_TO_CODE: dict[str, str] = {}
_ALIAS_RE = _alias_regex()


def countries_in(normalized_text: str) -> list[str]:
    """Códigos de país mencionados, en orden de aparición y sin repetir."""
    codes: list[str] = []
    for match in _ALIAS_RE.finditer(normalized_text):
        code = _ALIAS_TO_CODE[match.group(1)]
        if code not in codes:
            codes.append(code)
    return codes


def regions_in(normalized_text: str) -> set[str]:
    """Países incluidos por las regiones mencionadas ("LATAM", "Cono Sur"...)."""
    result: set[str] = set()
    for name, members in REGIONS.items():
        if re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", normalized_text):
            result |= members
    return result
