# Radar de Empleo Junior en Google Ads — Requisitos

**Especificación de requisitos · v1.0 · 5 de noviembre de 2026**
Complementa al [documento de diseño](diseno-radar-empleo-google-ads.md). Cada bloque de este documento corresponde a una sección del diseño.

---

## Cómo leer este documento

- **ID:** identificador único de cada requisito (por ejemplo, `RF-CLA-03`). Los commits, las pruebas y los *issues* lo citan para que se pueda rastrear qué cubre cada uno.
  - `RP`: requisito previo (cuentas y herramientas).
  - `RF`: requisito funcional (qué hace el sistema).
  - `RNF`: requisito no funcional (cómo debe hacerlo).
- **Prioridad:**
  - **Debe:** sin esto, la etapa no está terminada.
  - **Debería:** importante, pero puede pasar a la etapa siguiente.
  - **Podría:** mejora opcional.
- **Etapa:** etapa de la hoja de ruta (0 a 3) en la que se implementa.
- **Criterio de aceptación:** prueba concreta que demuestra que el requisito se cumple.

---

## 1. Requisitos previos

Lo que hay que tener listo antes de escribir código.

| ID | Requisito | Cómo se cumple | Etapa |
|---|---|---|---|
| RP-01 | Cuenta de GitHub y repositorio público `radar-empleo-google-ads` | Crear el repositorio con licencia MIT, `.gitignore` de Python y un README provisional | 0 |
| RP-02 | Python 3.12 instalado en local | Instalarlo desde python.org; crear un entorno virtual con `python -m venv .venv` | 1 |
| RP-03 | Bot de Telegram creado | Hablar con **@BotFather**, ejecutar `/newbot` y guardar el token. Nunca se pega en el código ni en el chat | 1 |
| RP-04 | ID del chat privado | Enviarle `/start` al bot y obtener el `chat_id` con `getUpdates` | 1 |
| RP-05 | Cuenta de Gmail dedicada a las alertas | Se recomienda una cuenta nueva (por ejemplo, `radar.empleo.xx@gmail.com`) para que el bot nunca lea el correo personal | 0 |
| RP-06 | Alertas de empleo activas en los portales | Crear búsquedas guardadas con alertas diarias hacia la cuenta de RP-05 (ver sección 3) | 0 |
| RP-07 | Proyecto de Google Cloud con la API de Gmail habilitada | Crear el proyecto, habilitar la API de Gmail, configurar la pantalla de consentimiento OAuth en modo "prueba" y descargar las credenciales de escritorio | 1 |
| RP-08 | Permiso de Gmail de solo lectura | Pedir únicamente el alcance `gmail.readonly` | 1 |
| RP-09 | Claves de las APIs opcionales | InfoJobs (registro de desarrollador) y SerpAPI (plan gratuito), solo si la etapa 0 las elige | 2 |

---

## 2. Perfil y configuración

*Sección 4 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-CFG-01 | Todo el perfil de búsqueda vive en `config.yaml`: términos, niveles, mercados, modalidad, horario y fuentes activas | Debe | 1 | Cambiar un término en el archivo modifica la clasificación sin tocar el código |
| RF-CFG-02 | Lista de mercados objetivo: los 20 países hispanohablantes, sin Estados Unidos ni Puerto Rico | Debe | 1 | La lista coincide con la sección 4 del diseño; quitar un país lo excluye |
| RF-CFG-03 | Campo `pais_base: Argentina` (ciudadanía, residencia legal y cuenta bancaria) y regla de país de la sección 6 del diseño | Debe | 1 | "Remoto, solo Argentina", "Remoto LATAM" y "Remoto, cualquier país" salen 🟢; "Remoto, solo residentes en España" sale 🟡 con el motivo "requiere residencia en España" |
| RF-CFG-04 | Diccionario de ubicaciones: país, gentilicio, capitales y ciudades principales, y regiones ("LATAM", "Latinoamérica", "Cono Sur", "Europa") | Debe | 1 | "Remoto desde CDMX" se reconoce como México; "Remoto LATAM" se expande a los países latinoamericanos |
| RF-CFG-05 | Se valida la configuración al arrancar | Debería | 2 | Un campo faltante o mal escrito detiene la ejecución con un mensaje claro |

