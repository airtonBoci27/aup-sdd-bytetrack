---

description: "Lista de tareas de la iteración C1: recepción de equipos y registro de orden de servicio"
---

# Tasks: Recepción de equipos y registro de orden de servicio (Iteración C1)

**Input**: Documentos de diseño en `/specs/001-recepcion-orden-servicio/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api-c1.md](contracts/api-c1.md), [quickstart.md](quickstart.md)

**Tests**: OBLIGATORIOS. La constitución (principio III) exige una prueba automatizada para cada RN-xx en alcance y para cada caso de prueba `CU-xx-<curso>`. Cada prueba lleva en su nombre el código que cubre (por ejemplo `test_cu01_5a_...`, `test_rn02_...`). Las pruebas de cada historia se escriben primero y deben fallar antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario del spec para implementar y probar cada una de forma independiente.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario a la que pertenece (US1 a US5)
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

Proyecto único (web-service) según el plan: `app/` (`api`, `services`, `repositories`, `models`) y `tests/`. Capas obligatorias: API → servicio → repositorio (constitución, principio IV). Solo se trabaja sobre estas tareas (principios II y VII); `docs/aup/` y `.specify/memory/` no se modifican.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Inicialización del proyecto con `uv`

- [ ] T001 Crear `pyproject.toml` y `.python-version` en la raíz: `requires-python = ">=3.12,<3.13"`, dependencias `fastapi`, `uvicorn` y `sqlalchemy>=2`, grupo de desarrollo `pytest` y `httpx`, y `[tool.pytest.ini_options]` con `testpaths = ["tests"]`; ejecutar `uv sync` para generar `uv.lock`
- [ ] T002 Crear `.gitignore` (`*.db`, `*.db-wal`, `*.db-shm`, `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`) y los paquetes vacíos con `__init__.py`: `app/`, `app/api/`, `app/services/`, `app/repositories/`, `app/models/` y `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Infraestructura común que DEBE estar completa antes de cualquier historia

**⚠️ CRITICAL**: Ninguna historia puede empezar hasta terminar esta fase

