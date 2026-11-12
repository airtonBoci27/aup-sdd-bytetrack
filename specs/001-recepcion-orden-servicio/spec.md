# Feature Specification: Recepción de equipos y registro de orden de servicio (Iteración C1)

**Feature Branch**: `001-recepcion-orden-servicio`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Crea la especificación de la iteración C1 de ByteTrack a partir de docs/aup/caso.md. Alcance: CU-05 Buscar cliente, CU-06 Registrar nuevo cliente y CU-01 Registrar orden de servicio, con su curso básico y los cursos alternos 2a, 2b, 5a y 6a de la narrativa de CU-01. Reglas en alcance: RN-01, RN-02, RN-03 (solo la asignación a un técnico disponible) y RN-10. Fuera de alcance: autenticación OAuth2/JWT y CU-02, CU-03, CU-04, CU-07 y CU-08. RNF: solo aplica la idempotencia (RNF-04), cubierta por RN-10; RNF-01, RNF-02 y RNF-03 se registran como pendientes."

**Fuente de verdad**: `docs/aup/caso.md` (visión 2.1, reglas de negocio 2.2, narrativa de CU-01, prototipos GUI-01/GUI-02 y plan de la iteración C1 en 4.1). Los códigos CU, RN, E01, GUI-01 y GUI-02 se conservan tal cual.

## Contexto

ByteFix Lab pasó de 8 a 30 equipos diarios y gestiona las órdenes con talonario, hojas de cálculo y mensajes, lo que provoca pérdida de trazabilidad y órdenes duplicadas por equipo. El objetivo de producto relevante para esta iteración es **una sola orden activa por equipo**, con trazabilidad de cada equipo por estado.

La iteración C1 entrega la **recepción funcional** mediante GUI-01 (Recepción y orden de servicio) y GUI-02 (Modal de registro de cliente): el Recepcionista identifica o registra al cliente, recibe el equipo y genera una orden de servicio asignada a un técnico disponible. Los reintentos no duplican órdenes ni incrementan nuevamente la cola del técnico.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar cliente por DNI y cargar sus equipos (Priority: P1)

El Recepcionista abre la pantalla de recepción (GUI-01), ingresa el DNI de 8 dígitos del cliente y presiona "Buscar cliente" (CU-05). El sistema muestra los datos del cliente (nombres, apellidos y teléfono) y carga en el selector los equipos que ese cliente ya tiene registrados.

**Why this priority**: Es el punto de entrada de toda recepción (CU-01 incluye a CU-05). Sin identificar al cliente no se puede registrar ninguna orden. Es de riesgo bajo y entrega valor por sí sola: el taller deja de buscar clientes en hojas de cálculo.

**Independent Test**: Con clientes y equipos precargados, buscar un DNI existente y verificar que se muestran sus datos y su lista de equipos; buscar un DNI inexistente y verificar que se habilita "Registrar nuevo cliente".

**Acceptance Scenarios**:

1. **Given** un cliente registrado con DNI de 8 dígitos y dos equipos, **When** el Recepcionista busca ese DNI en GUI-01, **Then** el sistema muestra nombres, apellidos y teléfono del cliente y carga sus dos equipos en el selector.
2. **Given** un cliente registrado sin equipos, **When** el Recepcionista busca su DNI, **Then** el sistema muestra sus datos y el selector de equipos queda vacío, permitiendo ingresar un equipo nuevo.
3. **Given** un DNI que no existe en el sistema, **When** el Recepcionista presiona "Buscar cliente", **Then** el sistema habilita la acción "Registrar nuevo cliente" (CU-06).
4. **Given** un valor que no cumple el formato de 8 dígitos numéricos, **When** el Recepcionista intenta buscar, **Then** el sistema rechaza la búsqueda e indica que el DNI debe tener 8 dígitos (RN-01).

---

### User Story 2 - Registrar una orden de servicio para un equipo sin orden activa (Priority: P1)

Con el cliente identificado, el Recepcionista selecciona un equipo existente o ingresa los datos de uno nuevo (tipo, marca, modelo y número de serie), marca los accesorios dejados, describe el estado físico al ingreso, registra la falla reportada, selecciona un técnico disponible, verifica el costo de revisión inicial y presiona "Generar orden de servicio" (CU-01, curso básico). El sistema registra la orden en estado RECEPCIONADO, suma 1 a la cola del técnico asignado y muestra el código de orden listo para imprimir.