---

## 3. Fuentes y recolección

*Sección 5 del diseño.*

### 3.1 Validación de fuentes (etapa 0)

| ID | Requisito | Prioridad | Criterio de aceptación |
|---|---|---|---|
| RF-VAL-01 | Alertas creadas como mínimo en LinkedIn, Indeed y Computrabajo, y en un portal nacional por cada mercado principal (Argentina, México, España, Colombia, Chile) | Debe | Llegan correos de alerta de cada portal a la cuenta de RP-05 |
| RF-VAL-02 | Términos de búsqueda de las alertas: "Google Ads", "SEM", "PPC", "paid media junior", "trafficker digital", "asistente de marketing digital" | Debe | Cada portal tiene las alertas configuradas con estos términos |
| RF-VAL-03 | Planilla de validación con 30 ofertas reales: fuente, país, título, relevante (sí o no) y motivo | Debe | La planilla existe en `data/validacion.csv` |
| RF-VAL-04 | Selección de las dos fuentes iniciales | Debe | Queda documentada en el README con el número de ofertas relevantes por fuente |

> "Trafficker digital" es el término que usan muchas empresas latinoamericanas para este rol. Se incluye porque en Argentina, Colombia y Perú se usa tanto como "SEM".

### 3.2 Recolectores

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-REC-01 | Interfaz común: cada recolector implementa `fetch() -> list[RawJob]` | Debe | 1 | Agregar una fuente nueva no requiere modificar el resto de los módulos |
| RF-REC-02 | Recolector de Gmail: lee los correos de alertas no procesados, identifica el portal por el remitente y extrae las ofertas | Debe | 1 | Con un correo de ejemplo guardado, extrae todas sus ofertas con el título, la empresa y el enlace correctos |
| RF-REC-03 | Un analizador por formato de correo (LinkedIn, Indeed, Computrabajo, etc.) | Debe | 1–2 | Cada analizador tiene una prueba con al menos un correo real anonimizado en `tests/fixtures/` |
| RF-REC-04 | Los correos procesados se marcan con una etiqueta de Gmail (`radar/procesado`) | Debe | 1 | Una segunda ejecución no vuelve a leer los mismos correos |
| RF-REC-05 | Enlace limpio: se quitan los parámetros de rastreo (`utm_*`, `trk`, etc.) | Debería | 2 | El enlace guardado abre la oferta y no tiene parámetros de rastreo |
| RF-REC-06 | Recolectores por API (InfoJobs, Get on Board, SerpAPI) si la etapa 0 los elige | Podría | 2 | Devuelven ofertas reales y respetan los límites de su API |
| RF-REC-07 | Solo vías permitidas: APIs oficiales, RSS o correos propios. Sin extracción automatizada de portales que la prohíben | Debe | Todas | Revisión del código: no hay solicitudes a páginas de portales fuera de sus APIs |

---

## 4. Normalización y deduplicación

