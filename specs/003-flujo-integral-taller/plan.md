# Implementation Plan: Flujo integral de laboratorio, decisión y liquidación (Iteraciones C2, C3 y C4)

**Branch**: `003-flujo-integral-taller` | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-flujo-integral-taller/spec.md`

## Summary

Completa la fase de Construcción AUP implementando las iteraciones C2 (`CU-07`, `CU-02`), C3 (`CU-03`, `CU-08`) y C4 (`CU-04` + integración total del taller) tanto en la API FastAPI como en la aplicación web modular sin framework. Se consolida una unidad de trabajo transaccional serializada con `BEGIN IMMEDIATE` en SQLite que garantiza la atomicidad todo-o-nada de reservas de stock (`RNF-01`, `RN-04`, alerta `E02`), la liberación o consumo exacto de inventario (`RN-06`, `RN-07`), el cobro único con comprobante `CP-AAAA-NNNN` (`RN-08`, `RN-09`, `RN-11`) y la idempotencia criptográfica por `id_op` (`RN-10`, `RNF-04`).

## Technical Context

- **Language/Version**: Python 3.12 + JavaScript ES Modules nativo en navegador.
- **Primary Dependencies**: FastAPI, SQLAlchemy 2.x, Pydantic v2, Uvicorn, `pyjwt`, `python-multipart`, `python-dotenv` (sin nuevas dependencias respecto de la constitución 1.3.0/1.4.0).
- **Storage**: SQLite local (`WAL`, `foreign_keys=ON`, `busy_timeout=30000`, `BEGIN IMMEDIATE` explícito). Nuevas tablas: `repuesto`, `diagnostico`, `detalle_repuesto`, `comprobante_pago`; ampliación de `orden_servicio` y `usuario.tecnico_id`.
- **Testing**: `pytest` con base de datos temporal aislada por prueba (`tests/test_flujo_taller.py`, `tests/test_trazabilidad_swagger.py`, `tests/test_interfaz_estatica.py`).
- **Project Type**: Monolito modular web-service (API REST + SPA estática vanilla servida en `/`).
- **Constraints**: Prohibido `innerHTML` y CDN externos; CSP estricta (`default-src 'self'`); control de acceso aplicado en el servidor (`exigir_recepcionista`, `exigir_tecnico`, `_verificar_acceso_tecnico`).

## Decisiones Técnicas Clave

1. **Reserva atómica en SQLite (`RNF-01` / `RN-04`)**: Dado que SQLite bloquea a nivel de base de datos de escritura y no por fila (`SELECT ... FOR UPDATE`), `iniciar_escritura(sesion)` emite `BEGIN IMMEDIATE` antes de leer la orden y los repuestos. Ninguna otra transacción puede modificar `stock_reservado` entre la validación de todos los ítems y el `COMMIT`; además, la tabla `repuesto` impone `CHECK (stock_reservado <= stock_disponible)` como segunda barrera en el motor.
2. **Idempotencia transversal (`RN-10` / `RNF-04`)**: Se reutiliza `operacion_idempotente` calculando una huella SHA-256 canónica sobre `{"op": "CU-xx", "codigo": codigo, "datos": payload_sin_id_op}`. Un reintento idéntico devuelve el JSON original con `reintento=True`; datos distintos con igual `id_op` lanzan `409 ID_OP_CONFLICTO`.
3. **Resolución de las decisiones de `caso.md` §4.1**:
   - Precondición de `CU-08`: estado `APROBADO`.
   - Ruta de devolución (`RN-11`): `CU-04` acepta órdenes en `RECHAZADO` exigiendo como pago exacto `orden.costo_revision`, emitiendo el comprobante `CP-AAAA-NNNN` y pasando a `ENTREGADO` para desbloquear el número de serie (`RN-02`).

## Constitution Check (v1.4.0)

| Principio | Verificación en este plan | Estado |
|-----------|---------------------------|--------|
| I. Documentación AUP como fuente de verdad | Se conservan intactos `CU-02/03/04/07/08`, `RN-03` a `RN-11`, `E02`, `GUI-03` a `GUI-06` y el formato `CP-AAAA-NNNN`. | PASA |
| II. Especificación antes que código | Especificación, modelo de datos, contratos y tareas estructurados y trazados. | PASA |
| III. Pruebas automatizadas obligatorias | Todas las reglas `RN-01` a `RN-11` y `RNF-01`, `RNF-02`, `RNF-04` cuentan con pruebas automatizadas en `tests/`. | PASA |
| IV. Arquitectura en capas | `app/api/taller.py` → `app/services/flujo_taller_service.py` → `app/repositories/{orden,repuesto,operacion,cliente,tecnico}_repository.py` → `app/models/entities.py`. | PASA |
| V. Simplicidad e integraciones | SQLite local sin servicios adicionales ni dependencias externas nuevas. | PASA |
| VI. Sin credenciales en el repositorio | `app/seed.py` pobla repuestos y órdenes demo sin contraseñas en código; secretos solo en `.env`. | PASA |
| VII y VIII. Alcance acotado y cerrado | Cada endpoint (17 en total) y cada control HTML con `id` declara su código AUP, verificado automáticamente por `pytest`. | PASA |

## Project Structure

### Documentation (this feature)

```text
specs/003-flujo-integral-taller/
├── spec.md              # Especificación funcional C2, C3 y C4
├── plan.md              # Plan técnico y verificación constitucional
├── data-model.md        # Modelo relacional completo y máquina de estados
├── contracts/
│   └── api-taller.md    # Contratos REST de seguimiento, almacén, diagnóstico, decisión y cobro
└── tasks.md             # Desglose de tareas ejecutadas por historia de usuario
```

### Source Code Impact

```text
app/
├── api/
│   ├── etiquetas.py                 ~ Etiquetas OpenAPI CU-02·GUI-03, CU-03·GUI-04, CU-04·GUI-06, CU-07·GUI-03, CU-08·GUI-05
│   ├── seguridad.py                 ~ Dependencia exigir_tecnico (RNF-02)
│   └── taller.py                    + 10 endpoints (seguimiento, CU-07, CU-02, CU-03, CU-08, CU-04)
├── services/
│   └── flujo_taller_service.py      + Lógica transaccional de CU-07, CU-02, CU-03, CU-08, CU-04 y paneles
├── repositories/
│   ├── repuesto_repository.py       + Búsqueda paginada, bloqueo lógico por IDs y alerta de stock bajo
│   ├── orden_repository.py          ~ Paginación filtrada por técnico, resumen por estado y correlativo CP-AAAA-NNNN
│   ├── cliente_repository.py        ~ Directorio paginado de clientes y equipos
│   └── tecnico_repository.py        ~ Listado completo de carga de trabajo
├── models/
│   ├── entities.py                  ~ Repuesto, Diagnostico, DetalleRepuesto, ComprobantePago, Usuario.tecnico_id
│   └── schemas.py                   ~ Esquemas Pydantic de entrada/salida y páginas
├── errors.py                        ~ E02, OrdenNoAsignada, EstadoOrdenInvalido, PruebaNoConformeError, MontoIncompletoError, ConformidadRequeridaError
├── seed.py                          ~ Catálogo de 8 repuestos y 7 órdenes demo en todos los estados AUP
└── web/
    ├── index.html                   ~ Vistas GUI-03 a GUI-06, panel KPI, directorio de clientes, almacén y modal timeline
    ├── css/estilos.css              ~ Estilos responsivos, badges de estado, tema claro/oscuro e impresión
    └── js/
        ├── app.js                   ~ Navegación lateral filtrada según rol (RECEPCIONISTA vs TECNICO)
        ├── taller.js                + Controladores de GUI-03, GUI-04, GUI-05, GUI-06, panel y almacén
        └── ui_addons.js             + Tema visual, notificaciones toast, modal de línea de tiempo y exportación CSV/impresión

tests/
├── test_flujo_taller.py             + Ciclo completo C1→C4, E02 todo-o-nada, rechazo RN-06, devolución RN-11 y paginación
├── test_trazabilidad_swagger.py     ~ Verificación de los 17 endpoints y sus reglas RN/RNF
└── test_interfaz_estatica.py        ~ Verificación de IDS_BASE_AUP (GUI-01 a GUI-06) y data-trace
```