- [ ] T003 Implementar `app/config.py`: lee de variables de entorno `BYTETRACK_DB_PATH` (por defecto `./bytetrack.db`) y `BYTETRACK_COSTO_REVISION` (por defecto `40.00`, comentario: "valor de prototipo, pendiente de confirmar con el taller"); sin secretos ni credenciales (principio VI)
- [ ] T004 Implementar `app/database.py`: motor SQLAlchemy 2.x para SQLite con `Base` declarativa; en el evento `connect` activar `PRAGMA foreign_keys=ON`, `journal_mode=WAL` y `busy_timeout`; configurar el control de transacciones de `pysqlite` con los eventos `connect`/`begin` para emitir `BEGIN IMMEDIATE` en las transacciones de escritura (research D4); `SessionLocal`, dependencia `get_session` y función `crear_tablas()` (depende de T003)
- [ ] T005 [P] Implementar `app/models/entities.py` con las entidades de [data-model.md](data-model.md) usando `Base` de T004. Restricciones textuales: `cliente.dni` único con `CHECK` de formato `^[0-9]{8}$` (RN-01); `cliente.nombres`, `apellidos`, `telefono` obligatorios y `correo` opcional; `equipo.numero_serie` único en todo el sistema, obligatorio (RN-01) y `equipo.cliente_id` FK obligatoria; `tecnico.disponible` booleano y `tecnico.cola` entero `>= 0`; `orden_servicio.codigo` único con formato `OS-NNNNNN`, `estado` = `RECEPCIONADO` al crearse, `estado_fisico` y `falla_reportada` obligatorios, `accesorios` opcional, `costo_revision` decimal(2), `id_op` único, **índice único parcial** sobre `orden_servicio(equipo_id)` donde `estado <> 'ENTREGADO'` con `sqlite_where` (RN-02); `operacion_idempotente` con `id_op` como PK, `operacion`, `huella` (SHA-256), `orden_id` FK y `resultado` JSON en texto (RN-10) (depende de T004)
- [ ] T006 [P] Implementar `app/errors.py`: excepción base de dominio con `codigo`, `mensaje`, `detalle` y `status_http`, y las subclases `ClienteNoEncontrado` (404, `CLIENTE_NO_ENCONTRADO`, `detalle.habilitar_registro=true`), `OrdenActivaError` (409, `E01`, mensaje "Este número de serie ya posee la Orden activa N.° [X] en laboratorio" con `detalle.orden_activa`), `IdOpConflicto` (409, `ID_OP_CONFLICTO`), `TecnicoNoDisponible` (409, `TECNICO_NO_DISPONIBLE`), `SinTecnicosDisponibles` (409, `SIN_TECNICOS_DISPONIBLES`) y `SerieEnOtroCliente` (409, `SERIE_EN_OTRO_CLIENTE`)
- [ ] T007 [P] Implementar `app/models/schemas.py` con los esquemas Pydantic de [contracts/api-c1.md](contracts/api-c1.md): `DniStr` (exactamente 8 dígitos numéricos, RN-01), `ClienteIn`, `ClienteOut`, `EquipoIn`/`EquipoOut`, `BusquedaClienteOut`, `RegistroClienteOut` (`ya_registrado`, `aviso`), `TecnicoOut`, `OrdenIn` (`id_op` de 8 a 64 caracteres; exactamente uno de `equipo_id` o `equipo`), `OrdenOut`, `CrearOrdenOut` (`orden`, `reintento`) y `ErrorOut`
- [ ] T008 Implementar `app/main.py`: aplicación FastAPI con título/descripción de ByteTrack, etiquetas de Swagger (`CU-05 · GUI-01`, `CU-06 · GUI-02`, `CU-01 · GUI-01`), `crear_tablas()` al iniciar y un manejador global de las excepciones de T006 que devuelve el formato de error uniforme `{codigo, mensaje, detalle}` (depende de T004, T006, T007)
- [ ] T009 Implementar `tests/conftest.py`: base SQLite temporal por prueba en archivo (no en memoria), sobrescritura de la dependencia de sesión, `TestClient`, una fábrica de sesiones independientes para pruebas de concurrencia y fixtures para crear clientes, equipos, técnicos (disponibles y no disponibles) y órdenes directamente en la base (depende de T004, T005, T008)

**Checkpoint**: Base lista; las historias pueden comenzar

---

## Phase 3: User Story 1 - Buscar cliente por DNI y cargar sus equipos (Priority: P1) 🎯 MVP inicial

**Goal**: El Recepcionista busca un cliente por DNI en GUI-01 y ve sus datos y su lista de equipos (CU-05; pasos 1-2 de CU-01).

**Independent Test**: Con clientes y equipos precargados por fixtures, `GET /clientes/{dni}` devuelve datos y equipos; un DNI inexistente devuelve 404 con `habilitar_registro`; un DNI mal formado devuelve 422.

### Tests for User Story 1 ⚠️

> Escribir primero; deben FALLAR antes de implementar

- [ ] T010 [P] [US1] Pruebas en `tests/test_cu05_buscar_cliente.py`: `test_cu01_B_busca_cliente_con_equipos` (200 con nombres, apellidos, teléfono y lista de equipos), `test_cu01_B_cliente_sin_equipos_lista_vacia`, `test_cu01_2a_dni_inexistente_habilita_registro` (404, código `CLIENTE_NO_ENCONTRADO`, `habilitar_registro=true`) y `test_rn01_dni_debe_tener_8_digitos` (422 con menos/más de 8 dígitos y con caracteres no numéricos)

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implementar `app/repositories/cliente_repository.py`: `obtener_por_dni(dni)` y consulta de los equipos del cliente (solo lectura en esta historia)
- [ ] T012 [US1] Implementar `app/services/cliente_service.py`: `buscar_cliente(dni)` que valida el formato de DNI (RN-01, citar `RN-01` en el código) y lanza `ClienteNoEncontrado` si no existe (depende de T011)
- [ ] T013 [US1] Implementar `app/api/clientes.py`: `GET /clientes/{dni}` con etiqueta `CU-05 · GUI-01`, descripción que cita RN-01 y modelo de respuesta `BusquedaClienteOut` (depende de T012)
- [ ] T014 [US1] Registrar el router de clientes en `app/main.py` y ejecutar `uv run pytest tests/test_cu05_buscar_cliente.py` hasta que pase

