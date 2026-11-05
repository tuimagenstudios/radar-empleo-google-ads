# Política de privacidad · Radar de Empleo

**Última actualización:** 5 de noviembre de 2026

El Radar de Empleo es una herramienta **personal** de Tuimagen Studios. La usa una sola persona, la autora, para recibir alertas de ofertas de empleo. No es un servicio abierto al público.

## Qué datos usa

- **Gmail (solo lectura, `gmail.readonly`).** El Radar lee únicamente los correos de alertas de empleo que envían los portales configurados (por ejemplo, Bumeran). No lee el resto de la bandeja, no envía correos, no los borra ni los modifica.
- **De cada alerta** extrae solo los datos públicos de la oferta: título, empresa, ubicación, enlace y descripción.

## Dónde se guardan

- Las ofertas se guardan en una base SQLite dentro del repositorio del proyecto (rama `datos`). No se guardan correos completos ni datos personales.
- Las credenciales de acceso se guardan como *secrets* cifrados de GitHub y nunca se publican.

## Con quién se comparten

Con nadie. El único destino de la información es el chat privado de Telegram de la autora.

## Cómo revocar el acceso

Desde [myaccount.google.com/permissions](https://myaccount.google.com/permissions) se puede quitar el permiso de "Radar Empleo" en cualquier momento.

## Contacto

Tuimagen Studios · [github.com/tuimagenstudios/radar-empleo-google-ads](https://github.com/tuimagenstudios/radar-empleo-google-ads)
