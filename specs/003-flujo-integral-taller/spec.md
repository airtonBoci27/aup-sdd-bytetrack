# Feature Specification: Flujo integral de laboratorio, decisión y liquidación (Iteraciones C2, C3 y C4)

**Feature Branch**: `003-flujo-integral-taller`

**Created**: 2026-11-20

**Status**: Implemented

**Input**: User description: "Completa las iteraciones C2, C3 y C4 de Construcción de ByteTrack a partir de docs/aup/caso.md y docs/aup/requerimientos.md: CU-07 Consultar stock de repuestos, CU-02 Emitir diagnóstico y presupuesto (GUI-03, reserva atómica RN-04/RNF-01 y alerta E02), CU-03 Registrar decisión de presupuesto (GUI-04, RN-05 y RN-06), CU-08 Finalizar reparación (GUI-05, RN-07) y CU-04 Liquidar orden y entregar equipo (GUI-06, RN-08, RN-09 y devolución RN-11), aplicando acceso por rol y bandeja asignada (RNF-02, RN-03), idempotencia (RN-10, RNF-04) y paneles de seguimiento paginado."

**Fuente de verdad**: `docs/aup/requerimientos.md` (`RF-01` a `RF-06`, `RNF-01`, `RNF-02`, `RNF-04`) y `docs/aup/caso.md` (narrativas `CU-02`, `CU-03`, `CU-04`, `CU-07`, `CU-08`, prototipos `GUI-03` a `GUI-06`, diseño arquitectónico §3.6, plan de iteraciones §4.1 y diagramas de clases §4.2).

## Contexto

Con la iteración C1 completada (`001-recepcion-orden-servicio` y `002-interfaz-recepcion-rol`), ByteTrack ya registra órdenes en estado `RECEPCIONADO` bajo control de sesión y rol. Para alcanzar el hito **IOC (Capacidad Operativa Inicial)** de la fase de Construcción AUP, esta especificación cubre las iteraciones **C2, C3 y C4**:

- **Iteración C2**: consulta de stock libre (`CU-07`) y emisión de diagnóstico y presupuesto (`CU-02`, `GUI-03`) con reserva atómica todo-o-nada (`RN-04`, `RNF-01`), alerta `E02` y restricción del Técnico a sus órdenes asignadas (`RN-03`).
- **Iteración C3**: registro de la decisión del cliente con evidencia (`CU-03`, `GUI-04`, `RN-05`, `RN-06`) y finalización técnica con prueba de funcionamiento conforme y consumo definitivo de inventario (`CU-08`, `GUI-05`, `RN-07`).
- **Iteración C4**: liquidación, cobro único total, emisión de comprobante interno `CP-AAAA-NNNN` y entrega en una sola transacción (`CU-04`, `GUI-06`, `RN-08`, `RN-09`), incluyendo la devolución de órdenes en `RECHAZADO` cobrando la revisión inicial (`RN-11`), además de los tableros operativos paginados de órdenes, clientes y almacén.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar stock libre y emitir diagnóstico con reserva atómica (Priority: P1 — Iteración C2)

El Técnico de laboratorio inicia sesión, consulta en `GUI-03` una orden asignada en estado `RECEPCIONADO`, busca repuestos con stock libre positivo (`CU-07`), redacta el informe técnico, ingresa la mano de obra y presiona «Emitir diagnóstico y presupuesto» (`CU-02`). El sistema reserva de forma atómica todos los repuestos requeridos sobre el stock libre (`stock_disponible - stock_reservado`), guarda el diagnóstico y cambia la orden a `PRESUPUESTADO`. Si algún ítem carece de stock libre suficiente, aborta toda la operación y muestra la alerta **E02** (`RN-04`, `RNF-01`).

**Why this priority**: Resuelve el riesgo técnico más alto del proyecto (`R1`: asignación simultánea de la última unidad de stock) y habilita los casos de uso posteriores (`CU-03`, `CU-08` y `CU-04`).

**Independent Test**: Con una orden `RECEPCIONADO` asignada al Técnico autenticado y repuestos en almacén, emitir presupuesto con repuestos (pasa a `PRESUPUESTADO` y sube `stock_reservado`), probar presupuesto solo con mano de obra (`CU-02-6b`) y probar un ítem sin stock libre verificando alerta `E02` (`409`) y cero reservas parciales (`CU-02-9a`).

