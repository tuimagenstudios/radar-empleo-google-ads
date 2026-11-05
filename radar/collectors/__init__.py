"""Recolectores de ofertas. Todos implementan `fetch() -> list[RawJob]` (RF-REC-01)."""

from __future__ import annotations

from radar.collectors.base import Collector
from radar.collectors.muestra import MuestraCollector
from radar.config import Config

TIPOS: dict[str, type[Collector]] = {
    "muestra": MuestraCollector,
}


def build_collectors(config: Config) -> list[Collector]:
    collectors: list[Collector] = []
    for fuente in config.fuentes:
        if not fuente.get("activa", True):
            continue
        tipo = fuente.get("tipo")
        if tipo not in TIPOS:
            raise ValueError(f"Tipo de fuente desconocido: {tipo!r}")
        collectors.append(TIPOS[tipo](fuente, config))
    return collectors


__all__ = ["Collector", "build_collectors"]
