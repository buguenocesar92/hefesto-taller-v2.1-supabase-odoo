# Hefesto Taller v2.1 — Traspaso y despliegue

**Para usar Supabase, sigue primero SUPABASE.md y compose.supabase.yaml. Los comandos sin ese archivo en esta guía corresponden a la alternativa SQLite.**

## Qué se entrega
1. Aplicación Sites existente con persistencia y acceso privado.
2. Misma interfaz y reglas de negocio ejecutables fuera de Sites: React + Node 24 + SQLite, Docker, autenticación propia de administrador.
3. Exportación JSON v2 íntegra, validador e importador inicial de instancia propia.
4. Conversor offline a CSV para Odoo.
5. Módulo `odoo/hefesto_taller` dirigido a Odoo 18 Community, con órdenes, conceptos, pagos históricos e importador por respaldo.

La ruta independiente no requiere una cuenta ChatGPT, API de OpenAI, Odoo ni WordPress. El acceso es de un administrador por instancia; no es todavía SaaS multiempresa con usuarios internos y permisos por rol.

## A. Exportar desde el sitio
En Portabilidad, pulsa Exportar JSON v2. Este respaldo incluye los registros actualmente guardados, las fotos y los identificadores. El ZIP de código no contiene los datos del taller en producción: los datos se exportan desde la aplicación con tu sesión.

## B. Desplegar en Coolify o Docker Compose
1. Sube este código a un repositorio propio privado o a tu VPS.
2. Copia `.env.example` como `.env` y establece `ADMIN_PASSWORD` (aleatoria de al menos 16 caracteres), `PUBLIC_ORIGIN` (URL exacta HTTPS) y `COOKIE_SECURE=true`.
3. Ejecuta desde la raíz:

```bash
docker compose up -d --build
```

4. Apunta tu proxy HTTPS al servicio `taller:3000` en la red de Coolify, o a `127.0.0.1:3080` en el host. El puerto del Compose se publica solo en loopback; no se expone directamente a Internet.
5. En Coolify: elige Docker Compose, usa `compose.yaml`, define variables y asigna dominio al servicio. Si Coolify gestiona el puerto, elimina el bloque `ports` de su configuración y conserva el puerto interno 3000.
6. Entra a tu dominio y utiliza la contraseña configurada. Las sesiones vencen en 12 horas. Cerrar sesión está disponible en Configuración.

El volumen `taller-data` conserva SQLite entre despliegues. No ejecutes `docker compose down -v` salvo que quieras eliminarlo.

### Prueba local
Usa `PUBLIC_ORIGIN=http://localhost:3080` y `COOKIE_SECURE=false`. No uses esa configuración con dominio público.

### Importación inicial sin sobrescribir registros
Primero valida el archivo. Luego cópialo al contenedor y ejecuta el importador:

```bash
docker compose cp ./hefesto-taller-v2.json taller:/data/import.json
docker compose exec taller node portable/tools/transfer.mjs validate /data/import.json
docker compose exec taller node portable/tools/transfer.mjs import /data/import.json
```

El importador rechaza una instancia que ya contiene clientes, inventario, órdenes, proveedores o sesiones de caja. Conserva los ID originales. Importa antes de empezar a trabajar en la nueva instancia. El respaldo original sigue intacto.

### Respaldo posterior

```bash
docker compose exec taller node portable/tools/transfer.mjs export /data/backup.json
docker compose cp taller:/data/backup.json ./hefesto-respaldo.json
```

Guarda copias fuera del VPS, cifradas y con acceso restringido. Para un respaldo físico de SQLite, detén el contenedor y copia el volumen completo, incluyendo archivos WAL/SHM si existen; no copies solo el archivo principal mientras está escribiendo.

## C. Migrar a Odoo — módulo incluido
Objetivo: Odoo 18 Community. La sintaxis Python y XML se revisó; no se realizó instalación dentro de una instancia Odoo. Versiones distintas requieren revisar las vistas y APIs de modelos. No se debe presentar como migración ya realizada.

