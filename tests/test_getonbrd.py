"""Recolector de Get on Board con respuestas simuladas (sin red)."""

import time

from radar.classifier import classify
from radar.collectors.getonbrd import GetOnBoardCollector, a_raw_job
from radar.models import Clasificacion as C
from radar.normalizer import normalize_job

AHORA = int(time.time())


def item(id_, titulo, modalidad="fully_remote", paises=("Remote",), seniority="2",
         descripcion="<p>Gestión de campañas de <b>Google Ads</b>.</p>", publicada=AHORA,
         lang="es"):
    return {
        "id": id_,
        "links": {"public_url": f"https://www.getonbrd.com/jobs/{id_}"},
        "attributes": {
            "title": titulo, "description": descripcion, "remote_modality": modalidad,
            "remote_zone": None, "countries": list(paises), "lang": lang,
            "min_salary": 800, "max_salary": 1000, "published_at": publicada,
            "seniority": {"data": {"id": seniority}}, "modality": {"data": {"id": "1"}},
            "company": {"data": {"attributes": {"name": "Empresa Ficticia"}}},
        },
    }


class FakeResp:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, items):
        self.items, self.headers, self.consultas = items, {}, []

    def get(self, url, params, timeout):
        self.consultas.append(params["query"])
        return FakeResp({"data": self.items, "meta": {"total_pages": 1}})


def test_mapeo_de_campos():
    raw = a_raw_job(item("sem-jr", "Analista SEM"), "getonbrd")
    assert raw.url == "https://www.getonbrd.com/jobs/sem-jr"
    assert raw.empresa == "Empresa Ficticia"
    assert raw.nivel == "Junior"
    assert raw.salario == "USD 800–1.000 / mes"
    assert "Google Ads" in raw.descripcion and "<b>" not in raw.descripcion


def test_remoto_total_queda_abierto(config):
    job = classify(normalize_job(a_raw_job(item("a", "Analista SEM"), "g"), config), config)
    assert job.paises_habilitados == {"*"}
    assert job.clasificacion == C.ENCAJE


def test_remoto_local_restringe_pais(config):
    raw = a_raw_job(item("b", "Analista SEM", "remote_local", ["Chile"]), "g")
    job = classify(normalize_job(raw, config), config)
    assert job.paises_habilitados == {"CL"}
    assert job.clasificacion == C.REVISAR


def test_seniority_de_la_fuente_descarta(config):
    raw = a_raw_job(item("c", "Especialista SEM", seniority="4"), "g")
    assert classify(normalize_job(raw, config), config).clasificacion == C.DESCARTE


def test_fetch_deduplica_y_filtra_viejas(config):
    viejo = AHORA - 90 * 86400
    sesion = FakeSession([item("a", "SEM Jr"), item("viejo", "SEM Jr 2", publicada=viejo)])
    fuente = {"tipo": "getonbrd", "nombre": "getonbrd", "consultas": ["sem", "ppc"]}
    jobs = GetOnBoardCollector(fuente, config, session=sesion, pausa=0).fetch()
    assert [j.id_externo for j in jobs] == ["a"]  # la vieja no entra y "a" no se repite
    assert sesion.consultas == ["sem", "ppc"]