**Why this priority**: Es el resultado central de la iteración y la base de las iteraciones siguientes (C2 usa las órdenes registradas en C1). Materializa RN-01, RN-02 y RN-03.

**Independent Test**: Con un cliente existente y al menos un técnico disponible, completar el formulario con un equipo sin orden previa y verificar que se genera una orden RECEPCIONADO con código único, asignada al técnico elegido, con su cola incrementada en 1.

**Acceptance Scenarios**:

1. **Given** un cliente existente, un equipo registrado sin órdenes activas y un técnico disponible, **When** el Recepcionista completa los datos obligatorios y presiona "Generar orden de servicio", **Then** el sistema crea la orden en estado RECEPCIONADO, la asigna al técnico seleccionado, incrementa en 1 su cola y muestra el código de orden listo para imprimir.
2. **Given** un cliente existente, **When** el Recepcionista ingresa un equipo nuevo con tipo, marca, modelo y número de serie no registrado, **Then** el sistema registra el equipo asociado a ese cliente y genera la orden (el cliente puede tener varios equipos, RN-01).
3. **Given** que faltan campos obligatorios (equipo, número de serie, falla reportada, estado físico o técnico), **When** el Recepcionista presiona "Generar orden de servicio", **Then** el sistema no crea la orden e indica los campos faltantes.
4. **Given** una lista de técnicos de la que solo algunos están disponibles, **When** el Recepcionista abre el selector de técnico, **Then** solo se ofrecen técnicos disponibles y la orden solo puede asignarse a uno de ellos (RN-03, asignación).
5. **Given** que no existe ningún técnico disponible, **When** el Recepcionista intenta generar la orden, **Then** el sistema no crea la orden y comunica que no hay técnicos disponibles.

---

### User Story 3 - Impedir una segunda orden para un equipo con orden activa (Priority: P1)

Si el número de serie del equipo ya posee una orden con estado distinto de ENTREGADO, el sistema bloquea el registro y muestra la alerta **E01** en GUI-01: "Este número de serie ya posee la Orden activa N.° [X] en laboratorio" (CU-01, curso alterno 5a; RN-02).

**Why this priority**: Es el objetivo de negocio principal ("una sola orden activa por equipo") y evita las duplicaciones que hoy sufre el taller. Debe cumplirse desde la primera versión funcional.

**Independent Test**: Registrar una orden para un equipo y, sin entregarlo, intentar registrar otra con el mismo número de serie; verificar que se muestra E01 con el número de la orden activa y que no se crea ninguna orden nueva ni se altera la cola del técnico.

**Acceptance Scenarios**:

1. **Given** un equipo con una orden en estado RECEPCIONADO (o cualquier estado distinto de ENTREGADO), **When** el Recepcionista intenta generar otra orden con el mismo número de serie, **Then** el sistema bloquea el registro y muestra E01 con el N.° de la orden activa.
2. **Given** un equipo cuya única orden anterior está en estado ENTREGADO, **When** el Recepcionista genera una nueva orden, **Then** el sistema la registra normalmente.
3. **Given** que el registro fue bloqueado por E01, **When** se consulta la cola del técnico seleccionado, **Then** su valor no cambió.

---

### User Story 4 - Registrar un cliente nuevo durante la recepción (Priority: P2)

Cuando el DNI no existe, el Recepcionista abre el modal GUI-02, ingresa DNI, nombres, apellidos, teléfono y correo (opcional) y presiona "Guardar cliente" (CU-06, curso alterno 2a de CU-01). El sistema registra al cliente y regresa al paso de selección de equipo en GUI-01 con los datos cargados. Si el DNI ya estaba registrado, avisa "El DNI ya está registrado" y carga al cliente existente sin duplicarlo (curso alterno 2b).

**Why this priority**: Permite atender a clientes nuevos sin salir del flujo de recepción, pero la mayoría de las recepciones recurrentes usan clientes existentes; por eso es P2 respecto de las historias anteriores.

**Independent Test**: Buscar un DNI inexistente, abrir GUI-02, guardar el cliente y verificar que queda registrado con DNI único y que GUI-01 muestra sus datos; repetir el guardado con el mismo DNI y verificar el aviso y la ausencia de duplicados.

**Acceptance Scenarios**:

