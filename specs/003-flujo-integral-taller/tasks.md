---
description: "Lista de tareas de las iteraciones C2, C3 y C4: flujo integral del taller ByteTrack"
---

# Tasks: Flujo integral de laboratorio, decisión y liquidación (Iteraciones C2, C3 y C4)

**Input**: Documentos de diseño en `/specs/003-flujo-integral-taller/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [data-model.md](data-model.md), [contracts/api-taller.md](contracts/api-taller.md)

**Tests**: OBLIGATORIOS (Constitución principio III). Todas las reglas `RN-03` a `RN-11`, `RNF-01`, `RNF-02` y `RNF-04` cuentan con verificación automatizada en `pytest`.

## Phase 1: Foundational (Modelo de Dominio Refinado, Seguridad Técnico y Errores)

- [X] T001 Ampliar `app/models/entities.py` con las entidades `Repuesto` (`stock_disponible`, `stock_reservado`, `stock_libre` y `CHECK stock_reservado <= stock_disponible`), `Diagnostico`, `DetalleRepuesto` (`RESERVADO`, `LIBERADO`, `CONSUMIDO`), `ComprobantePago` (`CP-AAAA-NNNN`), los atributos de decisión y cierre en `OrdenServicio`, y `Usuario.tecnico_id` (`RN-03`)
- [X] T002 [P] Incorporar en `app/errors.py` las excepciones `OrdenNoEncontrada`, `OrdenNoAsignada` (`RN-03`), `EstadoOrdenInvalido`, `RepuestoNoEncontrado`, `StockInsuficienteError` (`E02`, `RN-04`), `PruebaNoConformeError` (`RN-07`), `MontoIncompletoError` (`RN-08`) y `ConformidadRequeridaError` (`RN-08`)
- [X] T003 [P] Definir en `app/models/schemas.py` los esquemas Pydantic `RepuestoOut`, `PaginaRepuestosOut`, `DiagnosticoIn/Out`, `EmitirDiagnosticoOut`, `DecisionIn`, `RegistrarDecisionOut`, `FinalizarReparacionIn/Out`, `LiquidarOrdenIn/Out`, `ComprobantePagoOut`, `OrdenDetalleOut`, `PaginaOrdenesOut`, `ResumenTallerOut`, `TecnicoCargaOut` y `PaginaClientesOut`
- [X] T004 [P] Añadir la dependencia `exigir_tecnico` en `app/api/seguridad.py` (`RNF-02`) y las etiquetas OpenAPI `CU-02 · GUI-03`, `CU-03 · GUI-04`, `CU-04 · GUI-06`, `CU-07 · GUI-03` y `CU-08 · GUI-05` en `app/api/etiquetas.py`
- [X] T005 Implementar `app/repositories/repuesto_repository.py` y ampliar `orden_repository.py`, `cliente_repository.py` y `tecnico_repository.py` con consultas paginadas, resumen por estado y correlativo anual `CP-AAAA-NNNN`

---

## Phase 2: User Story 1 — Iteración C2: Stock libre (`CU-07`) y Diagnóstico atómico (`CU-02`)

- [X] T006 [P] [US1] Escribir pruebas de `CU-07` y `CU-02` en `tests/test_flujo_taller.py`: búsqueda paginada de stock libre, emisión de presupuesto con reserva atómica (`RN-04`), alerta `E02` todo-o-nada sin reservas parciales (`RNF-01`), idempotencia (`RN-10`) y rechazo `403` a Recepcionista o Técnico no asignado (`RN-03`, `RNF-02`)
- [X] T007 [US1] Implementar `consultar_repuestos` y `emitir_diagnostico` (con `BEGIN IMMEDIATE` y huella SHA-256) en `app/services/flujo_taller_service.py`
- [X] T008 [US1] Exponer `GET /repuestos` y `POST /ordenes/{codigo}/diagnostico` en `app/api/taller.py`
- [X] T009 [US1] Construir la vista `vista-diagnostico` (`GUI-03` con buscador `CU-07`, tabla de cotización, alerta `alerta-e02` e `id_op`) y `vista-almacen` en `app/web/index.html` y `app/web/js/taller.js`

---

## Phase 3: User Story 2 — Iteración C3a: Decisión de presupuesto (`CU-03`)

- [X] T010 [P] [US2] Escribir pruebas de `CU-03` en `tests/test_flujo_taller.py`: aprobación manteniendo reserva activa (`RN-05`, `RN-06`) y rechazo liberando inmediatamente `stock_reservado` hacia el stock libre (`CU-03-3a`)
- [X] T011 [US2] Implementar `registrar_decision` en `app/services/flujo_taller_service.py` y exponer `POST /ordenes/{codigo}/decision` en `app/api/taller.py` (restringido a `RECEPCIONISTA`)
- [X] T012 [US2] Construir la vista `vista-decision` (`GUI-04` con resumen del presupuesto, selector de decisión, canal, evidencia e `id_op`) en `app/web/index.html` y `app/web/js/taller.js`

---

## Phase 4: User Story 3 — Iteración C3b: Finalizar reparación (`CU-08`)

- [X] T013 [P] [US3] Escribir pruebas de `CU-08` en `tests/test_flujo_taller.py`: rechazo `422 PRUEBA_NO_CONFORME` cuando `prueba_conforme=False` (`RN-07`) y consumo definitivo de `stock_disponible` + paso a `LISTO` cuando es `True`
- [X] T014 [US3] Implementar `finalizar_reparacion` en `app/services/flujo_taller_service.py` y exponer `POST /ordenes/{codigo}/finalizar` en `app/api/taller.py` (restringido a `TECNICO` asignado)
- [X] T015 [US3] Construir la vista `vista-finalizar` (`GUI-05` con botón deshabilitado hasta marcar prueba conforme, `RN-07`) en `app/web/index.html` y `app/web/js/taller.js`

---

## Phase 5: User Story 4 — Iteración C4: Liquidación, comprobante y entrega (`CU-04` + `RN-11`)

- [X] T016 [P] [US4] Escribir pruebas de `CU-04` y `RN-11` en `tests/test_flujo_taller.py`: rechazo de pago parcial (`RN-08`), liquidación atómica con emisión de `CP-AAAA-NNNN` y paso a `ENTREGADO` (`RN-09`), devolución de orden `RECHAZADO` cobrando `costo_revision` (`RN-11`) y posterior reingreso de la misma serie (`RN-02`)
- [X] T017 [US4] Implementar `liquidar_orden` en `app/services/flujo_taller_service.py` y exponer `POST /ordenes/{codigo}/liquidar` en `app/api/taller.py` (restringido a `RECEPCIONISTA`)
- [X] T018 [US4] Construir la vista `vista-cobro` (`GUI-06` con método de pago, monto exacto, conformidad e impresión de comprobante) en `app/web/index.html`, `app/web/js/taller.js` y `app/web/js/ui_addons.js`

---

## Phase 6: User Story 5 & Polish — Seguimiento Operativo, Trazabilidad y Auditoría SDD

- [X] T019 [US5] Implementar endpoints de panel y seguimiento (`GET /ordenes`, `GET /ordenes/resumen`, `GET /tecnicos/resumen`, `GET /clientes`, `GET /ordenes/{codigo}`), registrar `taller.router` en `app/main.py` y configurar pestañas por rol en `app/web/js/app.js`
- [X] T020 [P] Ampliar `app/seed.py` con catálogo inicial de 8 repuestos y 7 órdenes demostrativas distribuidas en todos los estados del ciclo AUP
- [X] T021 [P] Actualizar `tests/test_trazabilidad_swagger.py` (17 operaciones trazadas con sus reglas `RN`/`RNF`) y `tests/test_interfaz_estatica.py` (`IDS_BASE_AUP` para `GUI-01` a `GUI-06`, cero `innerHTML` y CSP activa), y verificar `uv run pytest` completo
