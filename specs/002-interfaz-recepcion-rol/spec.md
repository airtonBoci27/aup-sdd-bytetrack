# Feature Specification: Interfaz web de recepción con acceso por rol (Iteración C1)

**Feature Branch**: `002-interfaz-recepcion-rol`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Crea la interfaz web de recepción de la iteración C1 con acceso por rol. (1) Acceso (RNF-02): inicio de sesión; las operaciones de recepción (CU-01, CU-05, CU-06) exigen sesión activa con rol Recepcionista; un usuario con rol Técnico recibe un rechazo. (2) Interfaz según los prototipos GUI-01 y GUI-02 de docs/aup/caso.md (imágenes en docs/aup/img): búsqueda de cliente por DNI, modal de registro de cliente, datos del equipo, falla, técnico disponible, costo de revisión, alerta E01 e ID de operación. Consume la API existente sin cambiar sus reglas. No agregues nada que no se trace a RF-01, RF-02, RNF-02, RNF-04 o a esos prototipos: ni listados, ni edición, ni reportes, ni gestión de usuarios."

**Fuente de verdad**: `docs/aup/caso.md` (narrativa de CU-01, prototipos GUI-01 y GUI-02 de la sección 3.2 con sus imágenes `image7.png` e `image10.png`, riesgo R3 de la sección 2.4 y reglas de negocio 2.2). Los códigos CU, RN, RF, RNF, E01, GUI-01 y GUI-02 se conservan tal cual.

## Contexto

La iteración C1 ya dispone de las operaciones de recepción (buscar cliente, registrar cliente, listar técnicos disponibles, consultar el costo de revisión y generar la orden de servicio; ver `specs/001-recepcion-orden-servicio/`), pero hoy solo se usan a través de la documentación Swagger y sin control de acceso. La documentación AUP identifica ese hueco como el riesgo R3 («Las reglas se saltan llamando a la API o un técnico ve órdenes ajenas», mitigado por RNF-02) y la precondición de CU-01 exige «sesión iniciada».

Esta funcionalidad entrega a la Recepcionista la **pantalla de recepción (GUI-01) y el modal de registro de cliente (GUI-02)** tal como los muestran los prototipos, y protege las operaciones de recepción con **inicio de sesión y acceso por rol**: solo un usuario con rol Recepcionista y sesión activa puede usarlas; un usuario con rol Técnico es rechazado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar sesión y acceder según el rol (Priority: P1)

Una persona abre la aplicación, ingresa su usuario y contraseña y, si son válidos, el sistema abre una sesión. Si el rol es Recepcionista, se muestra la pantalla de recepción (GUI-01) con la indicación «Recepcionista · sesión activa». Si el rol es Técnico, el sistema no le da acceso a la recepción y muestra un rechazo claro. Sin sesión activa, ninguna operación de recepción responde con datos ni crea nada (RNF-02; precondición de CU-01).

**Why this priority**: Es la precondición de CU-01 («sesión iniciada») y la mitigación del riesgo R3. Sin ella, la interfaz queda abierta a cualquiera y el rol no se hace cumplir; además es la puerta de entrada a las demás historias.

**Independent Test**: Con un usuario Recepcionista y uno Técnico preexistentes, iniciar sesión con cada uno y verificar que solo el primero llega a GUI-01; invocar cada operación de recepción sin sesión, con sesión de Técnico y con sesión de Recepcionista, y verificar el rechazo en los dos primeros casos y el funcionamiento en el tercero.

**Acceptance Scenarios**:

1. **Given** un usuario con rol Recepcionista y credenciales válidas, **When** inicia sesión, **Then** el sistema muestra GUI-01 con «Recepcionista · sesión activa».
2. **Given** credenciales incorrectas, **When** intenta iniciar sesión, **Then** el sistema no abre sesión y muestra un mensaje de credenciales inválidas, sin indicar cuál de los dos datos falló.
3. **Given** un usuario con rol Técnico y credenciales válidas, **When** inicia sesión o intenta usar una operación de recepción (CU-01, CU-05, CU-06), **Then** el sistema la rechaza con un mensaje de acceso no permitido para su rol, sin devolver datos ni crear registros.
4. **Given** que no hay sesión activa (nunca se inició, caducó o es inválida), **When** se intenta abrir GUI-01 o usar cualquier operación de recepción, **Then** el sistema rechaza la operación y solo ofrece el inicio de sesión.
5. **Given** una sesión de Recepcionista activa, **When** usa buscar cliente, registrar cliente, listar técnicos disponibles, consultar el costo de revisión y generar la orden, **Then** todas las operaciones responden con normalidad.