1. **Given** un DNI inexistente y GUI-02 abierto, **When** el Recepcionista ingresa DNI, nombres, apellidos y teléfono válidos y presiona "Guardar cliente", **Then** el sistema registra al cliente y regresa a GUI-01 con sus datos cargados, listo para registrar el equipo.
2. **Given** que el Recepcionista omite el correo, **When** guarda el cliente, **Then** el registro se completa (el correo es opcional).
3. **Given** un DNI ya registrado, **When** el Recepcionista intenta guardarlo en GUI-02, **Then** el sistema muestra "El DNI ya está registrado", carga al cliente existente en GUI-01 y no crea un segundo cliente con ese DNI (RN-01).
4. **Given** datos obligatorios faltantes o un DNI con formato inválido en GUI-02, **When** presiona "Guardar cliente", **Then** el sistema no registra al cliente e indica cada campo a corregir.

---

### User Story 5 - Reintentar la generación de la orden sin duplicarla (Priority: P2)

Si la solicitud de generar la orden se repite con el mismo identificador de operación (ID OP), por doble clic, fallo de red o reenvío, el sistema devuelve la orden ya creada sin duplicar el registro ni incrementar nuevamente la cola del técnico (CU-01, curso alterno 6a; RN-10; RNF-04).

**Why this priority**: Protege la integridad de los datos frente a reintentos (riesgo R2 de la lista de riesgos), pero se apoya en que el registro básico ya existe.

**Independent Test**: Enviar dos veces la misma solicitud de generación con el mismo ID OP y verificar que existe una sola orden, que ambas respuestas devuelven la misma orden y que la cola del técnico aumentó solo en 1.

**Acceptance Scenarios**:

1. **Given** una orden ya creada con un ID OP, **When** se repite la solicitud con el mismo ID OP y los mismos datos, **Then** el sistema devuelve la orden ya creada, sin crear otra ni volver a incrementar la cola del técnico.
2. **Given** dos envíos simultáneos con el mismo ID OP, **When** ambos se procesan, **Then** existe una sola orden y la cola del técnico aumentó una sola vez.
3. **Given** un ID OP ya utilizado, **When** se envía una solicitud con ese mismo ID OP pero con datos distintos, **Then** el sistema rechaza la solicitud y no modifica órdenes ni colas.

---

### Edge Cases

- ¿Qué ocurre si el Recepcionista selecciona un equipo existente cuyo número de serie ya tiene una orden activa? Se aplica el curso 5a: bloqueo y alerta E01 (RN-02).
- ¿Qué ocurre si ingresa un equipo nuevo con un número de serie que ya está registrado (por ejemplo, en otro cliente)? El número de serie es único en el sistema (RN-01): no se duplica el equipo; la solicitud se rechaza con un mensaje claro, sin crear la orden.
- ¿Qué ocurre si el DNI tiene menos o más de 8 dígitos, o contiene caracteres no numéricos? Se rechaza en CU-05 y en CU-06 (RN-01).
- ¿Qué ocurre si dos Recepcionistas intentan registrar al mismo tiempo órdenes para el mismo número de serie? Solo una orden queda registrada; la otra recibe la alerta E01 (RN-02).
- ¿Qué ocurre si el técnico seleccionado deja de estar disponible entre su selección y la confirmación? No se crea la orden y se solicita seleccionar otro técnico disponible (RN-03).
- ¿Qué ocurre si falla el registro a mitad de operación? No quedan datos parciales: ni equipo nuevo sin orden asociada por esa misma operación, ni cola incrementada sin orden.
- ¿Qué ocurre si el mismo cliente se guarda dos veces en GUI-02 por doble clic? Se aplica el curso 2b: no se duplica.

## Requirements *(mandatory)*

### Functional Requirements

**Buscar cliente (CU-05)**

- **FR-001**: El sistema MUST permitir buscar un cliente por DNI desde GUI-01 y mostrar sus nombres, apellidos y teléfono (CU-05).
- **FR-002**: El sistema MUST validar que el DNI sea un valor numérico de exactamente 8 dígitos antes de buscar o registrar (RN-01).
- **FR-003**: El sistema MUST cargar en el selector de GUI-01 los equipos previamente registrados del cliente encontrado (CU-01 paso 2; RN-01: un cliente puede tener varios equipos).
- **FR-004**: Cuando el DNI no exista, el sistema MUST habilitar la acción "Registrar nuevo cliente" (CU-01 curso 2a).

