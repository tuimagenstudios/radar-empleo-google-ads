import pytest

from radar.locations import LATAM, countries_in
from radar.normalizer import detect_experiencia, detect_modalidad, detect_paises_habilitados
from radar.text import normalize


@pytest.mark.parametrize("texto, pais", [
    ("Remoto desde CDMX", "MX"),
    ("Buenos Aires, Argentina", "AR"),
    ("Bogotá", "CO"),
    ("Madrid", "ES"),
    ("Miami, FL", "US"),
])
def test_deteccion_de_pais(texto, pais):  # RF-NOR-02, RF-CFG-04
    assert countries_in(normalize(texto))[0] == pais


def test_idioma_espanol_no_es_espana():
    assert countries_in(normalize("Nivel de español nativo")) == []


@pytest.mark.parametrize("texto, modalidad", [
    ("100% remoto", "remoto"),
    ("Home office", "remoto"),
    ("Teletrabajo", "remoto"),
    ("Esquema híbrido", "hibrido"),
    ("Trabajo presencial", "presencial"),
    ("Analista SEM", "sin_especificar"),
])
def test_modalidad(texto, modalidad):  # RF-NOR-03
    assert detect_modalidad(normalize(texto)) == modalidad


@pytest.mark.parametrize("texto, esperado", [
    ("Experiencia de 1 a 2 años", (1, 2)),
    ("1-2 años de experiencia", (1, 2)),
    ("+3 años en Google Ads", (3, None)),
    ("Más de 5 años de experiencia", (5, None)),
    ("Al menos 1 año de experiencia", (1, None)),
    ("Mínimo 2 años", (2, None)),
    ("Sin experiencia previa", (0, 0)),
    ("Edad de 18 a 25 años", (None, None)),
    ("Analista SEM", (None, None)),
])
def test_experiencia(texto, esperado):  # RF-NOR-05
    assert detect_experiencia(normalize(texto)) == esperado


def test_paises_habilitados():  # RF-NOR-04
    def h(texto, ubicacion=""):
        return detect_paises_habilitados(normalize(texto), normalize(ubicacion))

    assert h("Solo residentes en España") == {"ES"}
    assert h("Trabajá desde cualquier país") == {"*"}
    assert h("Puesto remoto", "Remoto LATAM") == set(LATAM)
    assert h("Remoto para toda Latinoamérica") == set(LATAM)
    assert h("Puesto remoto") == set()  # nunca se supone
