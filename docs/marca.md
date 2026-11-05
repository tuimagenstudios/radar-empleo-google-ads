# Identidad visual del proyecto

El Radar de Empleo se presenta con la identidad de **Tuimagen Studio**.
**Fuente:** Brand Kit de Tuimagen Studio en Notion (versión del 14 de octubre de 2026). Si el Brand Kit cambia, este archivo se actualiza.

---

## Paleta

El fondo es `deep-space` siempre. El texto sobre un relleno neón va en `deep-space`, nunca en blanco.

| Token | Valor | Uso en este proyecto |
|---|---|---|
| `deep-space` | `#05091a` | Fondo de la página de resultados, del banner del README y de los GIF de demostración |
| `dark-navy` | `#0d1b3e` | Tarjetas de oferta y paneles de métricas |
| `soft-white` | `#e8f4ff` | Texto principal |
| `muted-blue` | `#8ba3cc` | Texto secundario, metadatos, ofertas descartadas |
| `neon-cyan` | `#00e0ff` | Color primario: enlaces, botón "Ver oferta", ofertas 🟡 *para revisar* |
| `neon-green` | `#00ff88` | Ofertas 🟢 *buen encaje* y estado "en vivo" de las fuentes |
| `electric-violet` | `#a855f7` | Acento de alma: una sola palabra clave o un momento destacado por vista |
| `line` | `rgba(139,163,204,0.22)` | Bordes y separadores |
| `cyan-soft` · `green-soft` · `violet-soft` | Neón al 12–16 % | Fondos de las etiquetas |

**Asignación de la clasificación** (decisión provisional): la paleta de marca no tiene amarillo ni rojo, así que en las piezas visuales se usa:

| Clasificación | Color | Etiqueta |
|---|---|---|
| 🟢 Buen encaje | `neon-green` | `ENCAJE` |
| 🟡 Para revisar | `neon-cyan` | `REVISAR` |
| 🔴 Descartada | `muted-blue` | `DESCARTE` |

En Telegram se mantienen los emojis 🟢 🟡 🔴, porque ahí no se controlan los colores.

**No usar:** fondos claros o pastel, degradados decorativos ni imágenes de stock corporativas.

## Tipografía

Las tres familias están en Google Fonts.

| Estilo | Familia | Tamaño / interlineado · peso | Uso |
|---|---|---|---|
| `display` | Space Grotesk | 72 / 76 · 700 · −0.03em | Banner del README, portada del caso de estudio |
| `h1` | Space Grotesk | 48 / 54 · 700 | Título de la página de resultados |
| `h2` | Space Grotesk | 32 / 40 · 600 | Secciones |
| `h3` | Space Grotesk | 22 / 30 · 600 | Título de cada oferta |
| `lead` | Syne | 20 / 32 · 500 | Entradillas |
| `body` | Syne | 16 / 27 · 400 | Texto corrido |
| `small` | Syne | 14 / 22 · 400 | Texto secundario |
| `hud` | JetBrains Mono | 12 / 16 · 500 · +0.08em · MAYÚSCULAS | Etiquetas de sistema |
| `code` | JetBrains Mono | 14 / 22 · 400 | Código y URLs |

## Forma

- **Espaciado:** base de 4 px (`space-1` a `space-16`).
- **Esquinas:** afiladas. 0 px en bloques, 2 px en etiquetas y 4 px como máximo en botones y tarjetas.
- **Sombras:** `glow-cyan` en el botón principal; `glow-violet` solo para un momento destacado.
- **Movimiento:** 120 ms en *hover*, 220 ms en tarjetas, 480 ms en entradas de sección y 2400 ms en el pulso neón de "en vivo".

## Cómo se aplica en cada pieza

### Etiquetas HUD

Formato del Brand Kit: el nombre del sistema en cyan, después `//` y el detalle en `muted-blue`.

```
RADAR // GOOGLE ADS · JUNIOR
RADAR // 4 NUEVAS · FUENTES ONLINE
RADAR // LINKEDIN · ERROR
```

**Regla de oro de la marca:** cada titular en Space Grotesk lleva una etiqueta HUD o un acento violeta.

### Mensajes de Telegram

Telegram no permite elegir colores ni tipografías. La marca se traslada así:

- La etiqueta HUD va en monoespaciada, con la etiqueta `<code>` de HTML, en la cabecera del resumen:
  ```
  RADAR // 5 NOV · 4 NUEVAS · FUENTES ONLINE
  ```
- La voz es directa y precisa, sin relleno. Por ejemplo: "Encaja: junior, campañas de búsqueda, remoto LATAM."
- La foto de perfil del bot es el logo o un isotipo sobre fondo `deep-space`.

### README y caso de estudio

- Banner superior: fondo `deep-space`, título en Space Grotesk, etiqueta HUD en cyan y un acento violeta.
- Diagrama de arquitectura con los colores de la marca.
- GIF de demostración grabado con el tema oscuro de Telegram, para que combine con `deep-space`.

### Página de resultados (etapa 3)

- Cada oferta es una tarjeta `dark-navy` con una etiqueta HUD (`LINKEDIN // ARGENTINA · REMOTO`), el título en h3, los detalles en `muted-blue` y la etiqueta de clasificación.
- El panel de métricas muestra las cifras en Space Grotesk y las etiquetas en HUD.

## Voz

Mentor creativo, compañero de ruta. Directa pero nunca fría, técnica con propósito, con una metáfora cuando suma.
**Fuera de la marca:** lo genérico o corporativo vacío, las promesas sin sustento y los elogios exagerados.

## Recursos pendientes

- [ ] **Logo** en SVG o PNG con fondo transparente. El Brand Kit todavía no lo tiene cargado.
- [ ] Isotipo cuadrado para la foto de perfil del bot de Telegram (mínimo 512 × 512 px).