**Acceptance Scenarios**:

1. **Given** una orden `RECEPCIONADO` asignada al Técnico y repuestos con stock libre suficiente, **When** emite diagnóstico con `id_op`, **Then** el sistema reserva las unidades, calcula subtotales con precios de servidor, cambia la orden a `PRESUPUESTADO` y responde `201` (`CU-02-B`, `RN-04`).
2. **Given** una reparación de software sin repuestos, **When** el Técnico emite diagnóstico con lista de repuestos vacía, **Then** el total iguala la mano de obra y la orden pasa a `PRESUPUESTADO` (`CU-02-6b`).
3. **Given** un presupuesto con dos repuestos donde el segundo tiene `stock_libre = 0`, **When** el Técnico confirma, **Then** el sistema revierte toda la transacción, no reserva el primer repuesto, conserva `RECEPCIONADO` y devuelve `409` con código `E02` (`CU-02-9a`, `RNF-01`).
4. **Given** una orden asignada a otro técnico, **When** un Técnico intenta consultarla o diagnosticarla, **Then** el sistema rechaza con `403 ORDEN_NO_ASIGNADA` (`RN-03`, `RNF-02`).
5. **Given** un diagnóstico ya confirmado con `id_op`, **When** se repite el envío con los mismos datos, **Then** responde `200` con `reintento=true` sin duplicar reservas (`CU-02-9b`, `RN-10`).

---

### User Story 2 - Registrar decisión del cliente sobre el presupuesto (Priority: P1 — Iteración C3)

La Recepcionista carga en `GUI-04` una orden en estado `PRESUPUESTADO`, selecciona `APROBADO` o `RECHAZADO`, indica el canal (`WHATSAPP`, `LLAMADA` o `PRESENCIAL`) y redacta la evidencia textual (`CU-03`, `RN-05`). Si aprueba, se mantienen las reservas activas y pasa a `APROBADO`; si rechaza, se liberan de inmediato todas las reservas hacia el stock libre y pasa a `RECHAZADO` (`RN-06`).

**Why this priority**: Gobierna el ciclo de reservas de almacén y documenta la conformidad comercial del cliente antes de intervenir el equipo.

**Independent Test**: Emitir un presupuesto con 2 unidades reservadas; aprobar una orden verificando que `stock_reservado` permanece en 2 (`CU-03-B`) y rechazar otra orden verificando que `stock_reservado` vuelve a 0 y `estado_reserva = LIBERADO` (`CU-03-3a`).

**Acceptance Scenarios**:

1. **Given** una orden en `PRESUPUESTADO` con repuestos reservados, **When** la Recepcionista registra `APROBADO` con canal y evidencia, **Then** la orden pasa a `APROBADO` y las reservas permanecen en `RESERVADO` (`CU-03-B`, `RN-05`, `RN-06`).
2. **Given** una orden en `PRESUPUESTADO` con repuestos reservados, **When** la Recepcionista registra `RECHAZADO` con canal y evidencia, **Then** `stock_reservado` disminuye de inmediato, los detalles pasan a `LIBERADO` y la orden pasa a `RECHAZADO` (`CU-03-3a`, `RN-06`).
3. **Given** una orden que no está en `PRESUPUESTADO`, **When** se intenta registrar decisión, **Then** el sistema rechaza con `409 ESTADO_ORDEN_INVALIDO` (`CU-03-2a`).

---

### User Story 3 - Finalizar reparación y consumir repuestos reservados (Priority: P1 — Iteración C3)

El Técnico asignado abre en `GUI-05` una orden en estado `APROBADO`, describe el trabajo realizado, marca «Prueba de funcionamiento conforme» (`prueba_conforme = true`), detalla el resultado de la prueba y confirma «Finalizar reparación» (`CU-08`). El sistema consume definitivamente los repuestos reservados (`stock_disponible` y `stock_reservado` disminuyen), reduce en 1 la cola del técnico y cambia la orden a `LISTO` (`RN-07`).

**Why this priority**: Asegura calidad técnica previa a la entrega y sincroniza el stock físico real con las piezas instaladas.

