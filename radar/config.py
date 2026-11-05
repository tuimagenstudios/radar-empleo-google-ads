"""Carga y validación de config.yaml (RF-CFG-01, RF-CFG-05)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from radar.locations import BY_CODE

TERM_KEYS = (
    "especialidad_fuerte", "especialidad_debil", "menciona_busqueda",
    "nivel_inicial", "experiencia_afin", "descarte",
)


class ConfigError(ValueError):
    """La configuración tiene un campo faltante o inválido."""


@dataclass
class Config:
    pais_base: str
    experiencia_max_anios: int
    zona_horaria: str
    mercados: set[str]
    terminos: dict[str, list[str]]
    fuentes: list[dict] = field(default_factory=list)
    base_de_datos: str = "data/radar.sqlite"
    raiz: Path = Path(".")

    def ruta(self, relativa: str) -> Path:
        return (self.raiz / relativa).resolve()


def load_config(path: str | Path) -> Config:
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError as exc:
        raise ConfigError(f"No existe el archivo de configuración: {path}") from exc

    perfil = data.get("perfil") or {}
    for key in ("pais_base", "experiencia_max_anios", "zona_horaria"):
        if key not in perfil:
            raise ConfigError(f"Falta perfil.{key} en {path.name}")

    mercados = {str(c).upper() for c in data.get("mercados") or []}
    if not mercados:
        raise ConfigError("La lista 'mercados' está vacía")
    desconocidos = sorted((mercados | {str(perfil["pais_base"]).upper()}) - set(BY_CODE))
    if desconocidos:
        raise ConfigError(f"Códigos de país desconocidos: {', '.join(desconocidos)}")

    terminos = data.get("terminos") or {}
    for key in TERM_KEYS:
        if not isinstance(terminos.get(key), list):
            raise ConfigError(f"Falta la lista terminos.{key}")

    return Config(
        pais_base=str(perfil["pais_base"]).upper(),
        experiencia_max_anios=int(perfil["experiencia_max_anios"]),
        zona_horaria=str(perfil["zona_horaria"]),
        mercados=mercados,
        terminos={k: [str(t) for t in terminos[k]] for k in TERM_KEYS},
        fuentes=list(data.get("fuentes") or []),
        base_de_datos=str(data.get("base_de_datos", "data/radar.sqlite")),
        raiz=path.parent.resolve(),
    )
