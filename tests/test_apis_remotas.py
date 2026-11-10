"""Recolectores de Himalayas, Jobicy y Remotive con respuestas simuladas (sin red)."""

import time
from datetime import UTC, datetime, timedelta

from radar.classifier import classify
from radar.collectors import TIPOS, jobicy, remotive
from radar.collectors import himalayas as hima
from radar.models import Clasificacion as C
from radar.normalizer import normalize_job

AHORA = int(time.time())
HOY = datetime.now(UTC).isoformat()
VIEJA = (datetime.now(UTC) - timedelta(days=90)).isoformat()
LATAM_EN = ["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Ecuador",
            "Guatemala", "Mexico", "Panama", "Paraguay", "Peru", "Uruguay", "Venezuela"]
DESCRIPCION = ("<p>Buscamos una persona para la gestión de campañas de <b>Google Ads</b> "
               "y el análisis de palabras clave para los clientes de la agencia.</p>")


class FakeResp:
    status_code = 200

    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


class FakeSession:
    def __init__(self, data):
        self.data, self.headers, self.pedidos = data, {}, []

    def get(self, url, params, timeout):
        self.pedidos.append(params)
        return FakeResp(self.data)


def evaluar(raw, config):
    return classify(normalize_job(raw, config), config)


# ---------- Himalayas ----------

def oferta_hima(guid, titulo="Analista SEM Junior", restricciones=(), seniority=("Entry-level",),
                publicada=AHORA):
    return {"title": titulo, "companyName": "Agencia Ficticia", "guid": guid,
            "applicationLink": f"{guid}?utm_source=api", "description": DESCRIPCION,
            "locationRestrictions": list(restricciones), "seniority": list(seniority),
            "minSalary": 500, "maxSalary": 800, "currency": "USD", "salaryPeriod": "monthly",
            "pubDate": publicada}


def test_himalayas_mapea_campos():
    raw = hima.a_raw_job(oferta_hima("https://himalayas.app/x"), "himalayas", "AR")
    assert raw.url == "https://himalayas.app/x"  # sin parámetros de rastreo
    assert raw.empresa == "Agencia Ficticia"
    assert raw.nivel == "Junior"
    assert raw.salario == "USD 500–800 / mes"
    assert "Google Ads" in raw.descripcion and "<b>" not in raw.descripcion


def test_himalayas_ubicacion(config):
    sin_limite = hima.a_raw_job(oferta_hima("a"), "h", "AR")
    assert evaluar(sin_limite, config).paises_habilitados == {"*"}
    latam = evaluar(hima.a_raw_job(oferta_hima("b", restricciones=LATAM_EN), "h", "AR"), config)
    assert "AR" in latam.paises_habilitados and latam.clasificacion == C.ENCAJE
    solo_ar = hima.a_raw_job(oferta_hima("c", restricciones=["Argentina", "Egypt"]), "h", "AR")
    assert evaluar(solo_ar, config).paises_habilitados == {"AR"}


def test_himalayas_nivel_mas_alto_descarta(config):
    raw = hima.a_raw_job(oferta_hima("d", "Especialista SEM", seniority=["Senior", "Manager"]),
                         "h", "AR")
    assert raw.nivel == "Senior"
    assert evaluar(raw, config).clasificacion == C.DESCARTE
    assert hima.nivel(["Mid-level"]) == ""


def test_himalayas_fetch_filtra_por_pais_y_fecha(config):
    viejo = AHORA - 90 * 86400
    sesion = FakeSession({"totalCount": 2, "jobs": [oferta_hima("a"),
                                                   oferta_hima("viejo", publicada=viejo)]})
    fuente = {"tipo": "himalayas", "nombre": "himalayas", "consultas": ["google ads", "ppc"]}
    jobs = hima.HimalayasCollector(fuente, config, session=sesion, pausa=0).fetch()
    assert [j.id_externo for j in jobs] == ["a"]
    assert {p["country"] for p in sesion.pedidos} == {config.pais_base}
    assert [p["q"] for p in sesion.pedidos] == ["google ads", "ppc"]


