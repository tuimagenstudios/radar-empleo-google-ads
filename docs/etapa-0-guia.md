# Etapa 0 — Validación de fuentes: guía paso a paso

**Objetivo:** confirmar que hay suficientes ofertas relevantes y elegir las dos mejores fuentes antes de programar.
**Duración:** una o dos semanas, casi todo de espera. El trabajo real son unas dos horas.
**Requisitos que cubre:** RP-01, RP-05, RP-06 y RF-VAL-01 a RF-VAL-04.

---

## Lista de control

- [ ] **Paso 1** · Crear la cuenta de Gmail del radar
- [ ] **Paso 2** · Decidir cómo llegan las alertas a esa cuenta
- [ ] **Paso 3** · Crear las alertas en cada portal
- [ ] **Paso 4** · Crear el repositorio en GitHub
- [ ] **Paso 5** · Durante una o dos semanas, anotar las ofertas en la planilla
- [ ] **Paso 6** · Analizar la planilla y elegir las dos fuentes

---

## Paso 1 · Cuenta de Gmail del radar (RP-05)

1. Crear una cuenta nueva, por ejemplo `radar.googleads.tunombre@gmail.com`.
2. Activar la verificación en dos pasos. Google la exige para el acceso por API que se configura en la etapa 1.
3. Guardar la contraseña en tu gestor de contraseñas. **No la compartas en ningún chat, tampoco en este.**

> El bot solo leerá esta cuenta y nunca tu correo personal.

## Paso 2 · Cómo llegan las alertas

Elegí una de estas dos opciones:

| Opción | Cómo funciona | Cuándo conviene |
|---|---|---|
| **A · Registrarse con la cuenta del radar** | Te registrás en cada portal con la cuenta nueva y creás ahí las alertas | Si no tenés perfiles en esos portales, o no te importa tener uno extra |
| **B · Reenviar desde tu correo personal** | Mantenés tus perfiles actuales. En tu Gmail personal creás un filtro que reenvía las alertas a la cuenta del radar | Si ya tenés perfiles armados con tu CV en esos portales |

**Para la opción B:**
1. Gmail personal → ⚙ → *Ver toda la configuración* → *Reenvío y correo POP/IMAP* → *Añadir una dirección de reenvío* → la cuenta del radar. Confirmás el código que llega a esa cuenta.
2. Creás un filtro con remitentes como `jobalerts-noreply@linkedin.com`, `alert@indeed.com`, etc., y elegís *Reenviar a* la cuenta del radar.
3. Para saber los remitentes exactos, esperá a que llegue la primera alerta de cada portal y copiá la dirección.

## Paso 3 · Alertas por portal (RP-06, RF-VAL-01, RF-VAL-02)

### Términos de búsqueda

Si el portal acepta búsquedas con `OR`, usá una sola alerta:

```
"Google Ads" OR SEM OR PPC OR "trafficker digital" OR "paid media"
```

Si no las acepta, creá una alerta por cada término, en este orden de prioridad:

1. `Google Ads`
2. `SEM`
3. `trafficker digital`
4. `paid media`
5. `PPC`
6. `marketing digital junior`

**Frecuencia:** diaria en todas.

### Portales prioritarios

| # | Portal | Sitio | Ubicación de la alerta | Filtros recomendados |
|---|---|---|---|---|
| 1 | **LinkedIn** | linkedin.com/jobs | Una alerta para "Argentina" y otra para "América Latina" | Nivel de experiencia: *Prácticas*, *Sin experiencia* y *Algo de responsabilidad*. Tipo de empleo: *En remoto* en la alerta de Latinoamérica |
| 2 | **LinkedIn** | linkedin.com/jobs | "España" | Igual que la fila anterior, con *En remoto*. Sirve para medir cuántas ofertas españolas aceptan contratar desde fuera |
| 3 | **Indeed Argentina** | ar.indeed.com | "Argentina" o "Remoto" | Ordenar por fecha |
| 4 | **Indeed México** | mx.indeed.com | "Remoto" | Ordenar por fecha |
| 5 | **Computrabajo Argentina** | ar.computrabajo.com | Sin ubicación, o "Remoto" | Una alerta por término |
| 6 | **Computrabajo México y Colombia** | mx.computrabajo.com, co.computrabajo.com | "Remoto" | Una alerta por término |
| 7 | **Bumeran / ZonaJobs** | bumeran.com.ar, zonajobs.com.ar | Argentina | Nivel: *Junior* o *Sin experiencia* |
| 8 | **InfoJobs** | infojobs.net | "Teletrabajo" | Experiencia mínima: *No requerida* o *Al menos 1 año* |
| 9 | **Get on Board** | getonbrd.com | Remoto | Categoría *Marketing digital* |

