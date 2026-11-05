from radar.dedup import huella
from radar.models import RawJob
from radar.storage import Storage


def raw(titulo, empresa):
    return RawJob(fuente="t", titulo=titulo, empresa=empresa, url="https://example.com")


def test_misma_oferta_en_dos_portales():  # RF-DED-01
    assert huella(raw("Analista SEM Junior", "Agencia Ejemplo")) == \
        huella(raw("Analista SEM Jr (Remoto)", "Agencia Ejemplo S.A."))


def test_ofertas_distintas():
    assert huella(raw("Analista SEM Junior", "Agencia A")) != \
        huella(raw("Analista SEM Junior", "Agencia B"))


def test_dry_run_no_escribe_en_disco(tmp_path, evaluar):  # RF-EJE-02
    db = tmp_path / "radar.sqlite"
    storage = Storage.open(db, dry_run=True)
    job = evaluar("Analista SEM Junior")
    job.huella = "abc"
    storage.guardar(job)
    assert storage.existe("abc")
    storage.close()
    assert not db.exists()


def test_guardar_y_existe(tmp_path, evaluar):  # RF-DAT-01
    storage = Storage.open(tmp_path / "radar.sqlite")
    job = evaluar("Analista SEM Junior")
    job.huella = "xyz"
    storage.guardar(job)
    storage.close()
    assert Storage.open(tmp_path / "radar.sqlite").existe("xyz")
