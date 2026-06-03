### Clientes

GET /clientes - Listar todos os clientes
GET /clientes/{id} - Obter detalhes de um cliente específico
POST /clientes - Crear un nuevo cliente
PUT /clientes/{id} - Actualizar un cliente existente
DELETE /clientes/{id} - Eliminar un cliente
GET /clientes/{id}/pedidos - Listar todos los pedidos de un cliente específico
GET /clientes/{id}/pedidos/{pedido_id} - Obtener detalles de un pedido específico de un cliente

### Transaciones
GET /tansacciones - Listar todas las transacciones
GET /transacciones/{id} - Obtener detalles de una transacción específica
POST /transacciones - Crear una nueva transacción

### Reportes
GET /reportes/ventas - Obtener un reporte de ventas
GET /reportes/clientes - Obtener un reporte de clientes activos e inactivos
GET /reportes/portafolio - Obtener un reporte del portafolio de productos

### Portfolio
GET /portfolio - Listar todos los productos en el portafolio
GET /portfolio/{id} - Obtener detalles de una posición específica en el portafolio
POST /portfolio - Agregar una nueva posición al portafolio

### Webhooks
POST /webhooks/transacciones - Recibir notificaciones de transacciones desde sistemas externos
POST /webhooks/portfolio - Recibir actualizaciones de posiciones en el portafolio desde sistemas externos

### Auditoría
GET /auditoria - Listar todas las actividades auditadas
GET /auditoria/{id} - Obtener detalles de una actividad auditada específica