> No hace falta crearlas todas el primer día. Con los portales 1, 3, 5 y 7 ya hay una buena muestra. Los demás se pueden sumar durante la primera semana.

### Registro de las alertas creadas

Anotá cada alerta para poder replicarla o ajustarla después:

| Portal | Términos | Ubicación | Filtros | Remitente del correo | Fecha de creación |
|---|---|---|---|---|---|
| | | | | | |

## Paso 4 · Repositorio en GitHub (RP-01)

1. En github.com → **New repository**.
2. Nombre: `radar-empleo-google-ads` · Visibilidad: **Public** · Licencia: **MIT**.
3. **No** marques las opciones para agregar un README ni un `.gitignore`: ya están creados en tu carpeta local.
4. Pasame el enlace del repositorio y conecto la carpeta local con él.

## Paso 5 · Llenar la planilla (RF-VAL-03)

Archivo: [`data/validacion.csv`](../data/validacion.csv). Podés abrirlo en Excel o importarlo en Google Sheets.

- Cada día, o cada dos días, abrí los correos de alerta y anotá **todas** las ofertas, también las que no sirven. Las que no sirven son las que enseñan al filtro qué descartar.
- **Meta:** al menos 30 ofertas, idealmente con unas 10 relevantes.

| Columna | Qué poner |
|---|---|
| `fecha` | Día en que llegó la alerta (AAAA-MM-DD) |
| `fuente` | Portal de la alerta: `linkedin`, `indeed_ar`, `computrabajo_ar`, etc. |
| `pais` | País de la empresa o del puesto |
| `titulo` / `empresa` / `url` | Copiados tal cual |
| `modalidad` | `remoto`, `hibrido`, `presencial` o `sin_especificar` |
| `paises_habilitados` | Lo que diga la oferta, o `sin_especificar` |
| `experiencia` | Lo que pida la oferta ("0-1 años", "+3 años"…), o `sin_especificar` |
| `relevante` | `si`, `no` o `dudosa`: ¿te postularías? |
| `motivo` | Por qué, en pocas palabras: "senior", "solo Meta Ads", "requiere residencia en España"… |
| `duplicada_de` | Si ya anotaste la misma oferta desde otro portal, el número de fila de la primera |

## Paso 6 · Análisis y elección de fuentes (RF-VAL-04)

Cuando tengas las 30 ofertas, pasame la planilla y la analizamos juntos para obtener:

- las ofertas relevantes por fuente, para elegir las dos mejores;
- los motivos de descarte más frecuentes, que se convierten en las reglas del filtro;
- el porcentaje de duplicados entre portales;
- los términos que aparecen en las ofertas relevantes y no estaban en la lista.

El resultado se documenta en el README y se pasa a la etapa 1.

---

## Si después de dos semanas hay muy pocas ofertas relevantes

Es un resultado válido, y conviene saberlo antes de programar. Las opciones son:

1. Ampliar los términos: "analista de marketing digital", "ejecutivo de cuentas digitales", "performance marketing junior".
2. Sumar portales nacionales de otros países: OCC Mundial (México), Laborum (Chile), elempleo (Colombia).
3. Incluir puestos de "paid media" que piden Meta Ads y Google Ads juntos.
