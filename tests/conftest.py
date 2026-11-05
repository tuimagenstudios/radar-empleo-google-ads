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
    return load_config(ROOT / "config.yaml")


@pytest.fixture
def evaluar(config):
    """Normaliza y clasifica una oferta armada en el test."""

    def _evaluar(titulo: str, descripcion: str = "", ubicacion: str = "",
                 empresa: str = "Empresa") -> Job:
        raw = RawJob(fuente="test", titulo=titulo, url="https://example.com/x",
                     empresa=empresa, ubicacion=ubicacion, descripcion=descripcion)
        return classify(normalize_job(raw, config), config)

    return _evaluar