*Sección 8 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-NOR-01 | Cada oferta se convierte a un modelo único con los campos de la tabla `ofertas` | Debe | 1 | Las ofertas de todas las fuentes tienen la misma estructura |
| RF-NOR-02 | Detección de país a partir de la ubicación y la descripción, usando el diccionario de RF-CFG-04 | Debe | 1 | Las 30 ofertas de validación se asignan al país correcto en al menos el 90 % de los casos |
| RF-NOR-03 | Detección de modalidad: remoto, híbrido, presencial o sin especificar | Debe | 1 | "Home office", "teletrabajo" y "100 % remoto" se reconocen como remoto |
| RF-NOR-04 | Extracción de países habilitados. Si no se encuentran, se guarda "sin especificar" y nunca se supone | Debe | 1 | Una oferta sin esa información muestra "sin especificar" en el aviso |
| RF-NOR-05 | Extracción de los años de experiencia: "1 a 2 años", "+3 años", "sin experiencia" | Debe | 1 | Se extraen correctamente en las ofertas de validación que los mencionan |
| RF-NOR-06 | Extracción del salario y su moneda (ARS, MXN, EUR, COP, PEN, CLP, UYU, USD) cuando se publica | Podría | 3 | El aviso muestra el salario con su moneda, o "no publicado" |
| RF-NOR-07 | Ofertas fuera del mercado objetivo (por ejemplo, ubicadas en Estados Unidos y en inglés) se descartan antes de clasificar | Debe | 1 | Una oferta en inglés de Miami no llega a Telegram |
| RF-NOR-08 | Detección de idioma: la descripción debe estar en español | Debería | 2 | Una oferta en inglés publicada en un portal latinoamericano se marca como "otro idioma" |
| RF-DED-01 | Huella de deduplicación: título y empresa en minúsculas, sin acentos, sin palabras genéricas ("Sr.", "(remoto)") | Debe | 2 | La misma oferta recibida por LinkedIn y Computrabajo se notifica una sola vez |
| RF-DED-02 | Al encontrar un duplicado se conservan los enlaces de todas las fuentes | Debería | 2 | El aviso incluye "También en: Computrabajo" |
| RF-DED-03 | Una oferta ya notificada no se vuelve a notificar aunque reaparezca semanas después | Debe | 1 | Una nueva ejecución con los mismos datos no envía ningún aviso |

---

## 5. Clasificación

*Sección 6 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-CLA-01 | La comparación de términos ignora mayúsculas, acentos y signos | Debe | 1 | "SEM", "sem" y "S.E.M." se reconocen igual |
| RF-CLA-02 | Reconoce los términos regionales del rol: SEM, PPC, Google Ads, AdWords, trafficker digital, especialista en pauta digital, búsqueda pagada | Debe | 1 | Cada término está en `config.yaml` y tiene una prueba |
| RF-CLA-03 | Aplica las reglas 🟢 🟡 🔴 tal como están en la sección 6 del diseño | Debe | 1 | Pruebas unitarias con un caso por cada regla |
| RF-CLA-04 | "Paid media", "performance" o "pauta" solo cuentan como especialidad si la descripción también menciona Google Ads o búsqueda | Debe | 1 | "Paid media junior (Meta y TikTok)" sale 🔴 |
| RF-CLA-05 | Las señales de descarte se buscan por palabra completa | Debe | 1 | "Lead" descarta, pero "generación de leads" no |
| RF-CLA-06 | Cada clasificación guarda el puntaje y un motivo legible | Debe | 1 | Todas las ofertas en la base tienen un motivo no vacío |
| RF-CLA-07 | Prueba de regresión con el conjunto de las 30 ofertas validadas | Debe | 1 | El filtro coincide con la etiqueta manual en al menos el 80 % de los casos, y ninguna oferta etiquetada como relevante sale 🔴 |
| RF-CLA-08 | Clasificador con IA evaluado frente a las reglas sobre el mismo conjunto | Podría | 3 | Informe comparativo en el README; la IA solo se adopta si mejora la precisión |

---

## 6. Notificaciones y retroalimentación

*Sección 7 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-NOT-01 | Un mensaje por oferta 🟢 o 🟡 con el formato de la sección 7 del diseño | Debe | 1 | El mensaje recibido coincide con la plantilla |
| RF-NOT-02 | Mensaje de cabecera con el resumen del día y el estado de las fuentes | Debe | 2 | Aparece antes de las ofertas e indica las fuentes con error |
| RF-NOT-03 | Si no hay ofertas nuevas, se envía igual un aviso breve | Debe | 2 | Una ejecución sin novedades envía "Sin ofertas nuevas hoy · fuentes OK" |
| RF-NOT-04 | El texto se escapa correctamente para el formato HTML de Telegram | Debe | 1 | Un título con `<`, `&` o `*` se muestra bien y no rompe el envío |
| RF-NOT-05 | Se respetan los límites de Telegram (unos 30 mensajes por segundo y 4096 caracteres por mensaje) | Debe | 2 | Un envío de 25 ofertas llega completo, sin errores 429 |
| RF-NOT-06 | Orden: primero 🟢, después 🟡; dentro de cada grupo, por puntaje | Debería | 2 | El orden de los mensajes cumple la regla |
| RF-NOT-07 | Bandera del país en cada aviso (🇦🇷 🇲🇽 🇪🇸 …) | Podría | 3 | La bandera coincide con el país detectado |
| RF-FBK-01 | Botones "Ver oferta", "⭐ Guardar" y "✖ Descartar" | Debe | 2 | Los tres aparecen y "Ver oferta" abre el enlace |
| RF-FBK-02 | Las pulsaciones se leen con `getUpdates` al inicio de cada ejecución y se guardan en `accion_usuario` | Debe | 2 | Después de pulsar "Guardar", la siguiente ejecución registra la acción |
| RF-FBK-03 | Tras procesar una pulsación, el mensaje se edita para mostrar el estado ("⭐ Guardada") | Debería | 2 | El mensaje original cambia después de la ejecución |
| RF-FBK-04 | Comando `/guardadas` que lista las ofertas guardadas | Podría | 3 | El comando devuelve la lista en la siguiente ejecución |

