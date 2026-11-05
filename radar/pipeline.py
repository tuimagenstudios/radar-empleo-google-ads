"""Ciclo completo: recolectar → normalizar → deduplicar → clasificar → guardar → notificar."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from radar.classifier import classify
from radar.collectors import Collector
from radar.config import Config
from radar.dedup import huella
from radar.models import Clasificacion, Job
from radar.normalizer import normalize_job
from radar.notifier import Mensaje, format_header, format_job, ordenar
from radar.storage import Storage, ahora

log = logging.getLogger("radar")


class Notifier(Protocol):
    def enviar(self, mensaje: Mensaje) -> None: ...


@dataclass
class Resultado:
    leidas: int = 0
    nuevas: list[Job] = field(default_factory=list)
    duplicadas: int = 0
    errores: dict[str, str] = field(default_factory=dict)

    @property
    def a_notificar(self) -> list[Job]:
        return ordenar([j for j in self.nuevas if j.clasificacion != Clasificacion.DESCARTE])


def run(config: Config, collectors: list[Collector], storage: Storage, notifier: Notifier,
        ahora_local: datetime | None = None, resumen: bool = True) -> Resultado:
    """`resumen=False` es la ejecución silenciosa: solo escribe si hay ofertas o errores.

    Así llega un único resumen por día aunque el radar corra dos veces (RF-EJE-04).
    """
    resultado = Resultado()
    vistas: set[str] = set()

    for collector in collectors:
        inicio = ahora()
        try:
            crudas = collector.fetch()
        except Exception as exc:  # cada fuente aislada (RF-ERR-01)
            log.exception("Falló la fuente %s", collector.nombre)
            resultado.errores[collector.nombre] = f"{type(exc).__name__}: {exc}"
            storage.registrar_ejecucion(collector.nombre, inicio, "error", error=str(exc))
            continue

        nuevas = duplicadas = 0
        for raw in crudas:
            try:
                job = classify(normalize_job(raw, config), config)
                job.huella = huella(raw)
                if job.huella in vistas or storage.existe(job.huella):  # RF-DED-03
                    duplicadas += 1
                    continue
                vistas.add(job.huella)
                storage.guardar(job)
                resultado.nuevas.append(job)
                nuevas += 1
            except Exception:  # una oferta rota no frena al resto (RF-ERR-06)
                log.exception("No se pudo procesar la oferta %r", raw.url)

        resultado.leidas += len(crudas)
        resultado.duplicadas += duplicadas
        storage.registrar_ejecucion(collector.nombre, inicio, "ok", len(crudas), nuevas,
                                    duplicadas)

    fecha = ahora_local or datetime.now(ZoneInfo(config.zona_horaria))
    jobs = resultado.a_notificar
    if not resumen and not jobs and not resultado.errores:
        return resultado
    notifier.enviar(Mensaje(format_header(jobs, resultado.errores, fecha,
                                          revisadas=len(resultado.nuevas))))
    for job in jobs:
        notifier.enviar(Mensaje(format_job(job), url=job.raw.url))
        storage.marcar_notificada(job.huella)
    return resultado