---

### User Story 2 - Buscar un cliente por DNI y cargar sus equipos en GUI-01 (Priority: P1)

En GUI-01, sección «1. Cliente (CU-05)», la Recepcionista ingresa el DNI de 8 dígitos y presiona «Buscar cliente». El sistema muestra nombres, apellidos y teléfono con la marca «Cliente encontrado» y carga en el selector «Equipos del cliente» los equipos previamente registrados. El botón «Registrar nuevo cliente» solo se habilita si el DNI no existe.

**Why this priority**: Es el primer paso de toda recepción (CU-01 incluye a CU-05) y entrega valor por sí sola: el taller deja de buscar clientes en hojas de cálculo.

**Independent Test**: Con un cliente de dos equipos y un DNI inexistente, buscar ambos DNI en GUI-01 y verificar los datos y el selector en el primer caso y la habilitación de «Registrar nuevo cliente» en el segundo; ingresar un valor que no son 8 dígitos y verificar el mensaje.

**Acceptance Scenarios**:

1. **Given** un cliente registrado con dos equipos, **When** la Recepcionista busca su DNI, **Then** GUI-01 muestra nombres, apellidos, teléfono y «Cliente encontrado», y el selector lista sus dos equipos (CU-01 pasos 1-2).
2. **Given** un cliente registrado sin equipos, **When** lo busca, **Then** se muestran sus datos y el selector solo permite ingresar un equipo nuevo.
3. **Given** un DNI inexistente, **When** presiona «Buscar cliente», **Then** GUI-01 informa que el cliente no existe y habilita «Registrar nuevo cliente» (CU-01 curso 2a).
4. **Given** un valor que no son 8 dígitos numéricos, **When** intenta buscar, **Then** GUI-01 indica que el DNI debe tener 8 dígitos y no consulta (RN-01).
5. **Given** un cliente encontrado, **When** el DNI en pantalla cambia, **Then** los datos del cliente y los equipos cargados dejan de mostrarse hasta una nueva búsqueda, de modo que no se pueda generar una orden con un DNI distinto del buscado.

---

### User Story 3 - Generar la orden de servicio desde GUI-01 (Priority: P1)

Con el cliente cargado, la Recepcionista completa la sección «2. Equipo (RF-01 / RF-02)» (equipo existente o nuevo con tipo, marca, modelo y número de serie, accesorios dejados y estado físico al ingreso) y la sección «3. Orden de servicio» (falla reportada, técnico disponible y costo de revisión), y presiona «Generar orden de servicio» (CU-01, curso básico). GUI-01 muestra la confirmación con el N.° de orden listo para imprimir.

**Why this priority**: Es el resultado central de la iteración y la razón de la interfaz.

**Independent Test**: Con un cliente existente y un técnico disponible, completar el formulario con un equipo sin orden activa, generar la orden y verificar que GUI-01 muestra el N.° de orden y que el estado inicial indicado es RECEPCIONADO; repetir con campos obligatorios vacíos y verificar que no se genera y que se indican cuáles faltan.

**Acceptance Scenarios**:

1. **Given** un cliente cargado, un equipo existente seleccionado, falla, estado físico y un técnico disponible elegido, **When** presiona «Generar orden de servicio», **Then** GUI-01 muestra «N.° OS-AAAA-NNNN listo para imprimir» y que el técnico recibe +1 en su cola, y el flujo de estados resalta «Recepcionado».
2. **Given** que la Recepcionista elige ingresar un equipo nuevo, **When** completa tipo, marca, modelo y número de serie y genera la orden, **Then** se registra el equipo del cliente y se genera la orden (RN-01).
3. **Given** que falta algún campo obligatorio (equipo, estado físico, falla o técnico), **When** presiona «Generar orden de servicio», **Then** no se envía la orden y GUI-01 señala cada campo faltante.
4. **Given** el selector de técnico, **When** se abre, **Then** solo ofrece técnicos disponibles (RN-03, asignación); si no hay ninguno, GUI-01 lo comunica y no permite generar la orden.
5. **Given** que el técnico elegido dejó de estar disponible o el número de serie nuevo ya pertenece a otro cliente, **When** presiona «Generar orden de servicio», **Then** GUI-01 muestra el motivo de rechazo y no se genera la orden.
6. **Given** el formulario completo, **When** la Recepcionista presiona «Cancelar», **Then** GUI-01 descarta lo ingresado y vuelve a su estado inicial sin generar ninguna orden.