1. Duplica tu base Odoo o crea una base de pruebas con moneda CLP.
2. Copia `odoo/hefesto_taller` a `custom_addons`, actualiza la lista de aplicaciones e instala Hefesto Taller.
3. Como administrador, abre Hefesto Taller → Importar respaldo y carga JSON v2.
4. Mantén activado Solo validar y contar. Ejecuta, revisa recuentos y errores.
5. Desactiva Solo validar y contar y ejecuta la importación.
6. Por defecto, las órdenes existentes no se actualizan. La opción Actualizar órdenes previamente importadas reemplaza sus conceptos y pagos históricos por el respaldo; úsala solo tras revisar la versión del archivo.
7. Compara clientes, productos, órdenes, totales, pagos y muestras de equipos con el sitio original.

### Alcance del módulo
- Clientes y proveedores se crean como `res.partner` con identificadores externos por empresa.
- Repuestos se crean en `product.template` sin alterar existencias.
- Las órdenes viven en modelos `hefesto.taller.*`. Se importan datos de recepción, diagnóstico, estado, técnico, conceptos y pagos históricos.
- Se preserva el JSON completo de cada orden y un respaldo completo adjunto, incluidos los datos que todavía no se convierten a modelos nativos: fotografías, compras, caja, garantías, tareas, auditoría.
- No se generan `account.move`, facturas, boletas, conciliaciones bancarias ni movimientos físicos de stock. Los pagos importados son historia, no contabilidad.
- La interfaz Odoo del módulo no replica todas las automatizaciones de la aplicación. Es una base funcional de recepción de datos y gestión de órdenes, pendiente de pruebas y adaptación al flujo Odoo elegido.
- Al replicar datos personales, define permisos, conservación y respaldos en destino.

## D. Alternativa CSV sin instalar módulo

```bash
python3 migration/prepare_odoo.py hefesto-taller-v2.json salida-odoo
```

Los archivos 01–03 preparan contactos y productos; asigna las columnas a los campos de Odoo y usa Probar antes de importar. Los archivos 04–06 son para conciliación, no para importación contable directa. El convertidor no se conecta a Internet.

No mezcles la ruta CSV y el importador del módulo para la misma base sin acordar los identificadores: usan espacios de ID diferentes (el módulo los separa además por empresa). Elegir una ruta evita duplicados.

Para una importación nativa a Ventas, exporta primero una plantilla de `sale.order` desde tu versión de Odoo y resuelve producto/variante, lista de precios, moneda e impuestos. No se adivinan esos IDs. Los presupuestos históricos no se confirman automáticamente.

Referencia oficial: https://www.odoo.com/documentation/19.0/applications/essentials/export_import_data.html

## E. Arquitectura para otra plataforma Hefesto
- `lib/workshop.ts`: acciones y reglas de negocio, independientes de Sites.
- `lib/workshop-v1.ts`: reglas originales utilizadas por la capa v2.
- `lib/transfer.ts`: validación de respaldos.
- `app/api/workshop/route.ts`: adaptador D1 / identidad Sites.
- `portable/server.mjs`: adaptador SQLite / autenticación propia.
- `app/page.tsx` y `app/advanced.tsx`: interfaz compartida.

Se puede reemplazar el adaptador por Laravel/PostgreSQL o una API Odoo manteniendo el contrato de `docs/API.md`. La interfaz actual es React; no se ha convertido a Nuxt. La base actual guarda un documento por taller con control optimista, no tablas PostgreSQL normalizadas. Para mayor volumen, mueve fotografías a objetos y separa entidades en tablas, conservando IDs y contrato.

## Verificaciones realizadas y pendientes
Realizadas: compilación de ambas interfaces, tipos TypeScript, reglas transaccionales, garantías, stock y compras, sesiones, CSRF, conflicto de revisiones, validación de exportación/importación; comprobación estática de addon.
Pendientes: instalación real del contenedor en tu VPS, instalación Odoo y prueba visual de navegador. El entorno de esta entrega no tiene Docker ni navegador de control disponibles.