**Checkpoint**: US1 funcional y probada de forma independiente

---

## Phase 4: User Story 2 - Registrar una orden de servicio (Priority: P1)

**Goal**: Registrar la orden en estado RECEPCIONADO para un equipo existente o nuevo, asignada a un técnico disponible, con la cola del técnico +1 y un código `OS-NNNNNN` (CU-01, curso básico; RN-01, RN-03).

**Independent Test**: Con un cliente, un equipo (o datos de uno nuevo) y un técnico disponible, `POST /ordenes` responde 201 con la orden RECEPCIONADO y la cola del técnico aumenta exactamente en 1; sin campos obligatorios responde 422 y no deja datos.

**Depends on**: US1 (repositorio y servicio de clientes).

### Tests for User Story 2 ⚠️

- [ ] T015 [P] [US2] Pruebas en `tests/test_cu01_registrar_orden.py`: `test_cu01_B_crea_orden_equipo_existente` (201, `RECEPCIONADO`, código con formato `OS-NNNNNN`, costo de revisión de la configuración, cola +1), `test_cu01_B_crea_orden_con_equipo_nuevo`, `test_rn01_cliente_con_varios_equipos`, `test_rn01_serie_en_otro_cliente_rechazada` (409 `SERIE_EN_OTRO_CLIENTE`), `test_cu01_B_campos_obligatorios_422` (falta estado físico, falla, técnico o ambos/ninguno de `equipo_id`/`equipo`), `test_rn03_solo_tecnicos_disponibles_en_lista` (`GET /tecnicos/disponibles`), `test_rn03_tecnico_no_disponible_rechazado` (409), `test_rn03_sin_tecnicos_disponibles` (409), `test_cu01_B_consulta_costo_revision_inicial` y `test_cu01_B_fallo_no_deja_datos_parciales` (equipo nuevo y cola sin cambios tras un rechazo)

### Implementation for User Story 2

- [ ] T016 [P] [US2] Implementar `app/repositories/equipo_repository.py`: obtener por id y por número de serie, y crear equipo
- [ ] T017 [P] [US2] Implementar `app/repositories/tecnico_repository.py`: obtener por id, listar disponibles y `incrementar_cola(tecnico_id)` con actualización atómica `cola = cola + 1`
- [ ] T018 [P] [US2] Implementar `app/repositories/orden_repository.py`: crear orden y fijar `codigo` con formato `OS-` + id de 6 dígitos dentro de la misma transacción
- [ ] T019 [US2] Implementar `app/services/orden_service.py`: `crear_orden(...)` en una sola transacción (unidad de trabajo con `BEGIN IMMEDIATE`) — resuelve cliente por DNI, equipo existente (del cliente) o nuevo con serie única (RN-01), revalida técnico disponible dentro de la transacción (RN-03), crea el equipo nuevo y la orden con el costo de revisión de `app/config.py`, incrementa la cola y revierte todo ante error; además `listar_tecnicos_disponibles()` y `costo_revision_inicial()`; citar `RN-01`/`RN-03` donde se validan (depende de T012, T016, T017, T018)
- [ ] T020 [P] [US2] Implementar `app/api/tecnicos.py`: `GET /tecnicos/disponibles` con etiqueta `CU-01 · GUI-01` y descripción que cita RN-03 (depende de T019)
- [ ] T021 [P] [US2] Implementar `app/api/ordenes.py`: `POST /ordenes` (201, etiqueta `CU-01 · GUI-01`, descripción que cita RN-01, RN-02, RN-03 y RN-10) y `GET /ordenes/costo-revision-inicial` (depende de T019)
- [ ] T022 [US2] Registrar los routers de técnicos y órdenes en `app/main.py` y ejecutar `uv run pytest tests/test_cu01_registrar_orden.py` hasta que pase