**Independent Test**: Intentar finalizar con `prueba_conforme = false` verificando rechazo `422 PRUEBA_NO_CONFORME` (`CU-08-4a`); finalizar con `prueba_conforme = true` verificando paso a `LISTO`, descuento de `stock_disponible` y decremento de cola (`CU-08-B`).

**Acceptance Scenarios**:

1. **Given** una orden `APROBADO` asignada al Técnico con 2 unidades reservadas de un repuesto con `stock_disponible = 3`, **When** finaliza con `prueba_conforme = true`, **Then** la orden pasa a `LISTO`, el repuesto queda con `stock_disponible = 1` y `stock_reservado = 0`, y los detalles pasan a `CONSUMIDO` (`CU-08-B`, `RN-07`).
2. **Given** que `prueba_conforme` es `false`, **When** el Técnico intenta finalizar, **Then** el sistema rechaza con `422 PRUEBA_NO_CONFORME` sin tocar el stock (`CU-08-4a`, `RN-07`).

---

### User Story 4 - Liquidar orden, emitir comprobante interno y entregar equipo (Priority: P1 — Iteración C4)

La Recepcionista busca en `GUI-06` una orden en estado `LISTO` (o `RECHAZADO` para devolución), verifica el total a cobrar, elige el método de pago (`EFECTIVO`, `TARJETA` o `TRANSFERENCIA`), ingresa el monto exacto, marca la conformidad de entrega y confirma «Cobrar y entregar» (`CU-04`). En una única transacción se registra el pago total, se emite el comprobante `CP-AAAA-NNNN` y la orden pasa a `ENTREGADO`, liberando el número de serie para futuros ingresos (`RN-08`, `RN-09`, `RN-11`).

**Why this priority**: Cierra el ciclo operativo y financiero del taller ("100 % de entregas con cobro y comprobante registrados") y habilita el reingreso futuro del equipo (`RN-02`).

**Independent Test**: Intentar pago parcial (`422 MONTO_INCOMPLETO`) o sin conformidad (`422 CONFORMIDAD_REQUERIDA`); liquidar con el monto exacto verificando `CP-AAAA-NNNN`, paso a `ENTREGADO` y que el mismo número de serie ya permite crear una nueva orden en `CU-01`.

**Acceptance Scenarios**:

1. **Given** una orden en `LISTO` con presupuesto total de `S/ 500.00`, **When** la Recepcionista liquida con `monto_recibido = 500.00` y `conformidad_entrega = true`, **Then** se genera `CP-AAAA-NNNN`, la orden pasa a `ENTREGADO` y responde `201` (`CU-04-B`, `RN-08`, `RN-09`).
2. **Given** una orden en `RECHAZADO` con costo de revisión `S/ 40.00`, **When** la Recepcionista liquida la devolución con `40.00` y conformidad, **Then** se emite comprobante por `S/ 40.00` y la orden pasa a `ENTREGADO` liberando la serie (`RN-11`).
3. **Given** un monto distinto al total o `conformidad_entrega = false`, **When** intenta liquidar, **Then** el sistema rechaza con `422` sin emitir comprobante ni cambiar el estado (`CU-04-3a`, `RN-08`).
4. **Given** una liquidación confirmada con `id_op`, **When** se repite la solicitud, **Then** responde `200` devolviendo el mismo comprobante `CP-AAAA-NNNN` (`CU-04-4a`, `RN-10`).

---

### User Story 5 - Trazabilidad operativa paginada por rol (Priority: P2 — C2 a C4)

Tanto la Recepcionista como el Técnico disponen de un panel operativo con indicadores por estado, carga de técnicos, listado paginado de órdenes (filtrado automáticamente a las órdenes propias cuando el rol es Técnico, `RN-03`), consulta de almacén (`CU-07`) y directorio paginado de clientes para Recepción (`RF-01`, `RF-02`, `RF-03`).