**Registrar nuevo cliente (CU-06)**

- **FR-005**: El sistema MUST ofrecer en GUI-02 el registro de un cliente con DNI, nombres, apellidos, teléfono y correo opcional (CU-06).
- **FR-006**: El sistema MUST garantizar que el DNI de cada cliente sea único (RN-01).
- **FR-007**: Si el DNI ingresado en GUI-02 ya está registrado, el sistema MUST mostrar el aviso "El DNI ya está registrado" y cargar al cliente existente sin crear un duplicado (CU-01 curso 2b).
- **FR-008**: Tras guardar un cliente nuevo, el sistema MUST regresar a GUI-01 con los datos del cliente cargados y continuar en la selección o ingreso del equipo (CU-01 curso 2a).

**Registrar orden de servicio (CU-01)**

- **FR-009**: El sistema MUST permitir seleccionar un equipo existente del cliente o ingresar uno nuevo con tipo, marca, modelo y número de serie, además de los accesorios dejados y el estado físico al ingreso (CU-01 paso 3).
- **FR-010**: El sistema MUST garantizar que cada equipo tenga un número de serie único y esté asociado a un cliente (RN-01).
- **FR-011**: El sistema MUST permitir registrar la falla reportada, mostrar el costo de revisión inicial para su verificación y requerir la selección de un técnico (CU-01 paso 4).
- **FR-012**: El sistema MUST ofrecer para la asignación únicamente técnicos disponibles y MUST rechazar la asignación a un técnico no disponible (RN-03, solo asignación).
- **FR-013**: El sistema MUST validar los campos obligatorios antes de crear la orden e indicar cuáles faltan (CU-01 paso 5).
- **FR-014**: El sistema MUST verificar que el número de serie no tenga otra orden con estado distinto de ENTREGADO antes de crear una nueva (CU-01 paso 5; RN-02).
- **FR-015**: Cuando el número de serie tenga una orden activa, el sistema MUST bloquear el registro y mostrar en GUI-01 la alerta E01: "Este número de serie ya posee la Orden activa N.° [X] en laboratorio", con el número de la orden activa (CU-01 curso 5a).
- **FR-016**: El sistema MUST registrar la orden de servicio en estado RECEPCIONADO con un código de orden único y mostrarlo listo para imprimir (CU-01 paso 6).
- **FR-017**: El sistema MUST incrementar en 1 la cola del técnico asignado al crear la orden (CU-01 paso 6; RN-03).
- **FR-018**: El registro de la orden, del equipo nuevo (si lo hay) y el incremento de la cola MUST confirmarse como una unidad: si alguna parte falla, no se conserva ninguna (todo o nada).

**Idempotencia (RN-10, RNF-04)**

- **FR-019**: Cada solicitud de generación de orden MUST incluir un identificador de operación (ID OP), visible en el pie de la operación en GUI-01 (RN-10).
- **FR-020**: Si la solicitud se repite con el mismo ID OP y los mismos datos, el sistema MUST devolver la orden ya creada sin duplicar la orden ni incrementar nuevamente la cola del técnico (CU-01 curso 6a; RN-10).
- **FR-021**: Si un ID OP ya utilizado llega con datos distintos, el sistema MUST rechazar la solicitud sin modificar órdenes ni colas.

### Key Entities *(include if feature involves data)*

