import pytest

from radar.text import detect_language, find_terms, normalize


@pytest.mark.parametrize("entrada, esperado", [
    ("SEM", "sem"),
    ("S.E.M.", "sem"),
    ("Campañas en Búsqueda", "campanas en busqueda"),
    ("+3 años", "+3 anos"),
    ("1–2 años", "1-2 anos"),
    ("EE.UU.", "ee uu"),
    (None, ""),
])
def test_normalize(entrada, esperado):  # RF-CLA-01
    assert normalize(entrada) == esperado


def test_find_terms_por_palabra_completa():  # RF-CLA-05
    texto = normalize("Generación de leads para clientes")
    assert find_terms(texto, ["lead"]) == []
    assert find_terms(normalize("Team Lead SEM"), ["lead"]) == ["lead"]


def test_find_terms_quita_terminos_contenidos():
    texto = normalize("Buscamos trafficker digital")
    assert find_terms(texto, ["trafficker digital", "trafficker"]) == ["trafficker digital"]


def test_detect_language():  # RF-NOR-08
    assert detect_language(normalize("Buscamos un analista para la agencia de marketing")) == "es"
    assert detect_language(normalize("We are looking for you to join our team")) == "en"