---

## 7. Datos, ejecución e infraestructura

*Secciones 8 y 9 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-DAT-01 | Base SQLite con las tablas `ofertas` y `ejecuciones` del modelo de datos | Debe | 1 | El esquema se crea automáticamente si no existe |
| RF-DAT-02 | Migraciones simples y versionadas del esquema | Debería | 2 | Agregar una columna no borra los datos existentes |
| RF-DAT-03 | Limpieza de ofertas 🔴 con más de 90 días | Debería | 3 | La base no crece sin límite |
| RF-EJE-01 | Se puede ejecutar en local con un solo comando: `python -m radar` | Debe | 1 | El comando completa un ciclo entero |
| RF-EJE-02 | Modo de prueba `--dry-run`: hace todo excepto enviar a Telegram y escribir en la base | Debe | 1 | Muestra en consola los mensajes que se enviarían |
| RF-EJE-03 | Flujo de GitHub Actions con `cron` cada 12 horas, más ejecución manual (`workflow_dispatch`) | Debe | 2 | El historial de Actions muestra ejecuciones automáticas |
| RF-EJE-04 | Solo una ejecución diaria envía el resumen; la otra procesa las pulsaciones y recolecta | Debe | 2 | Llega un solo resumen por día |
| RF-EJE-05 | La base se guarda en la rama `datos` mediante un commit al final de cada ejecución | Debe | 2 | La base conserva el historial entre ejecuciones |
| RF-EJE-06 | Las horas se manejan en UTC y se muestran en la zona horaria configurada | Debería | 2 | El resumen llega a la hora local configurada |

---

## 8. Manejo de errores

*Sección 10 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-ERR-01 | Cada recolector corre aislado: si uno falla, los demás siguen | Debe | 1 | Si se simula la caída de una fuente, las demás igual se notifican |
| RF-ERR-02 | Cada fuente registra su estado en `ejecuciones` | Debe | 1 | La tabla distingue "error" de "0 ofertas" |
| RF-ERR-03 | Aviso específico en Telegram si una fuente falla tres veces seguidas | Debe | 2 | Al tercer fallo simulado llega el aviso |
| RF-ERR-04 | Aviso inmediato si expira o se revoca el token de Gmail | Debe | 2 | Con un token inválido llega "Renová el acceso a Gmail" |
| RF-ERR-05 | Reintentos con espera creciente (tres intentos) ante errores de red | Debería | 2 | Un error temporal no marca la fuente como caída |
| RF-ERR-06 | Si un correo no se puede analizar, se guarda su ID y se sigue con el resto | Debe | 1 | Un correo con un formato nuevo no detiene la ejecución |

---

## 9. Métricas

*Sección 11 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-MET-01 | Script `python -m radar.metricas` que calcula las seis métricas de la sección 11 del diseño | Debe | 3 | Genera una tabla en Markdown lista para pegar en el README |
| RF-MET-02 | Desglose por país y por fuente | Debería | 3 | La tabla muestra cuántas ofertas 🟢 aporta cada país |
| RF-MET-03 | Página de resultados estática generada desde la base (GitHub Pages) | Podría | 3 | La página se actualiza en cada ejecución |

