# Hefesto Taller + Supabase

Este paquete usa Supabase PostgreSQL para datos y sesiones de la versión desplegada en Docker/Coolify. La interfaz no recibe claves de Supabase. El servidor usa Data API/PostgREST con clave secreta, mientras el navegador utiliza la API autenticada de Hefesto.

## 1. Preparar tu proyecto
Crea o elige un proyecto Supabase. En SQL Editor ejecuta el contenido de:

`supabase/migrations/202610130001_hefesto_taller.sql`

Crea dos tablas dedicadas: `hefesto_taller_states` (estado del taller y revisión) y `hefesto_taller_sessions` (hashes de sesiones y vencimiento). RLS queda habilitado y se revoca el acceso a los roles públicos anon/authenticated. Solo el servidor con service_role accede a estas tablas. No cambies tablas ajenas al proyecto.

Mantén habilitada la Data API y expuesto el esquema `public`. Las tablas siguen protegidas por los permisos y RLS indicados. La clave secreta tiene privilegios de servidor: nunca ponerla en variables VITE_, NEXT_PUBLIC_ ni en código frontend.

## 2. Variables del servicio en Coolify

```dotenv
SUPABASE_URL=https://TU-PROYECTO.supabase.co
SUPABASE_SECRET_KEY=TU_CLAVE_SECRETA
WORKSHOP_ID=main
ADMIN_PASSWORD=UNA_CONTRASENA_LARGA_Y_ALEATORIA
PUBLIC_ORIGIN=https://taller.tu-dominio.cl
COOKIE_SECURE=true
```

Usa una clave secreta `sb_secret_...`. El adaptador admite alternativamente la clave legacy `service_role` en SUPABASE_SECRET_KEY. No sirve la clave publishable/anon. Obtén los valores en la configuración/API Keys de tu proyecto y guárdalos como secretos en Coolify, no en Git.

## 3. Desplegar
Selecciona `compose.supabase.yaml` como archivo Compose. El servicio usa el Dockerfile incluido, puerto interno 3000 y STORAGE_BACKEND=supabase. La base y las sesiones se conservan en Supabase; no dependen del disco del contenedor.

Desde un VPS con Docker:

```bash
cp .env.example .env
# Completar .env con los valores anteriores.
docker compose -f compose.supabase.yaml up -d --build
```

Conecta el proxy HTTPS a `taller:3000` en la red interna, o `127.0.0.1:3080` desde el host. PUBLIC_ORIGIN debe coincidir exactamente con el origen que visita el usuario.

El servidor se niega a iniciar si faltan credenciales, tablas o permisos. No sustituye Supabase por SQLite silenciosamente. Para SQLite se conserva `compose.yaml`, como alternativa independiente.

## 4. Migrar los datos actuales
Descarga Portabilidad → Exportar JSON v2 desde la aplicación actual. El ZIP contiene código, no una copia de tus datos en Sites.

```bash
docker compose -f compose.supabase.yaml cp ./hefesto-taller-v2.json taller:/data/import.json
docker compose -f compose.supabase.yaml exec taller node portable/tools/transfer.mjs validate /data/import.json
docker compose -f compose.supabase.yaml exec taller node portable/tools/transfer.mjs import /data/import.json
```

La instancia recién iniciada está vacía y puede recibir el respaldo. Si ya registra operaciones, el importador se detiene. Para otro destino limpio, utiliza otro WORKSHOP_ID; no cambies el identificador de una instancia activa sin planificar qué datos deben aparecer. El guardado usa comparación de revision para evitar sobrescribir cambios simultáneos.

## 5. Exportar desde Supabase

```bash
docker compose -f compose.supabase.yaml exec taller node portable/tools/transfer.mjs export /data/respaldo.json
docker compose -f compose.supabase.yaml cp taller:/data/respaldo.json ./respaldo-hefesto.json
```

Además de esta exportación, revisa las opciones de backup disponibles en tu plan Supabase. Conserva copias externas protegidas. Los respaldos JSON siguen siendo compatibles con el módulo Odoo y el convertidor CSV incluidos.

## Alcance exacto
- Supabase se usa como base PostgreSQL mediante JSONB y como almacén de sesiones de Hefesto.
- La autenticación sigue siendo la del administrador del servidor portable. No se implementan Supabase Auth, inicio con Google ni usuarios/roles adicionales.
- Las fotografías permanecen dentro del respaldo JSON, con los límites de la aplicación. No se configura Supabase Storage en esta entrega.
- Los datos se guardan como un documento por WORKSHOP_ID; no es una migración a tablas relacionales por entidad. Para gran volumen/concurrencia conviene normalizar el esquema y sacar las fotos a Storage.
- Puede usarse con Supabase Cloud o una instancia propia compatible. HTTPS es obligatorio salvo hosts internos permitidos para pruebas/despliegue propio.
- La clave de servidor permite acceder a todas las instancias del proyecto: WORKSHOP_ID separa datos operativamente, no implementa por sí solo un SaaS multiinquilino seguro para clientes no confiables.
- Las pruebas utilizan un adaptador HTTP simulado, además de pruebas reales de la API local con SQLite. No se creó ni conectó un proyecto Supabase real y no se ejecutó Docker en este entorno.
- El sitio privado actual sigue usando D1 de Sites. El traslado a Supabase ocurre cuando despliegas esta distribución y cargas el respaldo.

Documentación de referencia:
- https://supabase.com/docs/guides/getting-started/api-keys
- https://supabase.com/docs/guides/database/postgres/row-level-security