---

### User Story 4 - Ver la alerta E01 cuando el equipo ya tiene una orden activa (Priority: P1)

Si el número de serie ya posee una orden con estado distinto de ENTREGADO, GUI-01 bloquea la generación y muestra la alerta **E01**: «Este número de serie ya posee la Orden activa N.° [X] en laboratorio» (CU-01, curso alterno 5a; RN-02).

**Why this priority**: Materializa el objetivo principal del negocio («una sola orden activa por equipo») en la pantalla que usa la Recepcionista.

**Independent Test**: Generar una orden para un equipo y, sin entregarlo, intentar generar otra con el mismo número de serie; verificar que GUI-01 muestra E01 con el N.° de la primera orden y que no se genera una segunda.

**Acceptance Scenarios**:

1. **Given** un equipo con una orden activa, **When** la Recepcionista intenta generar otra orden para ese número de serie, **Then** GUI-01 muestra E01 con el N.° de la orden activa y no genera la orden.
2. **Given** que E01 está visible, **When** la Recepcionista cambia de equipo o corrige los datos, **Then** la alerta deja de mostrarse y puede volver a intentar.
3. **Given** un equipo cuya orden anterior está ENTREGADA, **When** genera una nueva orden, **Then** no aparece E01 y la orden se genera.

---

### User Story 5 - Registrar un cliente nuevo desde el modal GUI-02 (Priority: P2)

Cuando el DNI no existe, la Recepcionista abre el modal GUI-02 («Registrar nuevo cliente · CU-06»), ingresa DNI, nombres, apellidos, teléfono y correo (opcional) y presiona «Guardar cliente». El modal se cierra y GUI-01 queda con el cliente cargado, listo para registrar el equipo (CU-01 curso 2a). Si el DNI ya estaba registrado, el modal avisa «El DNI ya está registrado» y GUI-01 carga al cliente existente sin duplicarlo (curso 2b).

**Why this priority**: Permite atender a clientes nuevos sin salir del flujo, pero la mayoría de las recepciones usan clientes existentes.

**Independent Test**: Buscar un DNI inexistente, abrir GUI-02, guardar un cliente válido y verificar que GUI-01 lo muestra cargado; repetir el guardado con el mismo DNI y verificar el aviso y que no se crea un segundo cliente; probar campos faltantes y «Cancelar».

**Acceptance Scenarios**:

1. **Given** un DNI inexistente buscado en GUI-01, **When** la Recepcionista abre el modal, **Then** el campo DNI aparece con el DNI buscado y el modal muestra los campos DNI, Nombres, Apellidos, Teléfono y Correo (opcional), con (*) en los obligatorios.
2. **Given** datos válidos, **When** presiona «Guardar cliente», **Then** el modal se cierra y GUI-01 muestra al cliente cargado con su selector de equipos vacío.
3. **Given** que omite el correo, **When** guarda, **Then** el registro se completa (el correo es opcional).
4. **Given** un DNI ya registrado, **When** presiona «Guardar cliente», **Then** se muestra «El DNI ya está registrado», GUI-01 carga al cliente existente con sus equipos y no se crea otro cliente (RN-01).
5. **Given** campos obligatorios vacíos o un DNI que no son 8 dígitos, **When** presiona «Guardar cliente», **Then** el modal no registra nada e indica cada campo a corregir.
6. **Given** el modal abierto, **When** presiona «Cancelar», **Then** el modal se cierra sin registrar nada y GUI-01 conserva lo que tenía.

---

### User Story 6 - Reintentar la generación de la orden sin duplicarla (Priority: P2)

GUI-01 muestra en su pie el **ID de operación** («ID de operación OP-… · repetir el envío no duplica la orden (RNF-04)»). Si la Recepcionista presiona dos veces «Generar orden de servicio» o reenvía tras un fallo de red, el envío usa el mismo ID de operación y el sistema devuelve la orden ya creada sin duplicarla ni incrementar de nuevo la cola del técnico (CU-01 curso 6a; RN-10; RNF-04).

