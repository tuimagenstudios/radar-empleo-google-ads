# Guía · Alertas por correo (Argentina)

**Objetivo:** que Bumeran y ZonaJobs te manden alertas diarias a **tuimagenstudio@gmail.com** y que el Radar las lea solo.
**Tiempo:** unos 20 minutos, una sola vez.
**Requisitos que cubre:** RP-06, RP-07, RP-08 y RF-REC-02.

> Desde Rusia, Bumeran y ZonaJobs abren bien. Computrabajo e Indeed Argentina rechazaron la conexión automática; probalos en el navegador y, si te funcionan, sumá alertas ahí también.

---

## Parte A · Crear las alertas (en tus portales)

En **Bumeran** (bumeran.com.ar) y en **ZonaJobs** (zonajobs.com.ar):

1. Iniciá sesión o registrate con **tuimagenstudio@gmail.com**.
2. Buscá cada uno de estos términos, con la ubicación **Argentina**:
   - `Google Ads`
   - `SEM`
   - `trafficker digital`
   - `marketing digital junior`
3. En los resultados, tocá **"Crear alerta"** (o "Recibir avisos por email") y elegí la frecuencia **diaria**.

Cuando lleguen los primeros correos de alerta, avisale a Claude: con esos correos reales se programa el analizador de cada portal (RF-REC-03).

## Parte B · Darle al Radar permiso de lectura (Google Cloud)

El Radar pide permiso de **solo lectura** (`gmail.readonly`), y únicamente busca correos de los remitentes de los portales. No puede borrar, enviar ni modificar nada.

1. Entrá a **console.cloud.google.com** con tuimagenstudio@gmail.com y creá un proyecto llamado `Radar Empleo`.
2. **APIs y servicios → Biblioteca →** buscá **Gmail API** y tocá **Habilitar**.
3. **Google Auth Platform → Branding (marca):**
   - Nombre de la app: `Radar Empleo`
   - Correo de asistencia: tuimagenstudio@gmail.com
   - Público: **Externo**
4. **Público (Audience):** tocá **"Publicar app"** para pasarla a **En producción**.
   > ⚠ Si la dejás en "Prueba", Google vence el permiso cada 7 días. Para uso personal no hace falta verificar la app: al autorizar vas a ver el aviso "Google no verificó esta app". Tocá **Configuración avanzada → Ir a Radar Empleo**.
5. **Clientes → Crear cliente →** tipo **Aplicación de escritorio**, nombre `Radar`.
6. Copiá el **ID de cliente** y el **Secreto del cliente** en el `.env`:
   ```
   GMAIL_CLIENT_ID=...
   GMAIL_CLIENT_SECRET=...
   ```
7. En la carpeta del proyecto, ejecutá:
   ```bash
   .venv/Scripts/python -m radar.gmail_auth
   ```
   Se abre el navegador: elegí tuimagenstudio@gmail.com y aceptá el permiso de lectura. El programa guarda solo `GMAIL_REFRESH_TOKEN` en el `.env`, sin mostrarlo.
8. Avisale a Claude: sube los tres valores a GitHub Secrets con `gh secret set -f .env` y prueba la lectura.

## Si algo falla

| Mensaje | Qué hacer |
|---|---|
| "Gmail rechazó el acceso" | El permiso venció o se revocó: repetí el paso 7. |
| "Sin analizador para …" | Llegó un correo de un portal que todavía no tiene analizador: pasáselo a Claude. |
