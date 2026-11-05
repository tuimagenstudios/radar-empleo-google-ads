"""Recolector de Adzuna con respuestas simuladas (sin red ni claves reales)."""

import pytest
import requests

from radar.classifier import classify
from radar.collectors import build_collectors
from radar.collectors.adzuna import AdzunaCollector, a_raw_job, redactar
from radar.models import Clasificacion as C
from radar.normalizer import normalize_job


def resultado(id_=1, titulo="Analista <strong>SEM</strong> Junior", ciudad="Madrid",
              predicho="0"):
    return {
        "id": id_, "title": titulo, "description": "Gestión de campañas de Google Ads...",
        "created": "2026-11-04T10:00:00Z", "redirect_url": f"https://www.adzuna.es/details/{id_}",
        "company": {"display_name": "Agencia Ficticia"},
        "location": {"display_name": ciudad}, "salary_min": 22000, "salary_max": 26000,
        "salary_is_predicted": predicho,
    }


class FakeResp:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, resultados, status=200):
        self.resultados, self.status, self.headers, self.urls = resultados, status, {}, []

    def get(self, url, params, timeout):
        self.urls.append(url)
        return FakeResp({"results": self.resultados}, self.status)


@pytest.fixture
def claves(monkeypatch):
    monkeypatch.setenv("ADZUNA_APP_ID", "id-falso")
    monkeypatch.setenv("ADZUNA_APP_KEY", "clave-falsa")


def test_mapeo_y_pais():
    raw = a_raw_job(resultado(), "es", "adzuna")
    assert raw.titulo == "Analista SEM Junior"  # sin <strong>
    assert raw.ubicacion == "Madrid, España"
    assert raw.salario == "EUR 22.000–26.000 / año"
    assert raw.id_externo == "es-1"


def test_salario_estimado_no_se_muestra():
    assert a_raw_job(resultado(predicho="1"), "mx", "adzuna").salario == ""


def test_oferta_espanola_presencial_queda_para_revisar(config):
    job = classify(normalize_job(a_raw_job(resultado(), "es", "a"), config), config)
    assert job.pais == "ES"
    assert job.clasificacion == C.REVISAR  # sin país habilitado para Argentina


def test_fetch_recorre_paises_y_consultas(config, claves):
    sesion = FakeSession([resultado(1), resultado(2)])
    fuente = {"tipo": "adzuna", "paises": ["es", "mx"], "consultas": ["sem", "ppc"]}
    jobs = AdzunaCollector(fuente, config, session=sesion, pausa=0).fetch()
    assert len(sesion.urls) == 4
    assert {j.id_externo for j in jobs} == {"es-1", "es-2", "mx-1", "mx-2"}


def test_error_http_no_filtra_claves(config, claves):
    sesion = FakeSession([], status=401)
    with pytest.raises(RuntimeError) as exc:
        AdzunaCollector({"tipo": "adzuna"}, config, session=sesion, pausa=0).fetch()
    assert "clave-falsa" not in str(exc.value)


def test_error_de_red_no_filtra_claves(config, claves):
    class SesionRota(FakeSession):
        def get(self, url, params, timeout):
            raise requests.ConnectionError(f"{url}?app_id=id-falso&app_key=clave-falsa")

    with pytest.raises(RuntimeError) as exc:
        AdzunaCollector({"tipo": "adzuna"}, config, session=SesionRota([]), pausa=0).fetch()
    assert "clave-falsa" not in str(exc.value)
    assert redactar("x?app_key=abc&y=1") == "x?app_key=***&y=1"


def test_sin_claves_la_fuente_se_omite(config, monkeypatch):
    monkeypatch.delenv("ADZUNA_APP_ID", raising=False)
    monkeypatch.delenv("ADZUNA_APP_KEY", raising=False)
    config.fuentes.append({"tipo": "adzuna", "nombre": "adzuna", "activa": True})
    try:
        assert [c.nombre for c in build_collectors(config)] == ["muestra"]
    finally:
        config.fuentes.pop()