**Why this priority**: Protege frente al riesgo R2 (reintentos y doble clic duplican registros) en la pantalla donde ocurre, pero se apoya en que la generación básica ya funciona.

**Independent Test**: Presionar dos veces seguidas «Generar orden de servicio» (o reenviar la misma solicitud) y verificar que existe una sola orden, que GUI-01 muestra el mismo N.° y que la cola del técnico aumentó solo en 1; tras confirmar, verificar que una nueva recepción muestra un ID de operación distinto.

**Acceptance Scenarios**:

1. **Given** el formulario completo con un ID de operación visible, **When** la Recepcionista presiona «Generar orden de servicio» dos veces seguidas, **Then** existe una sola orden y GUI-01 muestra el mismo N.° de orden.
2. **Given** que un envío falló por un error recuperable (por ejemplo, de red o un rechazo de validación), **When** reenvía tras corregir, **Then** se usa el mismo ID de operación y, si la orden ya se había creado, se devuelve esa misma orden.
3. **Given** una orden confirmada o la acción «Cancelar», **When** la Recepcionista inicia una nueva recepción, **Then** GUI-01 muestra un ID de operación nuevo.

---

### Edge Cases

- ¿Qué ocurre si la sesión caduca mientras la Recepcionista llena GUI-01? Al enviar, la operación se rechaza por falta de sesión y la interfaz vuelve al inicio de sesión sin crear nada.
- ¿Qué ocurre si un usuario Técnico llama directamente a una operación de recepción sin pasar por la pantalla? Se rechaza igual que desde la pantalla: el control de rol no depende de la interfaz (RNF-02, riesgo R3).
- ¿Qué ocurre si no hay técnicos disponibles? GUI-01 lo informa y no permite generar la orden (precondición de CU-01; RN-03).
- ¿Qué ocurre si el DNI buscado cambia después de cargar al cliente? Se descartan los datos cargados hasta nueva búsqueda (US2, escenario 5).
- ¿Qué ocurre si se reutiliza un ID de operación con datos distintos? GUI-01 muestra el rechazo del conflicto y no se genera ni modifica nada (RN-10).
- ¿Qué ocurre si la respuesta de una operación llega con un error no previsto? GUI-01 muestra un mensaje general de error sin datos técnicos y conserva lo ingresado para reintentar.

## Requirements *(mandatory)*

### Functional Requirements

**Acceso por rol (RNF-02)**

- **FR-001**: El sistema MUST ofrecer una pantalla de inicio de sesión con usuario y contraseña; sin sesión activa, es lo único que se muestra (RNF-02; precondición de CU-01).
- **FR-002**: El sistema MUST rechazar credenciales inválidas con un mensaje que no revele cuál de los dos datos es incorrecto (RNF-02).
- **FR-003**: Las operaciones de recepción —buscar cliente (CU-05), registrar cliente (CU-06), listar técnicos disponibles, consultar el costo de revisión inicial y generar la orden de servicio (CU-01)— MUST exigir una sesión activa y el rol Recepcionista, y el control MUST aplicarse en las propias operaciones y no solo en la pantalla (RNF-02; riesgo R3).
- **FR-004**: Una solicitud de un usuario con rol Técnico MUST rechazarse con un mensaje de acceso no permitido para su rol, distinto del de falta de sesión, sin devolver datos ni crear ni modificar registros (RNF-02).
- **FR-005**: Una solicitud sin sesión activa (inexistente, caducada o inválida) MUST rechazarse sin devolver datos ni crear registros, y la interfaz MUST volver al inicio de sesión (RNF-02).
- **FR-006**: Con sesión de Recepcionista, GUI-01 y GUI-02 MUST mostrar en su encabezado «Recepcionista · sesión activa» (GUI-01, GUI-02).

**Pantalla GUI-01 — estructura y cliente (CU-05)**

