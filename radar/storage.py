"""Base SQLite: ofertas y ejecuciones (RF-DAT-01)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from radar.models import Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS ofertas (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    huella             TEXT NOT NULL UNIQUE,
    fuente             TEXT NOT NULL,
    id_externo         TEXT,
    url                TEXT NOT NULL,
    titulo             TEXT NOT NULL,
    empresa            TEXT,
    ubicacion          TEXT,
    pais               TEXT,
    modalidad          TEXT,
    paises_habilitados TEXT,
    exp_min            INTEGER,
    exp_max            INTEGER,
    salario            TEXT,
    descripcion        TEXT,
    clasificacion      TEXT NOT NULL,
    puntaje            INTEGER NOT NULL DEFAULT 0,
    motivo             TEXT NOT NULL,
    detectada_en       TEXT NOT NULL,
    notificada_en      TEXT,
    accion_usuario     TEXT,
    accion_en          TEXT
);
CREATE TABLE IF NOT EXISTS ejecuciones (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio     TEXT NOT NULL,
    fin        TEXT,
    fuente     TEXT NOT NULL,
    estado     TEXT NOT NULL,
    leidas     INTEGER NOT NULL DEFAULT 0,
    nuevas     INTEGER NOT NULL DEFAULT 0,
    duplicadas INTEGER NOT NULL DEFAULT 0,
    error      TEXT
);
"""


def ahora() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Storage:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self.conn.executescript(SCHEMA)

    @classmethod
    def open(cls, path: str | Path, dry_run: bool = False) -> Storage:
        """En modo de prueba trabaja sobre una copia en memoria (RF-EJE-02)."""
        path = Path(path)
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            return cls(sqlite3.connect(path))
        memoria = sqlite3.connect(":memory:")
        if path.exists():
            with sqlite3.connect(path) as origen:
                origen.backup(memoria)
        return cls(memoria)

    def existe(self, huella: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM ofertas WHERE huella = ?", (huella,)).fetchone()
        return row is not None

    def guardar(self, job: Job) -> int:
        r = job.raw
        cur = self.conn.execute(
            """INSERT INTO ofertas (huella, fuente, id_externo, url, titulo, empresa, ubicacion,
                   pais, modalidad, paises_habilitados, exp_min, exp_max, salario, descripcion,
                   clasificacion, puntaje, motivo, detectada_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (job.huella, r.fuente, r.id_externo, r.url, r.titulo, r.empresa, r.ubicacion,
             job.pais, job.modalidad, json.dumps(sorted(job.paises_habilitados)),
             job.exp_min, job.exp_max, r.salario, r.descripcion,
             str(job.clasificacion), job.puntaje, job.motivo, ahora()),
        )
        self.conn.commit()
        return int(cur.lastrowid or 0)

    def marcar_notificada(self, huella: str) -> None:
        self.conn.execute("UPDATE ofertas SET notificada_en = ? WHERE huella = ?",
                          (ahora(), huella))
        self.conn.commit()

    def registrar_ejecucion(self, fuente: str, inicio: str, estado: str, leidas: int = 0,
                            nuevas: int = 0, duplicadas: int = 0, error: str | None = None) -> None:
        self.conn.execute(
            """INSERT INTO ejecuciones (inicio, fin, fuente, estado, leidas, nuevas, duplicadas,
                   error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (inicio, ahora(), fuente, estado, leidas, nuevas, duplicadas, error),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