**Independent Test**: Consultar `GET /ordenes`, `GET /ordenes/resumen`, `GET /repuestos` y `GET /clientes` con ambos roles y verificar paginación, aislamiento de órdenes por técnico y rechazo `403` a Técnico en `GET /clientes`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST listar repuestos paginados filtrados por SKU o nombre calculando `stock_libre = stock_disponible - stock_reservado` (`CU-07`, `RF-03`, `RN-04`).
- **FR-002**: `POST /ordenes/{codigo}/diagnostico` MUST estar restringido al rol `TECNICO` y únicamente sobre órdenes asignadas a dicho técnico en estado `RECEPCIONADO` (`CU-02`, `RN-03`, `RNF-02`).
- **FR-003**: Al emitir diagnóstico, el sistema MUST validar y reservar todos los repuestos solicitados o ninguno dentro de una transacción `BEGIN IMMEDIATE`; ante falta de stock libre MUST lanzar `409 E02` sin mutar ningún repuesto (`RN-04`, `RNF-01`).
- **FR-004**: El sistema MUST admitir diagnósticos sin repuestos (`repuestos = []`), calculando `total_presupuesto = costo_mano_obra` (`CU-02` curso `6b`).
- **FR-005**: `DetalleRepuesto` MUST almacenar `precio_cotizado` al momento del presupuesto para aislar la cotización frente a cambios futuros de catálogo (`caso.md` §4.2.1).
- **FR-006**: `POST /ordenes/{codigo}/decision` MUST estar restringido al rol `RECEPCIONISTA` sobre órdenes en `PRESUPUESTADO` y exigir `decision`, `canal` y `evidencia` textual (`CU-03`, `RF-04`, `RN-05`, `RNF-02`).
- **FR-007**: Al registrar `RECHAZADO`, el sistema MUST liberar inmediatamente las reservas activas (`stock_reservado -= cantidad`, `estado_reserva = LIBERADO`) y pasar la orden a `RECHAZADO`; si es `APROBADO`, mantiene las reservas y pasa a `APROBADO` (`RN-06`).
- **FR-008**: `POST /ordenes/{codigo}/finalizar` MUST estar restringido al rol `TECNICO` asignado sobre órdenes en `APROBADO`, exigir `prueba_conforme = true` y `resultado_prueba` no vacío (`422 PRUEBA_NO_CONFORME` en caso contrario), consumir definitivamente el stock (`stock_disponible -= cantidad`, `stock_reservado -= cantidad`, `estado_reserva = CONSUMIDO`), decrementar la cola del técnico y pasar la orden a `LISTO` (`CU-08`, `RF-06`, `RN-03`, `RN-07`).
- **FR-009**: `POST /ordenes/{codigo}/liquidar` MUST estar restringido al rol `RECEPCIONISTA` sobre órdenes en `LISTO` (cobrando `total_presupuesto`) o `RECHAZADO` (cobrando `costo_revision`, `RN-11`), exigir `conformidad_entrega = true` y pago único exacto (`RN-08`), emitir `CP-AAAA-NNNN` y cambiar el estado a `ENTREGADO` en la misma transacción (`CU-04`, `RF-05`, `RN-09`).
- **FR-010**: Las cuatro escrituras transaccionales (`CU-02`, `CU-03`, `CU-08`, `CU-04`) MUST ser idempotentes por `id_op` con verificación de huella SHA-256 (`RN-10`, `RNF-04`).
- **FR-011**: Las pantallas `GUI-03`, `GUI-04`, `GUI-05`, `GUI-06` y las vistas de panel, clientes y almacén en `app/web/index.html` MUST trazarse con `data-trace`, operar según el rol activo y emplear exclusivamente `textContent`.

### Key Entities

- **Repuesto**: `sku` único, `nombre`, `stock_disponible >= 0`, `stock_reservado >= 0` (`<= stock_disponible`), `precio_unitario` y propiedad calculada `stock_libre`.
- **Diagnostico**: relación 1:1 con `OrdenServicio`; `informe_tecnico`, `costo_mano_obra`, `subtotal_repuestos`, `total_presupuesto`, `fecha_emision`.
- **DetalleRepuesto**: ítem cotizado con `cantidad > 0`, `precio_cotizado`, `subtotal` y `estado_reserva` (`RESERVADO`, `LIBERADO`, `CONSUMIDO`).
- **ComprobantePago**: relación 1:1 con `OrdenServicio`; `numero` único `CP-AAAA-NNNN`, `metodo_pago` (`EFECTIVO`, `TARJETA`, `TRANSFERENCIA`), `monto_total`, `conformidad_entrega`.
- **Usuario (extensión)**: atributo opcional `tecnico_id` que vincula la cuenta `TECNICO` con su registro de `Tecnico` para hacer cumplir `RN-03`.