---

## 10. Requisitos no funcionales

| ID | Requisito | Criterio de aceptación |
|---|---|---|
| RNF-SEG-01 | Ningún secreto en el repositorio: el token, el `chat_id`, las credenciales OAuth y las claves se guardan en GitHub Secrets o en un `.env` local ignorado por git | Un escaneo con `gitleaks` no encuentra secretos |
| RNF-SEG-02 | Permiso de Gmail mínimo (`gmail.readonly`) y cuenta dedicada | Lo confirma la pantalla de consentimiento OAuth |
| RNF-SEG-03 | La base y los *fixtures* no contienen datos personales: se quitan los nombres de reclutadores y los correos de contacto | Revisión de `tests/fixtures/` antes de cada commit |
| RNF-LEG-01 | Se respetan las condiciones de uso de cada fuente (ver RF-REC-07) | Cada fuente está documentada en el README con su vía de acceso |
| RNF-COS-01 | Costo mensual de cero, usando solo planes gratuitos | Ningún servicio requiere tarjeta para funcionar |
| RNF-CAL-01 | Código con *type hints*, formateado con `ruff` y con pruebas en `pytest` | El flujo de integración continua pasa en cada *pull request* |
| RNF-CAL-02 | Cobertura de pruebas del clasificador y de los analizadores de correo de al menos el 80 % | Lo muestra el informe de `pytest --cov` |
| RNF-REN-01 | Un ciclo completo tarda menos de 5 minutos | Lo muestra la duración en GitHub Actions |
| RNF-MAN-01 | Agregar una fuente nueva requiere un único archivo nuevo en `collectors/` y una línea en `config.yaml` | Se demuestra al agregar la segunda fuente |

---

## 11. Presentación en el portafolio

*Sección 15 del diseño.*

| ID | Requisito | Prioridad | Etapa | Criterio de aceptación |
|---|---|---|---|---|
| RF-POR-01 | README como caso de estudio, con las seis partes de la sección 15 del diseño | Debe | 3 | Lo revisa una persona ajena al proyecto y entiende el problema y la solución en dos minutos |
| RF-POR-02 | GIF o video corto de un aviso real llegando a Telegram | Debe | 3 | Está incrustado en el README |
| RF-POR-03 | Sección de decisiones de criterio (reglas antes que IA, correo en lugar de extracción de portales, términos regionales del rol) | Debe | 3 | Está en el README |
| RF-POR-04 | Resultados medidos con cifras reales de al menos cuatro semanas de uso | Debe | 3 | La tabla de RF-MET-01 está en el README con su fecha |
| RF-POR-05 | Versión en inglés del README | Podría | 3 | `README.en.md` existe y está enlazado |

---

## 12. Resumen por etapa

| Etapa | Requisitos con prioridad "Debe" |
|---|---|
| **0 · Validación** | RP-01, RP-05, RP-06, RF-VAL-01 a RF-VAL-04 |
| **1 · Prototipo** | RP-02 a RP-04, RP-07, RP-08; CFG-01 a 04; REC-01 a 04 y 07; NOR-01 a 05 y 07; DED-03; CLA-01 a 07; NOT-01 y 04; DAT-01; EJE-01 y 02; ERR-01, 02 y 06 |
| **2 · Versión útil** | DED-01; NOT-02, 03 y 05; FBK-01 y 02; EJE-03 a 05; ERR-03 y 04 |
| **3 · Portafolio** | MET-01; POR-01 a 04 |

Los requisitos no funcionales `RNF-SEG` y `RNF-LEG` se aplican en todas las etapas.

---

## 13. Pendientes que afectan a los requisitos

1. ~~País de residencia~~ **Resuelto:** el país base es Argentina (RF-CFG-03).
2. **Zona horaria y hora del resumen** (RF-EJE-06): se toma la zona horaria donde está físicamente el usuario, que no tiene por qué ser la del país base.
3. **Puerto Rico** (RF-CFG-02): queda excluido de forma provisional, junto con Estados Unidos.
