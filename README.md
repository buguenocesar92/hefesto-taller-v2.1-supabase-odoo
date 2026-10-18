# Hefesto Taller v2.1 — Supabase

Gestión de talleres con recepción, diagnósticos, presupuestos, repuestos, pagos, fotografías, clientes, agenda, tareas, tiempos, garantías, compras parciales, proveedores, trazabilidad, catálogo y control de caja.

## Abrir o instalar
- **Supabase + Coolify: empieza por [docs/SUPABASE.md](docs/SUPABASE.md) y usa compose.supabase.yaml.**
- Sitio privado: https://hefesto-taller.cbm3lla.chatgpt.site
- Instalación independiente con Docker/Coolify y traspaso: [docs/TRASPASO.md](docs/TRASPASO.md).
- API portable: [docs/API.md](docs/API.md).
- Módulo Odoo 18 de recepción de datos: `odoo/hefesto_taller`.
- Preparación CSV sin conexión: `migration/prepare_odoo.py`.

## Verificar
```
node --test tests/*.test.mjs
node node_modules/typescript/bin/tsc --noEmit
node node_modules/vite/bin/vite.js build --config portable/vite.config.mts
```
Para Sites se conservan su adaptador de identidad, D1 y helpers de publicación. La distribución portable tiene su propio package.json, Dockerfile y adaptador SQLite.

## Límites explícitos
No hay conexión activa a Odoo, WhatsApp, correo, SII ni pasarelas. Los pagos y autorizaciones se registran manualmente. El portal del cliente sigue siendo una vista previa privada. Los técnicos son asignables, no cuentas independientes. Los datos de ejemplo permanecen en Sites; la instancia portable comienza vacía. No se ha verificado instalación real en Odoo ni ejecutado Docker en este entorno. Consulta TRASPASO para no confundir el paquete preparado con una migración ya ejecutada.

## Despliegue en Coolify (MVP Hefesto)
Coolify usa el `compose.supabase.yaml` con build pack Docker Compose. El contrato limita a publicar puertos (queda solo `expose: "3000"`), quitar nombres fijos de proyecto, red y volumen, y mantener la red interna por defecto.

Variables de entorno que Coolify debe inyectar:

- `SUPABASE_URL` — interna (`http://supabase-kong:8000`) si comparte stack, o pública (`https://<proyecto>.supabase.co`).
- `SUPABASE_SECRET_KEY` — `sb_secret_…` o service role legacy; nunca `anon` ni `sb_publishable_…`.
- `ADMIN_PASSWORD` — al menos 16 caracteres aleatorios.
- `PUBLIC_ORIGIN` — el dominio HTTPS que Coolify publica para esta app.
- `WORKSHOP_ID` (opcional, valor por defecto `main`).
- `COOKIE_SECURE` (opcional, `true`).

Pasos la primera vez:

1. Aplicar la migración `supabase/migrations/202610130001_hefesto_taller.sql` desde el SQL Editor de Supabase como propietario del proyecto, antes de levantar el servicio. La versión coincide con la de otras apps del MVP Hefesto, por eso se aplica a mano y no con `supabase db push` sobre una base compartida. Las tablas ya se llaman `hefesto_taller_states` y `hefesto_taller_sessions` (el esquema antiguo `hefesto_workshops`/`hefesto_sessions` quedó obsoleto).
2. Definir las variables de entorno en Coolify y arrancar el servicio. El healthcheck interno es `GET /health`.
3. Validar el contrato del compose con `bash scripts/coolify-check.sh` (incluido en este repo) antes de mergear cualquier cambio al `compose.supabase.yaml`.