- **FR-007**: GUI-01 MUST mostrar el encabezado «ByteTrack v2.0 · Recepción» con los códigos GUI-01 · CU-01 / CU-05 y el indicador de flujo de estados (Recepcionado, Presupuestado, Aprobado, Listo, Entregado) con «Recepcionado» resaltado; el indicador es solo informativo (GUI-01).
- **FR-008**: La sección «1. Cliente (CU-05)» MUST ofrecer el campo DNI (8 dígitos) y los botones «Buscar cliente» y «Registrar nuevo cliente» (GUI-01; CU-05).
- **FR-009**: Al buscar, GUI-01 MUST validar que el DNI sean 8 dígitos numéricos y, si no lo son, indicarlo sin consultar (RN-01).
- **FR-010**: Si el cliente existe, GUI-01 MUST mostrar nombres, apellidos, teléfono y «Cliente encontrado» y cargar sus equipos en el selector (CU-01 pasos 1-2; RN-01).
- **FR-011**: «Registrar nuevo cliente» MUST habilitarse solo cuando el DNI buscado no existe (GUI-01: «el registro solo se habilita si el DNI no existe»; CU-01 curso 2a).
- **FR-012**: Si cambia el DNI en pantalla tras una búsqueda, GUI-01 MUST descartar el cliente y los equipos cargados hasta una nueva búsqueda (CU-05; RN-01).

**Pantalla GUI-01 — equipo (RF-01 / RF-02)**

- **FR-013**: La sección «2. Equipo (RF-01 / RF-02)» MUST ofrecer el selector «Equipos del cliente» (con la opción de ingresar un equipo nuevo) y los campos Tipo, Marca, Modelo y N.° de serie; al elegir un equipo existente, sus datos se muestran y no se editan (CU-01 paso 3; RF-01; RF-02).
- **FR-014**: La sección MUST ofrecer las casillas de accesorios «Cargador original» y «Funda / maletín» (opcionales) y el campo «Estado físico al ingreso» (obligatorio) (CU-01 paso 3; GUI-01).
- **FR-015**: Los valores del campo Tipo MUST provenir de [NEEDS CLARIFICATION: los prototipos muestran «Tipo» como lista desplegable con el valor «Laptop», pero ningún documento AUP define los tipos de equipo admitidos; ¿qué opciones ofrece la lista?].

**Pantalla GUI-01 — orden de servicio (CU-01)**

- **FR-016**: La sección «3. Orden de servicio» MUST ofrecer el campo «Falla reportada por el cliente» (obligatorio), el selector «Técnico disponible (solo disponibles)» y el campo «Costo de revisión» de solo lectura con el importe recibido del sistema, además de mostrar «Estado inicial: RECEPCIONADO» (CU-01 paso 4; RN-03; GUI-01).
- **FR-017**: El selector de técnico MUST ofrecer únicamente técnicos disponibles; si no hay ninguno, GUI-01 MUST informarlo e impedir generar la orden (RN-03; precondición de CU-01).
- **FR-018**: El selector de técnico MUST identificar a cada técnico por su nombre [NEEDS CLARIFICATION: el prototipo muestra «T02 · Marco Salazar (2 en cola)», pero la operación existente solo entrega identificador, nombres y apellidos; ¿se muestra la cola de cada técnico, lo que exige ampliar de forma aditiva la respuesta de esa operación, o solo el nombre?].
- **FR-019**: Al presionar «Generar orden de servicio», GUI-01 MUST validar los campos obligatorios (equipo, estado físico, falla, técnico) y señalar los que falten sin enviar la orden (CU-01 paso 5).
- **FR-020**: Mientras un envío está en curso, GUI-01 MUST impedir enviar de nuevo la misma solicitud desde el botón (RNF-04; riesgo R2).
- **FR-021**: Al generarse la orden, GUI-01 MUST mostrar la confirmación «N.° [código] listo para imprimir · el técnico recibe +1 en su cola» con el código devuelto (CU-01 paso 6; GUI-01).
- **FR-022**: Si el número de serie tiene una orden activa, GUI-01 MUST mostrar la alerta E01 con el texto «Este número de serie ya posee la Orden activa N.° [X] en laboratorio» y no generar la orden; la alerta MUST dejar de mostrarse al cambiar el equipo o corregir el envío (CU-01 curso 5a; RN-02).
- **FR-023**: Para los demás rechazos de la generación (cliente inexistente, técnico no disponible, sin técnicos disponibles, número de serie de otro cliente, conflicto de ID de operación), GUI-01 MUST mostrar el mensaje que entrega el sistema, sin modificar sus reglas (RN-01, RN-03, RN-10).
- **FR-024**: El botón «Cancelar» de GUI-01 MUST descartar lo ingresado y devolver la pantalla a su estado inicial, con un nuevo ID de operación, sin generar ninguna orden (GUI-01).

