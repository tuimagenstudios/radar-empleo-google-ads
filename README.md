<p align="center">
  <img src="assets/radar-bot-avatar.webp" alt="Avatar del Radar de Empleo: robot con un radar y un maletín" width="180">
</p>

# Radar de Empleo Junior en Google Ads

`RADAR // GOOGLE ADS · JUNIOR · LATAM + ES`

Bot que busca ofertas de empleo junior en publicidad de búsqueda (Google Ads, SEM, PPC) en el mercado hispanohablante, las clasifica según el perfil y envía las mejores a Telegram.

[![CI](https://github.com/tuimagenstudios/radar-empleo-google-ads/actions/workflows/ci.yml/badge.svg)](https://github.com/tuimagenstudios/radar-empleo-google-ads/actions/workflows/ci.yml)

> 🚧 En desarrollo · Etapa 0 (validación de fuentes) en curso · Núcleo de la etapa 1 listo y probado con ofertas ficticias.

## Cómo funciona

```
Fuentes → Normalizador → Deduplicador → Clasificador 🟢 🟡 🔴 → SQLite → Telegram
```

- **Normalizador:** detecta el país (por nombre, ciudad o gentilicio), la modalidad, los años de experiencia y los países desde los que se puede tomar la oferta. Si la oferta no lo dice, lo marca como "sin especificar" y nunca lo supone.
- **Clasificador:** usa reglas transparentes definidas en [`config.yaml`](config.yaml). Cada oferta lleva el motivo de su clasificación.
- **Deduplicador:** reconoce la misma oferta publicada en varios portales.

## Probarlo en local

```bash
python -m venv .venv
.venv/Scripts/activate      # en Linux o macOS: source .venv/bin/activate
pip install -e ".[dev]"
python -m radar --dry-run   # muestra en consola los avisos que enviaría
pytest                      # pruebas
```

Para enviar a Telegram de verdad, copiá `.env.example` como `.env`, completá el token y el chat ID, y ejecutá `python -m radar`.

## Documentación

- [Documento de diseño](docs/diseno-radar-empleo-google-ads.md)
- [Requisitos](docs/requisitos-radar-empleo.md)
- [Guía de la etapa 0](docs/etapa-0-guia.md)
- [Identidad visual](docs/marca.md)

## Licencia

MIT

---

<p align="center">
  <img src="assets/logo-tuimagenstudios.webp" alt="Tuimagen Studios" width="120"><br>
  <sub>Un proyecto de <b>Tuimagen Studios</b> · Diseño gráfico · Marketing · IA</sub>
</p>
