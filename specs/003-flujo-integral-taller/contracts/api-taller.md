# Contrato de API — Flujo Integral del Taller (`app/api/taller.py`)

Todas las operaciones exigen encabezado `Authorization: Bearer <jwt>` (`RNF-02`) y responden errores con el esquema uniforme `{codigo, mensaje, detalle}`.

## 1. Consultas y Seguimiento Paginado

| Método y Ruta | Etiqueta OpenAPI | Rol permitido | Propósito y Reglas |
|---------------|------------------|---------------|--------------------|
| `GET /ordenes` | `CU-01 · GUI-01` | Cualquier sesión activa | Lista paginada (`estado`, `q`, `page`, `limit`). Si es `TECNICO`, filtra por `usuario.tecnico_id` (`RN-03`, `RNF-02`). |
| `GET /ordenes/resumen` | `CU-01 · GUI-01` | Cualquier sesión activa | KPIs de órdenes por estado, técnicos disponibles y repuestos con `stock_libre <= 2` (`RNF-02`). |
| `GET /tecnicos/resumen` | `CU-01 · GUI-01` | Cualquier sesión activa | Disponibilidad y cola actual de todos los técnicos (`RN-03`, `RNF-02`). |
| `GET /clientes` | `CU-05 · GUI-01` | Solo `RECEPCIONISTA` | Directorio paginado de clientes con sus equipos (`RN-01`, `RNF-02`). |
| `GET /ordenes/{codigo}` | `CU-01 · GUI-01` | Cualquier sesión activa | Ficha integral de la orden; `403 ORDEN_NO_ASIGNADA` si un `TECNICO` consulta orden ajena (`RN-03`). |
| `GET /repuestos` | `CU-07 · GUI-03` | Cualquier sesión activa | Catálogo paginado con `stock_disponible`, `stock_reservado` y `stock_libre` (`RN-04`, `RNF-02`). |

## 2. Operaciones Transaccionales e Idempotentes

### `POST /ordenes/{codigo}/diagnostico` — `CU-02 · GUI-03`
- **Rol**: `TECNICO` asignado a la orden (`403 ROL_NO_PERMITIDO` o `403 ORDEN_NO_ASIGNADA`).
- **Precondición**: `orden.estado == "RECEPCIONADO"` (`409 ESTADO_ORDEN_INVALIDO`).
- **Entrada (`DiagnosticoIn`)**: `{id_op, informe_tecnico, costo_mano_obra, repuestos: [{repuesto_id, cantidad}]}`.
- **Respuestas**:
  - `201 Created` (`EmitirDiagnosticoOut`, `reintento: false`): reserva atómica aplicada y orden en `PRESUPUESTADO`.
  - `200 OK` (`reintento: true`): reenvío con el mismo `id_op` y mismos datos (`RN-10`).
  - `409 Conflict` (`codigo: "E02"`): `stock_libre < cantidad` en algún ítem; cero cambios persistidos (`RN-04`, `RNF-01`).

### `POST /ordenes/{codigo}/decision` — `CU-03 · GUI-04`
- **Rol**: `RECEPCIONISTA`.
- **Precondición**: `orden.estado == "PRESUPUESTADO"`.
- **Entrada (`DecisionIn`)**: `{id_op, decision: "APROBADO"|"RECHAZADO", canal: "WHATSAPP"|"LLAMADA"|"PRESENCIAL", evidencia}`.
- **Respuestas**: `200 OK` (`RegistrarDecisionOut`); si `RECHAZADO`, libera reservas activas inmediatamente (`RN-05`, `RN-06`, `RN-10`).

### `POST /ordenes/{codigo}/finalizar` — `CU-08 · GUI-05`
- **Rol**: `TECNICO` asignado a la orden.
- **Precondición**: `orden.estado == "APROBADO"` y `prueba_conforme == true` (`422 PRUEBA_NO_CONFORME` si es `false`, `RN-07`).
- **Entrada (`FinalizarReparacionIn`)**: `{id_op, trabajo_realizado, prueba_conforme, resultado_prueba}`.
- **Respuestas**: `200 OK` (`FinalizarReparacionOut`); consume definitivamente el stock reservado, reduce en 1 la cola del técnico y pasa a `LISTO`.

### `POST /ordenes/{codigo}/liquidar` — `CU-04 · GUI-06`
- **Rol**: `RECEPCIONISTA`.
- **Precondición**: `orden.estado` en `("LISTO", "RECHAZADO")` (`409 ESTADO_ORDEN_INVALIDO`).
- **Entrada (`LiquidarOrdenIn`)**: `{id_op, metodo_pago: "EFECTIVO"|"TARJETA"|"TRANSFERENCIA", monto_recibido, conformidad_entrega}`.
- **Validaciones**: `conformidad_entrega == true` (`422 CONFORMIDAD_REQUERIDA`); `monto_recibido` exacto igual a `total_presupuesto` (en `LISTO`, `RN-08`) o a `costo_revision` (en `RECHAZADO`, `RN-11`) (`422 MONTO_INCOMPLETO`).
- **Respuestas**: `201 Created` (`LiquidarOrdenOut` con `comprobante.numero = "CP-AAAA-NNNN"` y `orden.estado = "ENTREGADO"`, `RN-09`) o `200 OK` en reintento idempotente (`RN-10`).
