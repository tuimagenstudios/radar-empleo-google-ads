from datetime import datetime

from radar.collectors import Collector, build_collectors
from radar.models import Clasificacion as C
from radar.notifier import ConsoleNotifier, format_job
from radar.pipeline import run
from radar.storage import Storage

FECHA = datetime(2026, 11, 5, 9, 0)


def ejecutar(config, tmp_path, collectors=None):
    storage = Storage.open(tmp_path / "radar.sqlite")
    notifier = ConsoleNotifier()
    r = run(config, collectors or build_collectors(config), storage, notifier, FECHA)
    storage.close()
    return r, notifier


def test_circuito_completo_con_la_muestra(config, tmp_path):
    r, notifier = ejecutar(config, tmp_path)
    assert r.leidas == 10
    assert r.duplicadas == 1  # la oferta 8 repite la 1
    clases = [j.clasificacion for j in r.a_notificar]
    assert clases == sorted(clases, key=lambda c: c != C.ENCAJE)  # 🟢 primero
    assert {j.raw.titulo for j in r.a_notificar if j.clasificacion == C.ENCAJE} == {
        "Analista SEM Junior", "Trafficker Digital Jr"}
    assert "RADAR // 5 NOV · 5 NUEVAS · FUENTES ONLINE" in notifier.enviados[0].texto
    assert len(notifier.enviados) == 1 + len(r.a_notificar)


def test_no_vuelve_a_notificar(config, tmp_path):  # RF-DED-03
    ejecutar(config, tmp_path)
    r, notifier = ejecutar(config, tmp_path)
    assert r.nuevas == []
    assert "SIN NOVEDADES" in notifier.enviados[0].texto
    assert "Sin ofertas nuevas hoy." in notifier.enviados[0].texto  # RF-NOT-03


class Rota(Collector):
    def fetch(self):
        raise ConnectionError("timeout")


def test_fuente_caida_no_frena_al_resto(config, tmp_path):  # RF-ERR-01, RF-ERR-02
    collectors = [Rota({"tipo": "rota", "nombre": "rota"}, config), *build_collectors(config)]
    r, notifier = ejecutar(config, tmp_path, collectors)
    assert "rota" in r.errores
    assert r.leidas == 10
    assert "⚠ rota no respondió" in notifier.enviados[0].texto
    db = Storage.open(tmp_path / "radar.sqlite")
    estados = dict(db.conn.execute("SELECT fuente, estado FROM ejecuciones").fetchall())
    assert estados == {"rota": "error", "muestra": "ok"}


def test_html_escapado(evaluar):  # RF-NOT-04
    job = evaluar("SEM Junior <Remoto> & Co", "Google Ads", "Argentina")
    texto = format_job(job)
    assert "&lt;Remoto&gt; &amp; Co" in texto
