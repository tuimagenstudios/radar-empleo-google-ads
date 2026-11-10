"""Recolectores de ofertas. Todos implementan `fetch() -> list[RawJob]` (RF-REC-01)."""

from __future__ import annotations

import logging
import os

from radar.collectors.adzuna import AdzunaCollector
from radar.collectors.base import Collector
from radar.collectors.getonbrd import GetOnBoardCollector
from radar.collectors.gmail import GmailCollector
from radar.collectors.himalayas import HimalayasCollector
from radar.collectors.jobicy import JobicyCollector
from radar.collectors.muestra import MuestraCollector
from radar.collectors.remotive import RemotiveCollector
from radar.config import Config

log = logging.getLogger("radar")

TIPOS: dict[str, type[Collector]] = {
    "muestra": MuestraCollector,
    "getonbrd": GetOnBoardCollector,
    "adzuna": AdzunaCollector,
    "gmail": GmailCollector,
    "himalayas": HimalayasCollector,
    "jobicy": JobicyCollector,
    "remotive": RemotiveCollector,
}


def build_collectors(config: Config) -> list[Collector]:
    collectors: list[Collector] = []
    for fuente in config.fuentes:
        if not fuente.get("activa", True):
            continue
        tipo = fuente.get("tipo")
        if tipo not in TIPOS:
            raise ValueError(f"Tipo de fuente desconocido: {tipo!r}")
        faltan = [v for v in TIPOS[tipo].requiere_env if not os.getenv(v)]
        if faltan:
            log.warning("Fuente %s omitida: faltan %s", fuente.get("nombre", tipo),
                        ", ".join(faltan))
            continue
        collectors.append(TIPOS[tipo](fuente, config))
    return collectors


__all__ = ["Collector", "build_collectors"]