**Checkpoint**: US1 y US2 funcionan; ya se puede recibir un equipo de punta a punta (con clientes cargados por fixtures)

---

## Phase 5: User Story 3 - Impedir una segunda orden activa por equipo (Priority: P1)

**Goal**: Bloquear el registro cuando el número de serie tiene una orden con estado distinto de ENTREGADO y mostrar la alerta E01 (CU-01, curso alterno 5a; RN-02).

**Independent Test**: Registrar una orden y volver a intentar con la misma serie: 409 con código `E01` y número de la orden activa; la cola del técnico no cambia.

**Depends on**: US2.

### Tests for User Story 3 ⚠️

- [ ] T023 [P] [US3] Pruebas en `tests/test_cu01_5a_orden_activa.py`: `test_cu01_5a_serie_con_orden_activa_muestra_e01` (409, `codigo` `E01`, mensaje "Este número de serie ya posee la Orden activa N.° [X] en laboratorio" con el código de la orden activa), `test_cu01_5a_equipo_existente_con_orden_activa_bloqueado`, `test_rn02_orden_activa_en_cualquier_estado_distinto_de_entregado`, `test_rn02_permite_nueva_orden_tras_entregado` (orden previa puesta en `ENTREGADO` por fixture), `test_cu01_5a_bloqueo_no_incrementa_cola` y `test_rn02_concurrencia_misma_serie` (dos solicitudes simultáneas con `id_op` distintos desde sesiones independientes: una 201 y otra E01; una sola orden activa)

### Implementation for User Story 3

- [ ] T024 [US3] Añadir en `app/repositories/orden_repository.py` `obtener_activa_por_equipo(equipo_id)` (orden con `estado <> 'ENTREGADO'`) y la detección de la violación del índice único parcial para traducirla a E01
- [ ] T025 [US3] Añadir en `app/services/orden_service.py` la verificación del paso 5 de CU-01 (antes de crear la orden): si el equipo tiene orden activa lanzar `OrdenActivaError` (E01) con el código de la orden activa; traducir también a E01 la violación del índice único parcial por carrera (RN-02); citar `RN-02` en el código (depende de T024)

**Checkpoint**: US1, US2 y US3 funcionan; no existe ningún equipo con dos órdenes activas

---

## Phase 6: User Story 4 - Registrar un cliente nuevo durante la recepción (Priority: P2)

**Goal**: Registrar un cliente en GUI-02 cuando el DNI no existe y, si ya existe, avisar "El DNI ya está registrado" y devolver al cliente existente sin duplicarlo (CU-06; CU-01 cursos 2a y 2b; RN-01).

**Independent Test**: `POST /clientes` con un DNI nuevo responde 201; repetirlo responde 200 con `ya_registrado=true` y el aviso, y existe un único cliente con ese DNI.

**Depends on**: US1 (repositorio y servicio de clientes). Puede avanzar en paralelo con US2/US3 si se coordina la edición de `app/main.py`.

### Tests for User Story 4 ⚠️

- [ ] T026 [P] [US4] Pruebas en `tests/test_cu06_registrar_cliente.py`: `test_cu01_2a_registra_cliente_nuevo_201`, `test_cu01_2a_correo_opcional`, `test_cu01_2a_campos_obligatorios_y_dni_invalido_422`, `test_cu01_2b_dni_existente_avisa_y_carga_cliente` (200, `ya_registrado=true`, aviso "El DNI ya está registrado", equipos del cliente existente), `test_rn01_dni_unico_sin_duplicados` y `test_cu01_2b_doble_guardado_concurrente_no_duplica` (dos solicitudes simultáneas con el mismo DNI: un cliente en la base)

### Implementation for User Story 4