- **Cliente**: persona que entrega equipos al taller. Se identifica por DNI único de 8 dígitos; tiene nombres, apellidos, teléfono y correo opcional. Puede tener varios equipos (RN-01).
- **Equipo**: dispositivo del cliente, con tipo, marca, modelo y número de serie único (RN-01). Pertenece a un cliente.
- **Técnico**: persona de laboratorio a quien se asigna la orden. Tiene una condición de disponibilidad y una cola de órdenes asignadas que aumenta en 1 con cada orden nueva (RN-03).
- **Orden de servicio**: registro de la recepción de un equipo. Tiene código único, estado (RECEPCIONADO al crearse), cliente y equipo, accesorios dejados, estado físico al ingreso, falla reportada, costo de revisión inicial, técnico asignado y el ID OP con el que se creó. Un equipo solo puede tener una orden con estado distinto de ENTREGADO (RN-02).
- **Operación idempotente**: asociación entre un ID OP y el resultado de la operación (la orden creada), que permite devolver el mismo resultado ante reintentos (RN-10).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un Recepcionista completa la recepción de un equipo de un cliente ya registrado, desde la búsqueda del DNI hasta ver el código de orden, en menos de 3 minutos.
- **SC-002**: El 100 % de los intentos de registrar una orden para un número de serie con orden activa son bloqueados y muestran E01; no existe ningún equipo con dos órdenes activas.
- **SC-003**: El 100 % de las órdenes creadas queda asignado a un técnico disponible y la cola de cada técnico coincide con el número de órdenes que se le asignaron.
- **SC-004**: Repetir cualquier solicitud de generación de orden con el mismo ID OP, incluidos envíos simultáneos, produce cero órdenes duplicadas y cero incrementos adicionales de cola.
- **SC-005**: No existen dos clientes con el mismo DNI ni dos equipos con el mismo número de serie tras cualquier secuencia de registros, incluidos los reintentos y los guardados repetidos de GUI-02.
- **SC-006**: Cada regla de negocio en alcance (RN-01, RN-02, RN-03 en su parte de asignación y RN-10) y cada caso de prueba de la sección Trazabilidad cuenta con una prueba automatizada que pasa al cierre de la iteración.

## Assumptions

- **Autenticación**: dentro de C1 la precondición "sesión iniciada" de CU-01 se consideró satisfecha y el actor se asumió como Recepcionista. *Actualizado:* la funcionalidad [`002-interfaz-recepcion-rol`](../002-interfaz-recepcion-rol/spec.md) implementa el inicio de sesión y el acceso por rol (RNF-02) sobre las operaciones de esta iteración; las reglas de negocio de C1 no cambian.
- **Técnicos preexistentes**: los técnicos y su condición de disponibilidad existen como datos previos y se asumen cargados. "Disponible" significa que el técnico está marcado como disponible; la gestión de esa condición no pertenece a esta iteración. La precondición de CU-01 exige al menos un técnico disponible.
- **Costo de revisión inicial**: es un importe predefinido que se muestra al Recepcionista para su verificación; no se edita en la recepción. Su monto no está fijado en la documentación (el valor de S/ 40 de RN-11 es una propuesta sin aprobar y RN-11 está fuera de alcance), por lo que el monto se toma de la configuración del taller.
- **Campos obligatorios**: DNI, nombres, apellidos y teléfono del cliente; tipo, marca, modelo y número de serie del equipo; estado físico al ingreso; falla reportada; y técnico. Son opcionales el correo del cliente y los accesorios dejados.
- **Narrativas de CU-05 y CU-06**: la documentación no incluye narrativas propias para ellos; su comportamiento se toma de los pasos 1 y 2 y de los cursos 2a y 2b de CU-01 y de los prototipos GUI-01 y GUI-02.
- **Unicidad del número de serie**: es único en todo el sistema (RN-01); ingresar un equipo nuevo con un número de serie ya registrado no crea un segundo equipo.
- **ID OP con datos distintos**: el rechazo de un ID OP reutilizado con datos diferentes se toma del diseño de idempotencia del documento (el resultado anterior solo se devuelve si los datos coinciden).
- **Impresión**: "listo para imprimir" significa que el código de orden se presenta en una vista imprimible; la impresión en sí no es parte de la iteración.
- **Datos**: el almacenamiento es local y los servicios externos (pagos, facturación, correo) no intervienen en esta iteración (constitución, principio V).

## Alcance y Pendientes

**En alcance (C1)**: CU-05, CU-06 y CU-01 (curso básico y cursos alternos 2a, 2b, 5a y 6a); pantallas GUI-01 y GUI-02; alerta E01; reglas RN-01, RN-02, RN-03 (solo la asignación a un técnico disponible) y RN-10; RNF-04 (idempotencia) a través de RN-10.

**Fuera de alcance en esta iteración**: autenticación OAuth2/JWT (incorporada después por la funcionalidad 002, que protege las operaciones de recepción); CU-02, CU-03, CU-04, CU-07 y CU-08, junto con sus pantallas y alertas (GUI-03 a GUI-06, E02).

**Pendientes registrados (principio VII de la constitución)**:

