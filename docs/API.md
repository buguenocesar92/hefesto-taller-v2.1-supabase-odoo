# API Hefesto Taller v2

Base: mismo origen de la aplicación. JSON UTF-8; montos en pesos chilenos, precios netos y cálculo IVA 19%. Las escrituras son acciones validadas en servidor. No se aceptan escrituras de estado arbitrarias.

## Autenticación
Sites: identidad autenticada de la plataforma y aislamiento por propietario.
Instancia propia: `POST /api/login` con `{ "password": "..." }`, cookie HttpOnly/SameSite=Strict de 12 horas; `POST /api/logout`. HTTPS y Secure por defecto. Las escrituras requieren `Origin` igual a `PUBLIC_ORIGIN` en el servidor propio. No guardar credenciales en código.

## GET /api/workshop
Respuesta: `{ "state": { "schemaVersion": 2, ... }, "revision": 12 }`.
Incluye customers, orders, inventory, technicians, appointments, settings, suppliers, purchases, movements, expenses, cashSessions, claims, services, audit. No utiliza localStorage para registros operativos.

## POST /api/workshop
Solicitud: `{ "revision": 12, "action": { "type": "customer", "name": "Cliente", "email": "", "phone": "" } }`.
Respuesta: estado actualizado y revision 13. Un conflicto devuelve 409; recargar y revisar antes de repetir. Validación 400, falta de sesión 401, origen inválido 403, límite de cuerpo 413. No reintentar ciegamente pagos o recepciones después de una pérdida de conexión: primero consultar el estado.

Acciones y campos principales:

| Acción | Campos |
|---|---|
| customer / updateCustomer | name, email, phone, rut, notes; id al editar |
| order | customerId, device, deviceType, issue, due, technician, priority, serial, accessories |
| updateOrder | id, device, technician, due, serial, accessories, priority |
| status | id, status (siguiente etapa) |
| diagnosis / note | id, text |
| line | id, description, qty, price; o productId, qty |
| removeLine | id, lineId |
| approve | id, reference |
| payment | id, amount, method |
| check | id, label, value |
| photo | id, name, data (data URL jpeg/png/webp, <450000 caracteres) |
| appointment | title, customer, date, time, duration, technician |
| cancelAppointment | id |
| product | name, sku, price, stock, min |
| stock | id, delta (entero), reason |
| supplier | name, rut, email, phone, notes |
| purchase | supplierId, reference, lines: [{productId, qty, cost}] |
| receivePurchase | id, reference, lines: [{id (línea), qty}] |
| cashOpen / cashClose | amount; notes al cerrar |
| expense | description, category, amount, method, reference |
| task | id (orden), title |
| toggleTask | id, taskId, done |
| time | id, description, minutes |
| claim | id (orden entregada), reason |
| closeClaim | id (caso), resolution |
| cancelOrder | id, reason; solo sin pagos ni aprobación |
| service | name, category, price, minutes |
| technician | name |
| settings | name, email, phone, address, warranty |

La lógica de negocio está en `lib/workshop.ts` y sus pruebas. La cancelación restaura repuestos una vez. Las recepciones admiten parciales y no superan cantidades pendientes. La garantía toma fecha efectiva de entrega y congela el plazo configurado al entregar. Las órdenes antiguas sin esa fecha no inventan un plazo.

## Exportación
Formato `{ "format": "hefesto-taller", "version": 2, "exportedAt": "ISO-8601", "state": {...} }`. Los IDs son claves de migración; no regenerarlos. Fotos y datos personales forman parte del respaldo. El validador admite el respaldo sin envoltorio de la v1.
