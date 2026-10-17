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