| Código | Descripción | Iteración prevista |
|--------|-------------|--------------------|
| RNF-01 | Reserva atómica de repuestos sobre stock libre | C2 (CU-02) |
| RNF-02 | Seguridad: autenticación OAuth2/JWT y reglas aplicadas directamente en la API | Parcialmente cubierto por la funcionalidad 002 (acceso por rol a CU-01, CU-05 y CU-06); la parte restante (decisión, cobro, diagnóstico y finalización) llega con CU-02 a CU-08 |
| RNF-03 | Rendimiento: p95 ≤ 1 s con 5 sesiones concurrentes | Pendiente de planificar |
| RN-03 (parte de acceso) | El técnico solo accede a sus órdenes asignadas | Pendiente (la autenticación ya existe por 002; falta el acceso del Técnico a sus órdenes, desde C2) |
| RN-04 a RN-09, RN-11 | Reglas de presupuesto, decisión, reparación, cobro, transacción de entrega y cobro de revisión | C2 a C4 según la lista de trabajo |

## Trazabilidad

Los casos de prueba usan la convención `CU-xx-<curso>` de la constitución y la numeración de la narrativa de CU-01. CU-05 y CU-06 no tienen narrativa propia (ver Assumptions): sus escenarios se prueban a través de los pasos 1–2 y de los cursos 2a y 2b de CU-01.

| Caso de prueba | Curso | Historia | Reglas | Alerta / pantalla |
|----------------|-------|----------|--------|-------------------|
| CU-01-B | Curso básico (incluye CU-05) | US1, US2 | RN-01, RN-02, RN-03 | GUI-01 |
| CU-01-2a | El DNI no existe (CU-06) | US1, US4 | RN-01 | GUI-01, GUI-02 |
| CU-01-2b | DNI ya registrado en el modal (CU-06) | US4 | RN-01 | GUI-02 |
| CU-01-5a | El equipo ya tiene una orden activa | US3 | RN-02 | E01 en GUI-01 |
| CU-01-6a | Reintento de confirmación (ID OP) | US5 | RN-10 (RNF-04) | GUI-01 |

### Elementos de diseño con origen indirecto

Cada elemento que no figura literalmente en la narrativa de CU-01 se traza aquí a su origen en `docs/aup/`.

| Elemento | Origen en `docs/aup/` | Notas |
|----------|----------------------|-------|
| Código de orden `OS-AAAA-NNNN` | GUI-01 (ejemplo `OS-2026-0146`) | Año de la recepción y correlativo de 4 dígitos que se reinicia cada año |
| Monto de revisión 40.00 (valor por defecto) | GUI-01 («Costo de revisión S/ 40.00») y RN-11 | RN-11 es una propuesta sin aprobar y está fuera de alcance; el monto se toma de la configuración |
| `huella` (SHA-256) de la operación idempotente | RNF-04 y sección 3.7.2 (Liquidación e idempotencia, E2) | Detecta un ID OP reutilizado con datos distintos |
| `reintento` en la respuesta de la orden | RNF-04 y sección 3.7.2 | Indica que la respuesta proviene de un reintento (CU-01 curso 6a) |
| Estados `PRESUPUESTADO`, `APROBADO`, `RECHAZADO`, `LISTO` | Modelo de dominio (estados de la orden) | C1 solo crea `RECEPCIONADO`; los demás pertenecen a casos de uso fuera de alcance |
| `app/seed.py` (técnicos de demostración) | Datos iniciales de la fase de Transición | Solo datos ficticios; no es funcionalidad de C1 |
| Esquema de error `{codigo, mensaje, detalle}` | CU-01 curso 5a (alerta E01) | Una forma uniforme de entregar la alerta E01 y los demás rechazos |

Elementos con origen propuesto por el agente, **pendientes de confirmar** por el usuario:

| Elemento | Origen propuesto | Notas |
|----------|------------------|-------|
| `equipos` en la respuesta de `POST /clientes` | CU-01 curso 2b: «carga el cliente existente» y retorna al paso 3 | |
| `accesorios` opcional | CU-01 paso 3 y casillas de accesorios de GUI-01 | El AUP no dice si es obligatorio |
| Código de error `EQUIPO_NO_ENCONTRADO` | CU-01 paso 3 (selección de un equipo existente del cliente) | |
| Variables de entorno `BYTETRACK_DB_PATH` y `BYTETRACK_COSTO_REVISION` | Constitución, principio VI; CU-01 paso 4 | |
