"""Clasificación 🟢 🟡 🔴 con reglas transparentes (sección 6 del diseño, RF-CLA-*)."""

from __future__ import annotations

from radar.config import Config
from radar.locations import BY_CODE, LATAM
from radar.models import Clasificacion, Job
from radar.text import find_terms, normalize

_ETIQUETAS = {
    "google ads": "Google Ads", "adwords": "AdWords", "sem": "SEM", "ppc": "PPC",
    "paid search": "Paid search", "busqueda pagada": "Búsqueda pagada",
    "trafficker digital": "Trafficker digital", "trafficker": "Trafficker",
    "ga4": "GA4", "google analytics": "Google Analytics", "merchant center": "Merchant Center",
    "google tag manager": "Tag Manager", "campanas": "Campañas", "palabras clave": "Palabras clave",
    "keywords": "Keywords", "conversiones": "Conversiones", "pujas": "Pujas",
    "optimizacion": "Optimización",
}


def etiqueta(term: str) -> str:
    return _ETIQUETAS.get(term, term.capitalize())


def nombre_pais(code: str) -> str:
    return BY_CODE[code].name if code in BY_CODE else code


def evaluar_ubicacion(job: Job, config: Config) -> tuple[bool, str]:
    """¿Se puede tomar desde el país base? Devuelve (ok, motivo) (regla de país, sección 6)."""
    base = config.pais_base
    habilitados = job.paises_habilitados
    if "*" in habilitados:
        return True, "abierta a cualquier país"
    if base in habilitados:
        if habilitados >= LATAM:
            return True, "remoto LATAM"
        return True, f"habilitada para {nombre_pais(base)}"
    if habilitados:
        otros = ", ".join(sorted(nombre_pais(c) for c in habilitados))
        return False, f"requiere residencia en {otros}"
    if job.pais == base:
        return True, f"ubicada en {nombre_pais(base)}"
    if job.modalidad in ("presencial", "hibrido") and job.pais:
        return False, f"{job.modalidad} en {nombre_pais(job.pais)}"
    return False, "países habilitados sin especificar"


def classify(job: Job, config: Config) -> Job:
    t = config.terminos
    texto = normalize(f"{job.raw.titulo} {job.raw.descripcion}")

    fuertes = find_terms(texto, t["especialidad_fuerte"])
    debiles = find_terms(texto, t["especialidad_debil"])
    menciona_busqueda = bool(find_terms(texto, t["menciona_busqueda"]))
    nivel_fuente = normalize(job.raw.nivel)
    nivel = find_terms(f"{nivel_fuente} {texto}", t["nivel_inicial"])
    afines = find_terms(texto, t["experiencia_afin"])
    # Solo en el título y en el nivel que informa la fuente: la descripción suele nombrar
    # a otros ("reportarás al Head of Marketing") y eso no dice nada del nivel del puesto.
    descarte = find_terms(f"{normalize(job.raw.titulo)} {nivel_fuente}", t["descarte"])
    job.terminos = [etiqueta(x) for x in fuertes + afines]

    def resultado(clase: Clasificacion, motivo: str, puntaje: int = 0) -> Job:
        job.clasificacion, job.motivo, job.puntaje = clase, motivo, puntaje
        return job

    # 🔴 Descartes duros
    if job.fuera_de_mercado:
        return resultado(Clasificacion.DESCARTE,
                         f"fuera del mercado objetivo ({nombre_pais(job.pais or '?')})")
    if job.idioma == "en":
        return resultado(Clasificacion.DESCARTE, "oferta en otro idioma")
    if descarte:
        return resultado(Clasificacion.DESCARTE, f"nivel fuera de perfil ({', '.join(descarte)})")
    max_anios = config.experiencia_max_anios
    if job.exp_min is not None and job.exp_min > max_anios:
        return resultado(Clasificacion.DESCARTE, f"pide {job.exp_min}+ años de experiencia")
    especialidad = bool(fuertes) or (bool(debiles) and menciona_busqueda)
    if not especialidad:
        motivo = (f"{debiles[0]} sin Google Ads ni búsqueda" if debiles
                  else "sin señales de Google Ads o SEM")
        return resultado(Clasificacion.DESCARTE, motivo)

    # 🟢 / 🟡
    nivel_ok = bool(nivel) or (job.exp_max is not None and job.exp_max <= max_anios) \
        or job.exp_min == 0
    ubicacion_ok, motivo_ubicacion = evaluar_ubicacion(job, config)

    especialidad_txt = " + ".join(etiqueta(x) for x in (fuertes or debiles)[:2])
    if nivel:
        nivel_txt = nivel[0]
    elif nivel_ok:
        nivel_txt = "experiencia acorde"
    else:
        nivel_txt = "nivel sin especificar"
    motivo = f"{especialidad_txt} · {nivel_txt} · {motivo_ubicacion}"

    puntaje = (40 if fuertes else 20) + (20 if nivel_ok else 0) \
        + min(5 * len(afines), 20) + (20 if ubicacion_ok else 0)

    if fuertes and nivel_ok and ubicacion_ok:
        return resultado(Clasificacion.ENCAJE, motivo, puntaje)
    return resultado(Clasificacion.REVISAR, motivo, puntaje)