- [ ] T027 [US4] Añadir en `app/repositories/cliente_repository.py` `crear(...)` y la detección de la violación de unicidad de `dni`
- [ ] T028 [US4] Añadir en `app/services/cliente_service.py` `registrar_cliente(datos)`: si el DNI existe devuelve el cliente existente con `ya_registrado=true` y el aviso "El DNI ya está registrado" sin modificar nada (curso 2b); si no, lo crea (curso 2a); ante carrera por unicidad devuelve el cliente ya creado; citar `RN-01` (depende de T027)
- [ ] T029 [US4] Añadir en `app/api/clientes.py` `POST /clientes` con etiqueta `CU-06 · GUI-02` (201 al crear, 200 si ya estaba registrado) y ejecutar `uv run pytest tests/test_cu06_registrar_cliente.py` hasta que pase (depende de T028)

**Checkpoint**: Se puede registrar al cliente nuevo y continuar la recepción

---

## Phase 7: User Story 5 - Reintentar la generación de la orden sin duplicarla (Priority: P2)

**Goal**: Un reintento con el mismo ID OP devuelve la orden ya creada sin duplicarla ni volver a incrementar la cola (CU-01, curso alterno 6a; RN-10; RNF-04), guardando el ID OP de cada operación confirmada junto con su resultado.

**Independent Test**: Enviar dos veces `POST /ordenes` con el mismo `id_op` y datos: la primera 201 y la segunda 200 con `reintento=true`, una sola orden y la cola +1 una sola vez; con datos distintos se rechaza.

**Depends on**: US2 (y US3 para el orden de validaciones).

### Tests for User Story 5 ⚠️

- [ ] T030 [P] [US5] Pruebas en `tests/test_cu01_6a_idempotencia.py`: `test_cu01_6a_reintento_devuelve_misma_orden` (200, `reintento=true`, mismo cuerpo, una sola orden), `test_rn10_reintento_no_incrementa_cola`, `test_rn10_solicitudes_simultaneas_mismo_id_op` (hilos con sesiones independientes: una sola orden y cola +1), `test_rn10_id_op_con_datos_distintos_rechazado` (409 `ID_OP_CONFLICTO`, sin cambios), `test_rn10_fallo_no_registra_id_op` (tras un 409/422 se puede corregir y reintentar con el mismo `id_op`) y `test_rn10_resultado_guardado_se_devuelve_integro`

### Implementation for User Story 5

- [ ] T031 [P] [US5] Implementar `app/repositories/operacion_repository.py`: obtener operación por `id_op` y registrar `id_op`, `operacion`, `huella`, `orden_id` y `resultado` (JSON serializado)
- [ ] T032 [US5] Añadir en `app/services/orden_service.py` la idempotencia (research D5) dentro de la misma transacción de `crear_orden`: al inicio buscar el `id_op` (misma huella SHA-256 de la solicitud normalizada → devolver el resultado guardado con `reintento=true` sin escribir; huella distinta → `IdOpConflicto`); al final, antes de confirmar, registrar el `id_op` con su resultado; solo se registra si la operación se confirma; citar `RN-10` (depende de T031)
- [ ] T033 [US5] Ajustar `app/api/ordenes.py` para responder 201 al crear y 200 en reintento, y ejecutar `uv run pytest tests/test_cu01_6a_idempotencia.py` hasta que pase (depende de T032)

**Checkpoint**: Las cinco historias funcionan y los reintentos no duplican nada

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Cierre de la iteración y verificación de trazabilidad

