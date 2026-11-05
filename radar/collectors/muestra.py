"""Fuente de ejemplo: lee ofertas ficticias de un JSON local.

Sirve para probar todo el circuito hasta que la etapa 0 elija las fuentes reales.
"""

from __future__ import annotations

import json

from radar.collectors.base import Collector
from radar.models import RawJob


class MuestraCollector(Collector):
    def fetch(self) -> list[RawJob]:
        ruta = self.config.ruta(self.fuente["ruta"])
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return [RawJob(fuente=self.nombre, **oferta) for oferta in datos["ofertas"]]