**ID de operación (RN-10, RNF-04)**

- **FR-025**: El pie de GUI-01 MUST mostrar el ID de operación de la recepción en curso junto con la leyenda «repetir el envío no duplica la orden (RNF-04)» (GUI-01; RNF-04).
- **FR-026**: Todo reenvío de la misma recepción (doble clic, fallo de red, corrección tras un rechazo) MUST usar el mismo ID de operación; una recepción nueva (tras confirmar o cancelar) MUST usar uno nuevo (CU-01 curso 6a; RN-10).

**Modal GUI-02 (CU-06)**

- **FR-027**: «Registrar nuevo cliente» MUST abrir el modal GUI-02, que muestra los campos DNI (*), Nombres (*), Apellidos (*), Teléfono (*) y Correo (opcional), la nota «(*) campo obligatorio» y los botones «Guardar cliente» y «Cancelar»; el DNI aparece precargado con el DNI buscado (CU-06; GUI-02).
- **FR-028**: El modal MUST validar los campos obligatorios y el formato de DNI de 8 dígitos y señalar cada campo a corregir antes de registrar (CU-06; RN-01).
- **FR-029**: Al guardar un cliente nuevo, el modal MUST cerrarse y GUI-01 MUST quedar con el cliente cargado y listo para elegir o ingresar el equipo (CU-01 curso 2a; GUI-02).
- **FR-030**: Si el DNI ya está registrado, el modal MUST mostrar «El DNI ya está registrado», GUI-01 MUST cargar al cliente existente con sus equipos, y el sistema MUST NOT crear un duplicado (CU-01 curso 2b; RN-01).
- **FR-031**: El botón «Cancelar» del modal MUST cerrarlo sin registrar nada y conservar el estado de GUI-01 (GUI-02).

**Reglas inalteradas**

- **FR-032**: La interfaz MUST consumir las operaciones existentes de la iteración C1 sin cambiar sus reglas RN-01, RN-02, RN-03 (asignación) y RN-10; sus validaciones propias solo reflejan esas reglas. El único cambio sobre las operaciones existentes es el control de acceso de FR-003 a FR-005 (y, solo si se confirma en FR-018, un dato adicional de lectura).

### Key Entities *(include if feature involves data)*

- **Usuario**: persona que accede al sistema; tiene credenciales y un rol (Recepcionista o Técnico). Los usuarios existen previamente; esta funcionalidad no los gestiona (RNF-02).
- **Sesión**: acceso activo de un usuario tras un inicio de sesión válido; determina su rol y puede caducar (RNF-02).
- **Cliente**, **Equipo**, **Técnico** y **Orden de servicio**: entidades existentes de la iteración C1 (`specs/001-recepcion-orden-servicio/`); esta funcionalidad no agrega atributos propios.
- **Operación idempotente (ID OP)**: identificador de una recepción que permite reenviarla sin duplicar la orden (RN-10; RNF-04).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las solicitudes de las cinco operaciones de recepción hechas sin sesión activa o con rol Técnico son rechazadas sin devolver datos ni crear ni modificar registros.
- **SC-002**: Una Recepcionista con credenciales válidas llega a GUI-01 en menos de 30 segundos y completa la recepción de un equipo de un cliente ya registrado, desde la búsqueda del DNI hasta ver el N.° de orden, en menos de 3 minutos.
- **SC-003**: Presionar repetidamente «Generar orden de servicio» o reenviar la solicitud produce cero órdenes duplicadas y cero incrementos adicionales de la cola del técnico.
- **SC-004**: El 100 % de los intentos de generar una orden para un número de serie con orden activa muestran E01 con el N.° de la orden activa y no generan ninguna orden.
- **SC-005**: El 100 % de los motivos de rechazo de las operaciones de recepción (credenciales, rol, sesión, validación, E01 y demás) se presentan con un mensaje comprensible, sin mostrar datos técnicos.
- **SC-006**: Todos los campos y botones que muestran los prototipos GUI-01 y GUI-02 existen en la interfaz, y no existe ningún elemento (pantalla, campo, botón o listado) que no figure en la matriz de trazabilidad.
- **SC-007**: Cada requisito en alcance (RNF-02, RNF-04, RN-01, RN-02, RN-03 en su parte de asignación, RN-10) y cada caso de prueba de la sección Trazabilidad cuenta con una prueba automatizada que pasa al cierre de la iteración.