# ---------- Jobicy ----------

def oferta_jobicy(id_, geo="LATAM", nivel="Junior", publicada=HOY):
    return {"id": id_, "url": f"https://jobicy.com/jobs/{id_}", "jobTitle": "Analista SEM",
            "companyName": "Agencia &amp; Cía", "jobGeo": geo, "jobLevel": nivel,
            "jobDescription": DESCRIPCION, "pubDate": publicada,
            "salaryMin": 12000, "salaryMax": 15000, "salaryCurrency": "USD",
            "salaryPeriod": "yearly"}


def test_jobicy_mapea_campos(config):
    raw = jobicy.a_raw_job(oferta_jobicy(1), "jobicy")
    assert raw.empresa == "Agencia & Cía"
    assert raw.ubicacion == "Remoto LATAM"
    assert raw.salario == "USD 12.000–15.000 / año"
    assert evaluar(raw, config).clasificacion == C.ENCAJE
    assert jobicy.a_raw_job(oferta_jobicy(2, nivel="Any"), "jobicy").nivel == ""


def test_jobicy_solo_otro_pais_no_encaja(config):
    job = evaluar(jobicy.a_raw_job(oferta_jobicy(3, geo="USA"), "jobicy"), config)
    assert job.clasificacion != C.ENCAJE


def test_jobicy_fetch_deduplica_y_filtra_viejas(config):
    sesion = FakeSession({"jobs": [oferta_jobicy(1), oferta_jobicy(9, publicada=VIEJA)]})
    fuente = {"tipo": "jobicy", "nombre": "jobicy", "regiones": ["latam", "argentina"],
              "consultas": ["google ads"]}
    jobs = jobicy.JobicyCollector(fuente, config, session=sesion, pausa=0).fetch()
    assert [j.id_externo for j in jobs] == ["1"]
    assert [p["geo"] for p in sesion.pedidos] == ["latam", "argentina"]


# ---------- Remotive ----------

def oferta_remotive(id_, lugar="Worldwide", publicada=HOY):
    return {"id": id_, "url": f"https://remotive.com/remote-jobs/marketing/x-{id_}",
            "title": "Analista SEM Junior", "company_name": "Agencia Ficticia",
            "candidate_required_location": lugar, "description": DESCRIPCION,
            "publication_date": publicada[:19], "salary": ""}


def test_remotive_mapea_campos(config):
    job = evaluar(remotive.a_raw_job(oferta_remotive(7), "remotive"), config)
    assert job.raw.ubicacion == "Remoto Worldwide"
    assert job.paises_habilitados == {"*"}
    assert job.clasificacion == C.ENCAJE


def test_remotive_latin_america_en_ingles(config):
    job = evaluar(remotive.a_raw_job(oferta_remotive(8, "Latin America"), "remotive"), config)
    assert "AR" in job.paises_habilitados


def test_remotive_fetch(config):
    sesion = FakeSession({"jobs": [oferta_remotive(7), oferta_remotive(9, publicada=VIEJA)]})
    fuente = {"tipo": "remotive", "nombre": "remotive", "consultas": ["google ads"]}
    jobs = remotive.RemotiveCollector(fuente, config, session=sesion, pausa=0).fetch()
    assert [j.id_externo for j in jobs] == ["7"]


def test_tipos_registrados():
    assert {"himalayas", "jobicy", "remotive"} <= set(TIPOS)


def test_himalayas_conserva_lo_leido_si_corta_por_limite(config):
    class Limitada(FakeSession):
        def get(self, url, params, timeout):
            resp = super().get(url, params, timeout)
            resp.status_code = 429 if params["q"] == "ppc" else 200
            return resp

    sesion = Limitada({"totalCount": 1, "jobs": [oferta_hima("a")]})
    fuente = {"tipo": "himalayas", "nombre": "himalayas", "consultas": ["google ads", "ppc"]}
    jobs = hima.HimalayasCollector(fuente, config, session=sesion, pausa=0).fetch()
    assert [j.id_externo for j in jobs] == ["a"]
