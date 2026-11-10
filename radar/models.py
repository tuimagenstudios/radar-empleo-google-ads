"""Modelos de datos del radar."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Clasificacion(StrEnum):
    ENCAJE = "encaje"      # 🟢
    REVISAR = "revisar"    # 🟡
    DESCARTE = "descarte"  # 🔴

    @property
    def emoji(self) -> str:
        return {"encaje": "🟢", "revisar": "🟡", "descarte": "🔴"}[self.value]


@dataclass
class RawJob:
    """Oferta tal como llega de una fuente (RF-REC-01)."""

    fuente: str
    titulo: str
    url: str
    empresa: str = ""
    ubicacion: str = ""
    descripcion: str = ""
    salario: str = ""
    id_externo: str = ""
    publicada: str = ""
    # Nivel estructurado que informa la fuente ("Junior", "Senior"...), si lo tiene.
    nivel: str = ""
    # Países habilitados que informa la fuente, como códigos ("*" = cualquiera).
    # Vacío = la fuente no lo informa y el normalizador lo deduce del texto.
    paises: tuple[str, ...] = ()


@dataclass
class Job:
    """Oferta normalizada y clasificada (RF-NOR-01)."""

    raw: RawJob
    pais: str | None = None
    modalidad: str = "sin_especificar"  # remoto | hibrido | presencial | sin_especificar
    # Vacío = sin especificar · {"*"} = cualquier país · si no, códigos de país.
    paises_habilitados: set[str] = field(default_factory=set)
    exp_min: int | None = None
    exp_max: int | None = None
    idioma: str = "desconocido"
    fuera_de_mercado: bool = False
    huella: str = ""
    clasificacion: Clasificacion | None = None
    puntaje: int = 0
    motivo: str = ""
    terminos: list[str] = field(default_factory=list)