## Assumptions

- **RF-01 y RF-02 sin texto en la documentación**: `docs/aup/requerimientos.md` está vacío; RF-01 y RF-02 solo aparecen como etiqueta de la sección «2. Equipo» de GUI-01 (junto con la mención de RF-01 a RF-06 en `caso.md`, sección 2.2). Se trazan a esa sección y al paso 3 de CU-01; si su redacción difiere, debe reportarse antes de planificar.
- **Usuarios preexistentes**: existen al menos un usuario Recepcionista y uno Técnico, cargados como datos previos y sin pantallas ni operaciones para crearlos, editarlos o asignarles roles (la gestión de usuarios queda fuera de alcance). Las contraseñas no se guardan en el repositorio y se proporcionan por configuración del entorno (constitución, principio VI).
- **Técnico autenticado**: un Técnico con credenciales válidas puede iniciar sesión, pero ninguna pantalla de esta funcionalidad le da acceso; recibe el rechazo de FR-004. No hay pantallas para el Técnico (GUI-03 y siguientes están fuera de alcance).
- **Mecanismo de sesión**: `caso.md` y la especificación 001 nombran OAuth2 con JWT como mecanismo de RNF-02; esta especificación solo exige el comportamiento (sesión, rol, rechazo) y el mecanismo se decide en el plan. La duración de la sesión es un valor de configuración.
- **Pantalla de inicio de sesión**: no tiene prototipo en `docs/aup/`; se limita a usuario, contraseña y mensaje de error, y se traza a RNF-02 y a la precondición de CU-01.
- **Campo accesorios**: las dos casillas del prototipo se envían a la operación existente como un único texto de accesorios (campo opcional ya existente).
- **Interfaz servida por la misma aplicación**: la interfaz usa HTML, CSS y JavaScript sin framework, servida por la aplicación existente (constitución, sección Restricciones Técnicas), y sigue el aspecto de los prototipos.
- **Costo de revisión**: se muestra el importe que entrega el sistema; no se edita (CU-01 paso 4; spec 001).
- **Impresión**: «listo para imprimir» significa mostrar el N.° de orden; no se implementa impresión.
- **Documentos de la iteración 001**: la especificación, el contrato y el plan de 001 indican «sin autenticación» y RNF-02 pendiente; esta funcionalidad los supera para las operaciones de recepción y deben actualizarse al planificar (constitución, principio II).
- **Dependencia**: requiere las operaciones de C1 ya existentes y al menos un técnico disponible para generar órdenes (precondición de CU-01).

## Alcance y Pendientes

**En alcance**: inicio de sesión y control de acceso por rol para las operaciones de CU-05, CU-06 y CU-01 (RNF-02); pantallas GUI-01 y GUI-02 con la alerta E01 y el ID de operación; RNF-04 en la interfaz.

### Fuera de alcance

- Listados (de órdenes, clientes, equipos o técnicos), búsquedas distintas de «Buscar cliente» por DNI, edición o eliminación de clientes, equipos u órdenes, y reportes.
- Gestión de usuarios: altas, roles, cambio o recuperación de contraseña, y cierre de sesión (no figura en los prototipos).
- Pantallas y casos de uso GUI-03 a GUI-06, E02, CU-02, CU-03, CU-04, CU-07 y CU-08, y cualquier pantalla para el Técnico.
- Impresión real del comprobante de orden.
- Cualquier cambio en las reglas de negocio de C1.

**Pendientes registrados (principio VII)**:

| Código | Descripción | Iteración prevista |
|--------|-------------|--------------------|
| RN-03 (parte de acceso) | El técnico solo accede a sus órdenes asignadas | Pendiente (requiere pantallas del Técnico, C2 en adelante) |
| RNF-01 | Reserva atómica de repuestos sobre stock libre | C2 (CU-02) |
| RNF-03 | Rendimiento: p95 ≤ 1 s con 5 sesiones concurrentes | Pendiente de planificar |
| RN-04 a RN-09, RN-11 | Reglas de presupuesto, decisión, reparación, cobro, transacción de entrega y cobro de revisión | C2 a C4 |

