"""Interfaz común de los recolectores (RF-REC-01)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from radar.config import Config
from radar.models import RawJob


class Collector(ABC):
    # Variables de entorno que necesita la fuente. Si falta alguna, se omite sin error.
    requiere_env: tuple[str, ...] = ()

    def __init__(self, fuente: dict, config: Config):
        self.fuente = fuente
        self.config = config
        self.nombre: str = fuente.get("nombre") or fuente["tipo"]

    @abstractmethod
    def fetch(self) -> list[RawJob]:
        """Devuelve las ofertas de la fuente. Lanza una excepción si la fuente falla."""