## Success Criteria *(mandatory)*

- **SC-001**: El flujo completo `RECEPCIONADO → PRESUPUESTADO → APROBADO → LISTO → ENTREGADO` y la ruta alterna `PRESUPUESTADO → RECHAZADO → ENTREGADO (RN-11)` se ejecutan sin inconsistencias de stock ni bloqueos de serie residuales.
- **SC-002**: El 100 % de los intentos de sobre-reservar stock libre en presupuestos simples, múltiples o concurrentes abortan con `E02` dejando `0` reservas parciales (`RNF-01`).
- **SC-003**: El 100 % de los accesos de un Técnico a órdenes de otro técnico o a endpoints de Recepción (`CU-01`, `CU-03`, `CU-04`, `CU-06`, `GET /clientes`) y los accesos de Recepcionista a endpoints exclusivos de Técnico (`CU-02`, `CU-08`) son rechazados con `403` (`RN-03`, `RNF-02`).
- **SC-004**: Las 17 operaciones de la API pasan la auditoría automática de etiquetas y reglas en OpenAPI (`test_trazabilidad_swagger.py`) y todos los controles del DOM pasan la auditoría estática (`test_interfaz_estatica.py`).

## Alcance y Fuera de Alcance

**En alcance (C2–C4)**: `CU-02`, `CU-03`, `CU-04`, `CU-07`, `CU-08`; pantallas `GUI-03` a `GUI-06` y vistas de seguimiento paginado; reglas `RN-03` (acceso a órdenes propias), `RN-04` a `RN-09`, `RN-10` y `RN-11`; `RF-03` a `RF-06`, `RNF-01`, `RNF-02` completo y `RNF-04` completo.

**Fuera de alcance**: pasarela bancaria externa, pagos fraccionados, facturación electrónica SUNAT, compras a proveedores, alta/edición de catálogo de repuestos desde UI, gestión CRUD de usuarios y portal de autoatención para el cliente (`caso.md` §2.1 Tabla 4).

## Matriz de Trazabilidad

| Caso / Código | Iteración | Endpoint / Vista | Reglas / RNF verificados | Prueba automatizada |
|---------------|-----------|------------------|--------------------------|---------------------|
| `CU-07` | C2 | `GET /repuestos` · `GUI-03` / `vista-almacen` | `RF-03`, `RN-04`, `RNF-02` | `test_flujo_taller.py` |
| `CU-02-B`, `6b`, `9a`, `9b` | C2 | `POST /ordenes/{codigo}/diagnostico` · `GUI-03` (`alerta-e02`) | `RF-03`, `RN-03`, `RN-04`, `RN-10`, `RNF-01`, `RNF-02` | `test_flujo_taller.py` |
| `CU-03-B`, `2a`, `3a`, `4a` | C3 | `POST /ordenes/{codigo}/decision` · `GUI-04` | `RF-04`, `RN-05`, `RN-06`, `RN-10`, `RNF-02` | `test_flujo_taller.py` |
| `CU-08-B`, `4a`, `6a` | C3 | `POST /ordenes/{codigo}/finalizar` · `GUI-05` | `RF-06`, `RN-03`, `RN-07`, `RN-10`, `RNF-02` | `test_flujo_taller.py` |
| `CU-04-B`, `1a`, `3a`, `4a` | C4 | `POST /ordenes/{codigo}/liquidar` · `GUI-06` | `RF-05`, `RN-08`, `RN-09`, `RN-10`, `RN-11`, `RNF-01`, `RNF-02` | `test_flujo_taller.py` |
| Seguimiento / Trazabilidad | C2–C4 | `GET /ordenes`, `/ordenes/resumen`, `/ordenes/{codigo}`, `/tecnicos/resumen`, `/clientes` · `vista-panel`, `vista-clientes` | `RF-01`, `RF-02`, `RN-01`, `RN-03`, `RNF-02` | `test_flujo_taller.py`, `test_trazabilidad_swagger.py`, `test_interfaz_estatica.py` |