## Trazabilidad

Los casos de prueba usan la convención `CU-xx-<curso>` de la constitución; la verificación de acceso se nombra con su requisito (`RNF-02`).

| Caso de prueba | Curso | Historia | Reglas / requisitos | Pantalla / alerta |
|----------------|-------|----------|---------------------|-------------------|
| RNF-02 | Acceso por rol: Recepcionista permitido; Técnico y sin sesión rechazados | US1 | RNF-02 | Inicio de sesión, GUI-01 |
| CU-01-B | Curso básico (incluye CU-05) en la interfaz | US2, US3 | RN-01, RN-02, RN-03, RF-01, RF-02 | GUI-01 |
| CU-01-2a | El DNI no existe (CU-06) | US2, US5 | RN-01 | GUI-01, GUI-02 |
| CU-01-2b | DNI ya registrado en el modal | US5 | RN-01 | GUI-02 |
| CU-01-5a | El equipo ya tiene una orden activa | US4 | RN-02 | E01 en GUI-01 |
| CU-01-6a | Reintento de confirmación (ID OP) | US6 | RN-10, RNF-04 | GUI-01 (pie) |

### Matriz de trazabilidad: pantallas, campos y operaciones

| Elemento | Código AUP de origen | Observación |
|----------|----------------------|-------------|
| Pantalla de inicio de sesión (usuario, contraseña, mensaje de error) | RNF-02; precondición de CU-01 | Sin prototipo; solo lo mínimo para RNF-02 (ver Assumptions) |
| Rechazo por rol / por falta de sesión | RNF-02; riesgo R3 | |
| Encabezado «Recepcionista · sesión activa» | GUI-01, GUI-02 | |
| Indicador de flujo de estados y «Estado inicial: RECEPCIONADO» | GUI-01; CU-01 paso 6 | Solo informativo |
| GUI-01 §1: DNI, «Buscar cliente», «Registrar nuevo cliente», datos del cliente | CU-05; CU-01 pasos 1-2 y curso 2a; RN-01 | |
| GUI-01 §2: selector «Equipos del cliente», Tipo, Marca, Modelo, N.° de serie | RF-01, RF-02; CU-01 paso 3; RN-01 | Opciones de Tipo pendientes (FR-015) |
| GUI-01 §2: casillas «Cargador original» y «Funda / maletín», «Estado físico al ingreso» | CU-01 paso 3; GUI-01 | |
| GUI-01 §3: «Falla reportada», «Técnico disponible», «Costo de revisión» | CU-01 paso 4; RN-03 | Cola del técnico pendiente (FR-018) |
| Botón «Generar orden de servicio» y confirmación «N.° … listo para imprimir» | CU-01 pasos 5-6; GUI-01 | |
| Alerta E01 | CU-01 curso 5a; RN-02 | |
| ID de operación en el pie y leyenda | CU-01 curso 6a; RN-10; RNF-04; GUI-01 | |
| Botón «Cancelar» de GUI-01 | GUI-01 | Comportamiento supuesto: reinicia la pantalla |
| GUI-02: DNI, Nombres, Apellidos, Teléfono, Correo, «Guardar cliente», «Cancelar», aviso «El DNI ya está registrado» | CU-06; CU-01 cursos 2a y 2b; RN-01; GUI-02 | |
| Operación «Buscar cliente» | CU-05 (GUI-01) | Existente en C1; se añade control de acceso (RNF-02) |
| Operación «Registrar nuevo cliente» | CU-06 (GUI-02) | Existente en C1; se añade control de acceso (RNF-02) |
| Operación «Listar técnicos disponibles» | CU-01 paso 4; RN-03 | Existente en C1; se añade control de acceso (RNF-02) |
| Operación «Consultar costo de revisión inicial» | CU-01 paso 4 | Existente en C1; se añade control de acceso (RNF-02) |
| Operación «Registrar orden de servicio» | CU-01; RN-01, RN-02, RN-03, RN-10 | Existente en C1; se añade control de acceso (RNF-02) |
| Operación de inicio de sesión | RNF-02; precondición de CU-01 | Nueva; única operación nueva de la funcionalidad |
