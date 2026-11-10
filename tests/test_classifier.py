from radar.models import Clasificacion as C


def test_regla_de_pais(evaluar):  # RF-CFG-03
    assert evaluar("Analista SEM Junior", "Remoto.", "Argentina").clasificacion == C.ENCAJE
    assert evaluar("Analista SEM Junior", "Remoto LATAM.").clasificacion == C.ENCAJE
    assert evaluar("Analista SEM Junior",
                   "Remoto desde cualquier país.").clasificacion == C.ENCAJE
    job = evaluar("Analista SEM Junior", "Remoto. Solo residentes en España.")
    assert job.clasificacion == C.REVISAR
    assert "requiere residencia en España" in job.motivo


def test_remoto_sin_paises_queda_para_revisar(evaluar):
    job = evaluar("Analista Google Ads Junior", "Modalidad remota.")
    assert job.clasificacion == C.REVISAR
    assert "sin especificar" in job.motivo


def test_paid_media_sin_busqueda_se_descarta(evaluar):  # RF-CLA-04
    job = evaluar("Paid Media Junior (Meta y TikTok)", "Pauta en Meta Ads.", "Argentina")
    assert job.clasificacion == C.DESCARTE


def test_paid_media_con_google_cuenta(evaluar):  # RF-CLA-04
    job = evaluar("Paid Media Junior", "Campañas en Meta y Google.", "Argentina")
    assert job.clasificacion == C.REVISAR  # especialidad débil: nunca 🟢 directo


def test_senior_en_el_titulo_se_descarta(evaluar):
    assert evaluar("SEM Senior", "Google Ads.", "Argentina").clasificacion == C.DESCARTE
    assert evaluar("SEM Sr.", "Google Ads.", "Argentina").clasificacion == C.DESCARTE


def test_senior_en_la_descripcion_no_descarta(evaluar):
    job = evaluar("Analista SEM Junior", "Reportarás al Head of Marketing.", "Argentina")
    assert job.clasificacion == C.ENCAJE


def test_leads_no_es_lead(evaluar):  # RF-CLA-05
    job = evaluar("Analista SEM Junior", "Generación de leads con Google Ads.", "Argentina")
    assert job.clasificacion == C.ENCAJE


def test_experiencia_excesiva_se_descarta(evaluar):
    job = evaluar("Analista de Google Ads", "Mínimo 3 años de experiencia.", "Argentina")
    assert job.clasificacion == C.DESCARTE
    assert "3+ años" in job.motivo


def test_rango_de_experiencia_acorde_cuenta_como_nivel(evaluar):
    job = evaluar("Analista de Google Ads", "Experiencia de 1 a 2 años.", "Argentina")
    assert job.clasificacion == C.ENCAJE


def test_sin_especialidad_se_descarta(evaluar):
    job = evaluar("Community Manager Junior", "Redes sociales.", "Argentina")
    assert job.clasificacion == C.DESCARTE
    assert job.motivo == "sin señales de Google Ads o SEM"


def test_fuera_de_mercado(evaluar):  # RF-NOR-07
    job = evaluar("Analista SEM Junior", "Campañas de Google Ads.", "Miami, Estados Unidos")
    assert job.clasificacion == C.DESCARTE
    assert "fuera del mercado" in job.motivo


def test_oferta_en_ingles(evaluar):  # RF-NOR-08
    job = evaluar("Google Ads Specialist", "We are looking for you to join our team.")
    assert job.clasificacion == C.DESCARTE


def test_terminos_regionales(evaluar):  # RF-CLA-02
    assert evaluar("Trafficker Digital Jr", "", "Argentina").clasificacion == C.ENCAJE
    assert evaluar("Analista PPC Junior", "", "Argentina").clasificacion == C.ENCAJE


def test_todas_tienen_motivo(evaluar):  # RF-CLA-06
    for titulo in ("Analista SEM Junior", "SEM Senior", "Contador", "PPC Jr"):
        assert evaluar(titulo).motivo


def test_puesto_de_liderazgo_se_descarta(evaluar):
    """El aviso real que pasó el filtro el 10/11/2026: PO Paid Media, Astra Group."""
    po = evaluar("PO Paid Media", "Expertise en SEO y SEM. 100% remoto LATAM.")
    assert po.clasificacion == C.DESCARTE and "po" in po.motivo
    lider = evaluar("Analista de Paid Media", "Campañas de Google Ads. Experiencia liderando "
                    "equipo de adquisición. Remoto LATAM.")
    assert lider.clasificacion == C.DESCARTE and "liderazgo" in lider.motivo


def test_mencionar_al_lider_no_descarta(evaluar):
    job = evaluar("Analista SEM Junior", "Campañas de Google Ads. Reportarás al líder del "
                  "equipo de performance. Remoto LATAM.")
    assert job.clasificacion == C.ENCAJE