- [ ] T034 [P] Implementar `app/seed.py` ejecutable con `uv run python -m app.seed`: crea técnicos de demostración de forma idempotente (sin credenciales ni datos personales reales)
- [ ] T035 [P] Prueba `tests/test_trazabilidad_swagger.py`: verifica en el OpenAPI que cada operación de C1 tiene su etiqueta `CU-xx · GUI-xx` y que su descripción cita las `RN-xx` aplicables (principio I)
- [ ] T036 Ejecutar la validación de [quickstart.md](quickstart.md): `uv sync`, `uv run python -m app.seed`, `uv run uvicorn app.main:app --reload`, los cinco escenarios manuales en `/docs` y `uv run pytest` completo; registrar cualquier discrepancia
- [ ] T037 Revisar la cobertura de trazabilidad: confirmar que RN-01, RN-02, RN-03 (solo asignación) y RN-10, y los casos `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a` y `CU-01-6a` tienen al menos una prueba que lleva su código en el nombre; que no hay credenciales en el repositorio y que `docs/aup/` y `.specify/memory/` no fueron modificados (`git status`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **User Stories (Phase 3+)**: dependen de Foundational (ver dependencias entre historias)
- **Polish (Phase 8)**: depende de las historias que se vayan a entregar

### User Story Dependencies

- **US1 (P1)**: tras Foundational; sin dependencias de otras historias
- **US2 (P1)**: tras US1 (usa `cliente_repository` y `cliente_service`)
- **US3 (P1)**: tras US2 (extiende `orden_service` y `orden_repository`)
- **US4 (P2)**: tras US1 (extiende los mismos archivos de clientes); independiente de US2 y US3
- **US5 (P2)**: tras US2 (extiende `orden_service` y `api/ordenes.py`); se recomienda tras US3 para mantener el orden de validaciones

```text
Setup → Foundational → US1 ─┬→ US2 ─┬→ US3
                            │       └→ US5
                            └→ US4
```

### Within Each User Story

- Las pruebas se escriben primero y deben fallar antes de implementar
- Repositorios → servicio → endpoints → registro del router
- Historia completa y con pruebas en verde antes de pasar a la siguiente

### Parallel Opportunities

- Foundational: T005, T006 y T007 en paralelo (tras T004)
- US1: T010 y T011 en paralelo
- US2: T015, T016, T017 y T018 en paralelo; luego T020 y T021 en paralelo (tras T019)
- US4 puede ejecutarse en paralelo con US2/US3 (archivos distintos salvo `app/main.py`)
- Polish: T034 y T035 en paralelo

---

## Parallel Example: User Story 2

```bash
# Pruebas y repositorios de US2 en paralelo (archivos distintos):
Task: "Pruebas en tests/test_cu01_registrar_orden.py"
Task: "Repositorio en app/repositories/equipo_repository.py"
Task: "Repositorio en app/repositories/tecnico_repository.py"
Task: "Repositorio en app/repositories/orden_repository.py"

# Tras orden_service (T019), los endpoints en paralelo:
Task: "GET /tecnicos/disponibles en app/api/tecnicos.py"
Task: "POST /ordenes y GET /ordenes/costo-revision-inicial en app/api/ordenes.py"
```

---

## Implementation Strategy

### MVP First

1. Completar Phase 1 (Setup) y Phase 2 (Foundational)
2. Completar US1 (Buscar cliente) y validarla: es el primer incremento demostrable
3. Completar US2 y US3 (ambas P1): con ellas la recepción ya es utilizable y cumple "una sola orden activa por equipo"; este es el **MVP funcional de C1**
4. **PARAR y VALIDAR** con `uv run pytest` y el quickstart

### Incremental Delivery

1. Setup + Foundational → base lista
2. US1 → probar → US2 → probar → US3 → probar (MVP)
3. US4 (cliente nuevo) → probar
4. US5 (idempotencia) → probar
5. Polish → validar quickstart y trazabilidad

### Alcance (principio VII)

Fuera de C1: autenticación OAuth2/JWT, CU-02, CU-03, CU-04, CU-07 y CU-08. Pendientes registrados en el spec: RNF-01, RNF-02, RNF-03, RN-03 (parte de acceso) y RN-04 a RN-09 y RN-11. No crear tareas para ellos en esta iteración.

---

## Notes

- [P] = archivos distintos y sin dependencias pendientes
- La etiqueta [Story] vincula cada tarea con su historia para trazabilidad
- Cada endpoint declara su `CU-xx` y cada validación cita su `RN-xx` (AGENTS.md reglas 2 y 3)
- Verificar que las pruebas fallan antes de implementar; commit tras cada tarea o grupo lógico
- No incluir credenciales; la configuración va en variables de entorno
