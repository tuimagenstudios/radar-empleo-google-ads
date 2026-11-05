from __future__ import annotations

from pathlib import Path

import pytest

from radar.classifier import classify
from radar.config import Config, load_config
from radar.models import Job, RawJob
from radar.normalizer import normalize_job

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def config() -> Config:
    """La configuración real, pero solo con la fuente de muestra (sin red)."""
    cfg = load_config(ROOT / "config.yaml")
    cfg.fuentes = [{"tipo": "muestra", "nombre": "muestra",
                    "ruta": "data/muestra_ofertas.json", "activa": True}]
    # Las pruebas fijan el mercado hispanohablante completo para no depender de la
    # configuración del momento; test_mercado_argentina.py prueba el modo "solo AR".
    cfg.mercados = {"AR", "BO", "CL", "CO", "CR", "CU", "DO", "EC", "ES", "GQ", "GT", "HN",
                    "MX", "NI", "PA", "PE", "PY", "SV", "UY", "VE"}
    return cfg


@pytest.fixture
def evaluar(config):
    """Normaliza y clasifica una oferta armada en el test."""

    def _evaluar(titulo: str, descripcion: str = "", ubicacion: str = "",
                 empresa: str = "Empresa") -> Job:
        raw = RawJob(fuente="test", titulo=titulo, url="https://example.com/x",
                     empresa=empresa, ubicacion=ubicacion, descripcion=descripcion)
        return classify(normalize_job(raw, config), config)

    return _evaluar
