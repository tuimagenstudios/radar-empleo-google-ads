"""Lector de Gmail con respuestas simuladas (sin red ni credenciales reales)."""

import base64

import pytest

from radar.collectors import gmail
from radar.collectors.gmail import GmailCollector, a_correo, dominio
from radar.gmail_auth import guardar_en_env
from radar.models import RawJob


def b64(texto):
    return base64.urlsafe_b64encode(texto.encode()).decode().rstrip("=")


def mensaje(id_, remitente):
    return {"id": id_, "payload": {
        "headers": [{"name": "From", "value": remitente}, {"name": "Subject", "value": "Alerta"}],
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/plain", "body": {"data": b64("Analista SEM Junior")}},
            {"mimeType": "text/html", "body": {"data": b64("<a href='https://x'>SEM</a>")}},
        ]}}


class Resp:
    def __init__(self, data, status=200):
        self.data, self.status_code = data, status

    def json(self):
        return self.data

    def raise_for_status(self):
        assert self.status_code < 400


class Sesion:
    def __init__(self, mensajes, status_token=200):
        self.mensajes = {m["id"]: m for m in mensajes}
        self.status_token, self.consultas = status_token, []

    def post(self, url, data, timeout):
        return Resp({"access_token": "tok"}, self.status_token)

    def get(self, url, headers, params, timeout):
        if url.endswith("/messages"):
            self.consultas.append(params["q"])
            return Resp({"messages": [{"id": i} for i in self.mensajes]})
        return Resp(self.mensajes[url.rsplit("/", 1)[-1]])


@pytest.fixture
def credenciales(monkeypatch):
    for clave in gmail.ENV:
        monkeypatch.setenv(clave, "falso")


@pytest.mark.parametrize("remitente, esperado", [
    ("Bumeran <alertas@mail.bumeran.com.ar>", "bumeran.com.ar"),
    ("noreply@zonajobs.com.ar", "zonajobs.com.ar"),
    ("Indeed <alert@indeed.com>", "indeed.com"),
    ("x@ar.computrabajo.com", "computrabajo.com"),
])
def test_dominio(remitente, esperado):
    assert dominio(remitente) == esperado


def test_a_correo_decodifica_partes():
    correo = a_correo(mensaje("1", "a@bumeran.com.ar"))
    assert correo.texto == "Analista SEM Junior"
    assert "href" in correo.html


def test_usa_el_analizador_del_portal_y_saltea_desconocidos(config, credenciales,
                                                           monkeypatch):
    def analizador(correo, fuente):
        return [RawJob(fuente=fuente, titulo=correo.texto, url="https://x")]

    monkeypatch.setitem(gmail.ANALIZADORES, "bumeran.com.ar", analizador)
    sesion = Sesion([mensaje("1", "a@bumeran.com.ar"), mensaje("2", "b@desconocido.com")])
    fuente = {"tipo": "gmail", "nombre": "alertas", "remitentes": ["bumeran.com.ar"], "dias": 2}
    jobs = GmailCollector(fuente, config, session=sesion).fetch()
    assert [j.titulo for j in jobs] == ["Analista SEM Junior"]
    assert sesion.consultas == ["from:(bumeran.com.ar) newer_than:2d"]


def test_un_analizador_roto_no_frena_al_resto(config, credenciales, monkeypatch):
    def roto(correo, fuente):
        raise ValueError("formato nuevo")

    monkeypatch.setitem(gmail.ANALIZADORES, "bumeran.com.ar", roto)
    sesion = Sesion([mensaje("1", "a@bumeran.com.ar")])
    assert GmailCollector({"tipo": "gmail"}, config, session=sesion).fetch() == []


def test_token_vencido_da_mensaje_claro(config, credenciales):
    sesion = Sesion([], status_token=400)
    with pytest.raises(RuntimeError, match="gmail_auth"):
        GmailCollector({"tipo": "gmail"}, config, session=sesion).fetch()


def test_guardar_en_env_reemplaza_sin_duplicar(tmp_path):
    env = tmp_path / ".env"
    env.write_text("A=1\nGMAIL_REFRESH_TOKEN=\n", encoding="utf-8")
    guardar_en_env(env, "GMAIL_REFRESH_TOKEN", "nuevo")
    guardar_en_env(env, "OTRA", "x")
    assert env.read_text(encoding="utf-8") == "A=1\nGMAIL_REFRESH_TOKEN=nuevo\nOTRA=x\n"
