# Data Model: Iteración C1 — Recepción y orden de servicio

Modelo lógico de las entidades de C1, derivado de [spec.md](spec.md) y del modelo de dominio de `docs/aup/caso.md`. Solo se incluyen los atributos necesarios para CU-05, CU-06 y CU-01; las demás clases del dominio (Diagnostico, DetalleRepuesto, Repuesto, ComprobantePago) se incorporan en iteraciones posteriores.

## Entidades

### Cliente (`cliente`)

| Campo | Tipo | Reglas |
|-------|------|--------|
| id | entero, PK | Generado |
| dni | texto de 8 dígitos | **Único**; restricción de formato `^[0-9]{8}$` (RN-01) |
| nombres | texto | Obligatorio |
| apellidos | texto | Obligatorio |
| telefono | texto | Obligatorio |
| correo | texto | Opcional |

Relaciones: un cliente tiene 0..N equipos.

### Equipo (`equipo`)

| Campo | Tipo | Reglas |
|-------|------|--------|
| id | entero, PK | Generado |
| cliente_id | FK → cliente | Obligatorio |
| tipo | texto | Obligatorio |
| marca | texto | Obligatorio |
| modelo | texto | Obligatorio |
| numero_serie | texto | **Único** en todo el sistema (RN-01); obligatorio, sin espacios sobrantes |

Relaciones: pertenece a un cliente; tiene 0..N órdenes en el tiempo, pero solo una con estado distinto de ENTREGADO (RN-02).

### Técnico (`tecnico`)

| Campo | Tipo | Reglas |
|-------|------|--------|
| id | entero, PK | Generado |
| nombres | texto | Obligatorio |
| apellidos | texto | Obligatorio |
| disponible | booleano | La asignación solo es válida si es verdadero (RN-03) |
| cola | entero | ≥ 0; se incrementa en 1 por cada orden asignada (CU-01 paso 6) |

Los técnicos se cargan como datos previos (seed o fixtures); su mantenimiento no pertenece a C1.

### Orden de servicio (`orden_servicio`)

| Campo | Tipo | Reglas |
|-------|------|--------|
| id | entero, PK | Generado |
| codigo | texto | Único; formato `OS-AAAA-NNNN` (GUI-01): año de la recepción y correlativo del año |
| equipo_id | FK → equipo | Obligatorio |
| tecnico_id | FK → tecnico | Obligatorio; técnico disponible al crear (RN-03) |
| estado | texto | `RECEPCIONADO` al crearse; valores del dominio: RECEPCIONADO, PRESUPUESTADO, APROBADO, RECHAZADO, LISTO, ENTREGADO (C1 solo crea RECEPCIONADO) |
| accesorios | texto | Opcional |
| estado_fisico | texto | Obligatorio |
| falla_reportada | texto | Obligatorio |
| costo_revision | decimal (2) | Tomado de la configuración al crear |
| id_op | texto | Único; ID OP con el que se creó (RN-10) |

Restricción clave (RN-02): **índice único parcial** sobre `equipo_id` aplicable a las filas con `estado <> 'ENTREGADO'` — impide dos órdenes activas del mismo equipo incluso bajo concurrencia.

### Operación idempotente (`operacion_idempotente`)

| Campo | Tipo | Reglas |
|-------|------|--------|
| id_op | texto, PK | Identificador de la operación (RN-10) |
| huella | texto | SHA-256 de la solicitud normalizada; detecta reutilización con datos distintos |
| orden_id | FK → orden_servicio | Orden creada |
| resultado | JSON (texto) | Respuesta original serializada, devuelta íntegra en los reintentos |

Solo se inserta cuando la operación se confirma, dentro de la misma transacción que la orden y el incremento de cola.

## Relaciones

```text
Cliente 1 ──── 0..N Equipo 1 ──── 0..N OrdenServicio N ──── 1 Tecnico
                                         │ 1
                                         └── 1 OperacionIdempotente (por id_op)
```

## Reglas de validación (trazabilidad)

| Regla | Dónde se aplica | Entidad / restricción |
|-------|-----------------|------------------------|
| RN-01 DNI de 8 dígitos, único | Esquema de entrada, `cliente_service`, restricción `UNIQUE` + `CHECK` | cliente.dni |
| RN-01 Serie única; varios equipos por cliente | `orden_service`, restricción `UNIQUE` | equipo.numero_serie |
| RN-02 Una orden activa por equipo | `orden_service` (E01) + índice único parcial | orden_servicio.equipo_id |
| RN-03 Solo técnico disponible | `orden_service` (revalida dentro de la transacción) | tecnico.disponible |
| RN-10 Idempotencia por ID OP | `orden_service` + tabla | operacion_idempotente |

## Transiciones de estado

C1 solo crea órdenes: `∅ → RECEPCIONADO`. Las transiciones posteriores pertenecen a CU-02, CU-03, CU-08 y CU-04 (fuera de alcance).

## Operación atómica de CU-01 (una transacción)

1. Comprobar `id_op` (reintento → devolver resultado; datos distintos → rechazar).
2. Resolver cliente por DNI y equipo (existente o nuevo); validar serie.
3. Validar que el equipo no tenga orden activa (E01).
4. Validar técnico disponible.
5. Insertar equipo nuevo (si aplica) y orden; fijar `codigo`.
6. `tecnico.cola = tecnico.cola + 1`.
7. Insertar `operacion_idempotente` con el resultado.
8. Confirmar; ante cualquier error, revertir todo.
