"""Modo "solo Argentina": la configuración real desde el 5/11/2026."""

from dataclasses import replace

import pytest

from radar.classifier import classify
from radar.models import Clasificacion as C
from radar.models import RawJob
from radar.normalizer import normalize_job


@pytest.fixture
def solo_ar(config):
    return replace(config, mercados={"AR"})


def evaluar(cfg, titulo, descripcion="", ubicacion=""):
    raw = RawJob(fuente="t", titulo=titulo, url="https://example.com", ubicacion=ubicacion,
                 descripcion=descripcion)
    return classify(normalize_job(raw, cfg), cfg)


def test_config_real_es_solo_argentina():
    from radar.config import load_config
    from tests.conftest import ROOT
    assert load_config(ROOT / "config.yaml").mercados == {"AR"}


def test_oferta_en_argentina_encaja(solo_ar):
    assert evaluar(solo_ar, "Analista SEM Junior", "", "Buenos Aires").clasificacion == C.ENCAJE


def test_remoto_latam_y_global_siguen_entrando(solo_ar):
    assert evaluar(solo_ar, "Analista SEM Junior", "Remoto LATAM.").clasificacion == C.ENCAJE
    assert evaluar(solo_ar, "Analista SEM Junior",
                   "Remoto desde cualquier país.").clasificacion == C.ENCAJE


def test_solo_otro_pais_se_descarta(solo_ar):
    job = evaluar(solo_ar, "Analista SEM Junior", "Remoto. Solo residentes en España.")
    assert job.clasificacion == C.DESCARTE
    assert "fuera del mercado" in job.motivo


def test_presencial_en_otro_pais_se_descarta(solo_ar):
    job = evaluar(solo_ar, "Asistente Google Ads", "Presencial.", "Lima, Perú")
    assert job.clasificacion == C.DESCARTE
