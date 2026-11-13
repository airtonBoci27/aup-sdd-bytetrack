# Feature Specification: Interfaz web de recepción con acceso por rol (Iteración C1)

**Feature Branch**: `002-interfaz-recepcion-rol`

**Created**: 2026-11-12

**Status**: Draft

**Input**: User description: "Crea la interfaz web de recepción de la iteración C1 con acceso por rol. (1) Acceso (RNF-02): inicio de sesión; las operaciones de recepción (CU-01, CU-05, CU-06) exigen sesión activa con rol Recepcionista; un usuario con rol Técnico recibe un rechazo. (2) Interfaz según los prototipos GUI-01 y GUI-02 de docs/aup/caso.md (imágenes en docs/aup/img): búsqueda de cliente por DNI, modal de registro de cliente, datos del equipo, falla, técnico disponible, costo de revisión, alerta E01 e ID de operación. Consume la API existente sin cambiar sus reglas. No agregues nada que no se trace a RF-01, RF-02, RNF-02, RNF-04 o a esos prototipos: ni listados, ni edición, ni reportes, ni gestión de usuarios."

**Fuente de verdad**: `docs/aup/requerimientos.md` (RF-01, RF-02, RNF-02 y RNF-04) y `docs/aup/caso.md` (narrativa de CU-01, prototipos GUI-01 y GUI-02 de la sección 3.2 con sus imágenes `image7.png` e `image10.png`, riesgo R3 de la sección 2.4 y reglas de negocio 2.2). Los códigos CU, RN, RF, RNF, E01, GUI-01 y GUI-02 se conservan tal cual.

**Requisitos en alcance** (texto de `docs/aup/requerimientos.md`):

- **RF-01** Gestionar cliente y equipo: buscar por DNI único (8 dígitos), registrar los datos obligatorios del cliente y asociar múltiples equipos por número de serie único (CU-01, 05, 06).
- **RF-02** Registrar orden: guardar falla reportada, estado físico y accesorios; asignar únicamente a un técnico con `disponible = true`; fijar el costo de revisión; impedir la creación si el equipo ya posee una orden con estado distinto de «Entregado» (CU-01).
- **RNF-02** Seguridad: acceso basado en roles y sesiones activas; las operaciones de recepción están restringidas al rol Recepcionista.
- **RNF-04** Reintentos seguros: repetir una solicitud con el mismo identificador de operación no duplica órdenes.

## Contexto

La iteración C1 ya dispone de las operaciones de recepción (buscar cliente, registrar cliente, listar técnicos disponibles, consultar el costo de revisión y generar la orden de servicio; ver `specs/001-recepcion-orden-servicio/`), pero hoy solo se usan a través de la documentación Swagger y sin control de acceso. La documentación AUP identifica ese hueco como el riesgo R3 («Las reglas se saltan llamando a la API o un técnico ve órdenes ajenas», mitigado por RNF-02) y la precondición de CU-01 exige «sesión iniciada».

Esta funcionalidad entrega a la Recepcionista la **pantalla de recepción (GUI-01) y el modal de registro de cliente (GUI-02)** tal como los muestran los prototipos, y protege las operaciones de recepción con **inicio de sesión y acceso por rol**: solo un usuario con rol Recepcionista y sesión activa puede usarlas; un usuario con rol Técnico es rechazado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar sesión y acceder según el rol (Priority: P1)

Una persona abre la aplicación, ingresa su usuario y contraseña y, si son válidos, el sistema abre una sesión. Si el rol es Recepcionista, se muestra la pantalla de recepción (GUI-01) con la indicación «Recepcionista · sesión activa». Si el rol es Técnico, el sistema no le da acceso a la recepción y muestra un rechazo claro. Sin sesión activa, ninguna operación de recepción responde con datos ni crea nada (RNF-02; precondición de CU-01). La persona puede cerrar su sesión, tras lo cual vuelve al inicio de sesión y puede entrar con otro usuario (RNF-02, «sesiones activas»).

**Why this priority**: Es la precondición de CU-01 («sesión iniciada») y la mitigación del riesgo R3. Sin ella, la interfaz queda abierta a cualquiera y el rol no se hace cumplir; además es la puerta de entrada a las demás historias. El cierre de sesión permite cambiar de rol, necesario para demostrar el rechazo del Técnico.

**Independent Test**: Con un usuario Recepcionista y uno Técnico preexistentes, iniciar sesión con cada uno y verificar que solo el primero llega a GUI-01; invocar cada operación de recepción sin sesión, con sesión de Técnico y con sesión de Recepcionista, y verificar el rechazo en los dos primeros casos y el funcionamiento en el tercero.

**Acceptance Scenarios**:

1. **Given** un usuario con rol Recepcionista y credenciales válidas, **When** inicia sesión, **Then** el sistema muestra GUI-01 con «Recepcionista · sesión activa».
2. **Given** credenciales incorrectas, **When** intenta iniciar sesión, **Then** el sistema no abre sesión y muestra un mensaje de credenciales inválidas.
3. **Given** un usuario con rol Técnico y credenciales válidas, **When** inicia sesión o intenta usar una operación de recepción (CU-01, CU-05, CU-06), **Then** el sistema la rechaza con un mensaje de acceso no permitido para su rol, sin devolver datos ni crear registros.
4. **Given** que no hay sesión activa (nunca se inició, caducó o es inválida), **When** se intenta abrir GUI-01 o usar cualquier operación de recepción, **Then** el sistema rechaza la operación y solo ofrece el inicio de sesión.
5. **Given** una sesión de Recepcionista activa, **When** usa buscar cliente, registrar cliente, listar técnicos disponibles, consultar el costo de revisión y generar la orden, **Then** todas las operaciones responden con normalidad.
6. **Given** una sesión activa, **When** la persona presiona «Cerrar sesión», **Then** la sesión deja de ser válida, la interfaz vuelve al inicio de sesión y cualquier operación de recepción posterior con esa sesión se rechaza; la persona puede iniciar sesión con otro usuario (por ejemplo, un Técnico).

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
- ¿Qué ocurre si se reutiliza un ID de operación con datos distintos? GUI-01 muestra el rechazo del conflicto y no se genera ni modifica nada (RN-10).
- ¿Qué ocurre si la respuesta de una operación llega con un error no previsto? GUI-01 muestra un mensaje general de error sin datos técnicos y conserva lo ingresado para reintentar.

## Requirements *(mandatory)*

### Functional Requirements

**Acceso por rol (RNF-02)**

- **FR-001**: El sistema MUST ofrecer una pantalla de inicio de sesión con usuario y contraseña; sin sesión activa, es lo único que se muestra (RNF-02; precondición de CU-01).
- **FR-002**: El sistema MUST rechazar credenciales inválidas con un mensaje de error, sin abrir sesión (RNF-02).
- **FR-003**: Las operaciones de recepción —buscar cliente (CU-05), registrar cliente (CU-06), listar técnicos disponibles, consultar el costo de revisión inicial y generar la orden de servicio (CU-01)— MUST exigir una sesión activa y el rol Recepcionista, y el control MUST aplicarse en las propias operaciones y no solo en la pantalla (RNF-02; riesgo R3).
- **FR-004**: Una solicitud de un usuario con rol Técnico MUST rechazarse con un mensaje de acceso no permitido para su rol, distinto del de falta de sesión, sin devolver datos ni crear ni modificar registros (RNF-02).
- **FR-005**: Una solicitud sin sesión activa (inexistente, caducada o inválida) MUST rechazarse sin devolver datos ni crear registros, y la interfaz MUST volver al inicio de sesión (RNF-02).
- **FR-006**: Con sesión de Recepcionista, GUI-01 y GUI-02 MUST mostrar en su encabezado «Recepcionista · sesión activa» (GUI-01, GUI-02).
- **FR-007**: El encabezado MUST ofrecer la acción «Cerrar sesión», que invalida la sesión activa, devuelve la interfaz al inicio de sesión y hace que las operaciones de recepción posteriores con esa sesión se rechacen (RNF-02, «sesiones activas»). La acción no figura en los prototipos y se incorpora por RNF-02.

**Pantalla GUI-01 — estructura y cliente (CU-05)**

- **FR-008**: GUI-01 MUST mostrar el encabezado «ByteTrack v2.0 · Recepción» con los códigos GUI-01 · CU-01 / CU-05 y el indicador de flujo de estados (Recepcionado, Presupuestado, Aprobado, Listo, Entregado) con «Recepcionado» resaltado; el indicador es solo informativo (GUI-01).
- **FR-009**: La sección «1. Cliente (CU-05)» MUST ofrecer el campo DNI (8 dígitos) y los botones «Buscar cliente» y «Registrar nuevo cliente» (GUI-01; CU-05; RF-01).
- **FR-010**: Al buscar, GUI-01 MUST validar que el DNI sean 8 dígitos numéricos y, si no lo son, indicarlo sin consultar (RF-01; RN-01).
- **FR-011**: Si el cliente existe, GUI-01 MUST mostrar nombres, apellidos, teléfono y «Cliente encontrado» y cargar sus equipos en el selector (CU-01 pasos 1-2; RN-01).
- **FR-012**: «Registrar nuevo cliente» MUST habilitarse solo cuando el DNI buscado no existe (GUI-01: «el registro solo se habilita si el DNI no existe»; CU-01 curso 2a).
- **FR-013**: *(eliminado: sin origen en `docs/aup/`; se conserva el número para no alterar las referencias)*

**Pantalla GUI-01 — equipo (RF-01 / RF-02)**

- **FR-014**: La sección «2. Equipo (RF-01 / RF-02)» MUST ofrecer el selector «Equipos del cliente» (con la opción de ingresar un equipo nuevo) y los campos Tipo, Marca, Modelo y N.° de serie; al elegir un equipo existente, sus datos se muestran y no se editan (CU-01 paso 3; RF-01; RF-02).
- **FR-015**: La sección MUST ofrecer las casillas de accesorios «Cargador original» y «Funda / maletín» (opcionales) y el campo «Estado físico al ingreso» (obligatorio) (CU-01 paso 3; RF-02; GUI-01).
- **FR-016**: El campo Tipo MUST ser un campo de texto libre obligatorio, no una lista desplegable: CU-01 paso 3 solo pide «tipo» sin enumerar valores y ningún documento AUP define los tipos admitidos, por lo que no se inventan opciones. Es una desviación justificada respecto de GUI-01 (ver «Desviaciones respecto de los prototipos»).

**Pantalla GUI-01 — orden de servicio (CU-01)**

- **FR-017**: La sección «3. Orden de servicio» MUST ofrecer el campo «Falla reportada por el cliente» (obligatorio), el selector «Técnico disponible (solo disponibles)» y el campo «Costo de revisión» de solo lectura con el importe recibido del sistema, además de mostrar «Estado inicial: RECEPCIONADO» (CU-01 paso 4; RN-03; GUI-01).
- **FR-018**: El selector de técnico MUST ofrecer únicamente técnicos disponibles; si no hay ninguno, GUI-01 MUST informarlo e impedir generar la orden (RN-03; precondición de CU-01).
- **FR-019**: El selector de técnico MUST mostrar a cada técnico disponible con su nombre y su cola actual, con el formato «[nombres] [apellidos] ([N] en cola)» (GUI-01; CU-01 paso 6, que define la cola del técnico). Para ello, la operación existente «Listar técnicos disponibles» MUST incluir la cola de cada técnico como dato adicional de solo lectura, sin cambiar qué técnicos se devuelven ni ninguna regla (RN-03).
- **FR-020**: Al presionar «Generar orden de servicio», GUI-01 MUST validar los campos obligatorios (equipo, estado físico, falla, técnico) y señalar los que falten sin enviar la orden (CU-01 paso 5).
- **FR-021**: Mientras un envío está en curso, GUI-01 MUST impedir enviar de nuevo la misma solicitud desde el botón (RNF-04; riesgo R2).
- **FR-022**: Al generarse la orden, GUI-01 MUST mostrar la confirmación «N.° [código] listo para imprimir · el técnico recibe +1 en su cola» con el código devuelto (CU-01 paso 6; GUI-01).
- **FR-023**: Si el número de serie tiene una orden activa, GUI-01 MUST mostrar la alerta E01 con el texto «Este número de serie ya posee la Orden activa N.° [X] en laboratorio» y no generar la orden; la alerta MUST dejar de mostrarse al cambiar el equipo o corregir el envío (CU-01 curso 5a; RN-02).
- **FR-024**: Para los demás rechazos de la generación (cliente inexistente, técnico no disponible, sin técnicos disponibles, número de serie de otro cliente, conflicto de ID de operación), GUI-01 MUST mostrar el mensaje que entrega el sistema, sin modificar sus reglas (RN-01, RN-03, RN-10).
- **FR-025**: El botón «Cancelar» de GUI-01 MUST descartar lo ingresado y devolver la pantalla a su estado inicial, con un nuevo ID de operación, sin generar ninguna orden (GUI-01).

**ID de operación (RN-10, RNF-04)**

- **FR-026**: El pie de GUI-01 MUST mostrar el ID de operación de la recepción en curso junto con la leyenda «repetir el envío no duplica la orden (RNF-04)» (GUI-01; RNF-04).
- **FR-027**: Todo reenvío de la misma recepción (doble clic, fallo de red, corrección tras un rechazo) MUST usar el mismo ID de operación; una recepción nueva (tras confirmar o cancelar) MUST usar uno nuevo (CU-01 curso 6a; RN-10).

**Modal GUI-02 (CU-06)**

- **FR-028**: «Registrar nuevo cliente» MUST abrir el modal GUI-02, que muestra los campos DNI (*), Nombres (*), Apellidos (*), Teléfono (*) y Correo (opcional), la nota «(*) campo obligatorio» y los botones «Guardar cliente» y «Cancelar»; el DNI aparece precargado con el DNI buscado (CU-06; GUI-02).
- **FR-029**: El modal MUST validar los campos obligatorios y el formato de DNI de 8 dígitos y señalar cada campo a corregir antes de registrar (CU-06; RN-01).
- **FR-030**: Al guardar un cliente nuevo, el modal MUST cerrarse y GUI-01 MUST quedar con el cliente cargado y listo para elegir o ingresar el equipo (CU-01 curso 2a; GUI-02).
- **FR-031**: Si el DNI ya está registrado, el modal MUST mostrar «El DNI ya está registrado», GUI-01 MUST cargar al cliente existente con sus equipos, y el sistema MUST NOT crear un duplicado (CU-01 curso 2b; RN-01).
- **FR-032**: El botón «Cancelar» del modal MUST cerrarlo sin registrar nada y conservar el estado de GUI-01 (GUI-02).

**Reglas inalteradas**

- **FR-033**: La interfaz MUST consumir las operaciones existentes de la iteración C1 sin cambiar sus reglas RN-01, RN-02, RN-03 (asignación) y RN-10; sus validaciones propias solo reflejan esas reglas. Los únicos cambios sobre las operaciones existentes son el control de acceso de FR-003 a FR-005 y el dato adicional de solo lectura de FR-019 (la cola de cada técnico).

### Key Entities *(include if feature involves data)*

- **Usuario**: persona que accede al sistema; tiene credenciales y un rol (Recepcionista o Técnico). Los usuarios existen previamente; esta funcionalidad no los gestiona (RNF-02).
- **Sesión**: acceso activo de un usuario tras un inicio de sesión válido; determina su rol y puede caducar (RNF-02).
- **Cliente**, **Equipo**, **Técnico** y **Orden de servicio**: entidades existentes de la iteración C1 (`specs/001-recepcion-orden-servicio/`); esta funcionalidad no agrega atributos propios.
- **Operación idempotente (ID OP)**: identificador de una recepción que permite reenviarla sin duplicar la orden (RN-10; RNF-04).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las solicitudes de las cinco operaciones de recepción hechas sin sesión activa o con rol Técnico son rechazadas sin devolver datos ni crear ni modificar registros.
- **SC-002**: *(eliminado: sus plazos no tienen origen en `docs/aup/`)*
- **SC-003**: Presionar repetidamente «Generar orden de servicio» o reenviar la solicitud produce cero órdenes duplicadas y cero incrementos adicionales de la cola del técnico.
- **SC-004**: El 100 % de los intentos de generar una orden para un número de serie con orden activa muestran E01 con el N.° de la orden activa y no generan ninguna orden.
- **SC-005**: *(eliminado: sin origen en `docs/aup/`)*
- **SC-006**: Todos los campos y botones que muestran los prototipos GUI-01 y GUI-02 existen en la interfaz, y no existe ningún elemento (pantalla, campo, botón o listado) que no figure en la matriz de trazabilidad.
- **SC-007**: El acceso por rol (RNF-02) y las operaciones de recepción protegidas cuentan con pruebas automatizadas que pasan al cierre de la iteración; el comportamiento de la pantalla (GUI-01, GUI-02, E01 e ID de operación) se verifica con la lista de verificación manual de la sección Trazabilidad, ejecutada y registrada al cierre; y los casos `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a` y `CU-01-6a`, así como RN-01, RN-02, RN-03 (asignación) y RN-10, siguen cubiertos por las pruebas automatizadas de la API de la iteración 001, que continúan pasando con el control de acceso activo.

## Assumptions

- **Usuarios preexistentes**: existen al menos un usuario Recepcionista y uno Técnico, cargados como datos previos y sin pantallas ni operaciones para crearlos, editarlos o asignarles roles (la gestión de usuarios queda fuera de alcance). Las contraseñas no se guardan en el repositorio y se proporcionan por configuración del entorno (constitución, principio VI); una plantilla `.env.example` sin valores secretos indica qué variables configurar (principio VI; datos iniciales de la fase de Transición).
- **Técnico autenticado**: un Técnico con credenciales válidas puede iniciar sesión, pero ninguna pantalla de esta funcionalidad le da acceso; recibe el rechazo de FR-004. No hay pantallas para el Técnico (GUI-03 y siguientes están fuera de alcance), por lo que la restricción de RNF-02 «únicamente sobre sus órdenes asignadas» queda pendiente.
- **Mecanismo de sesión**: RNF-02 exige «roles y sesiones activas» sin fijar mecanismo; `caso.md` (riesgo R3 y arquitectura candidata) nombra OAuth2 con JWT. Esta especificación solo exige el comportamiento (sesión, rol, rechazo, cierre) y el mecanismo se decide en el plan. La duración de la sesión es un valor de configuración.
- **Pantalla de inicio de sesión y «Cerrar sesión»**: no tienen prototipo en `docs/aup/`; se limitan a usuario, contraseña, mensaje de error y una acción en el encabezado, y se trazan a RNF-02 (roles y sesiones activas) y a la precondición de CU-01.
- **Campo accesorios**: las dos casillas del prototipo se envían a la operación existente como un único texto de accesorios (campo opcional ya existente; RF-02).
- **Interfaz servida por la misma aplicación**: la interfaz usa HTML, CSS y JavaScript sin framework, servida por la aplicación existente (constitución, sección Restricciones Técnicas), y sigue el aspecto de los prototipos salvo las desviaciones registradas.
- **Costo de revisión**: se muestra el importe que entrega el sistema; no se edita (CU-01 paso 4; RF-02, «fijar costo de revisión»).
- **Impresión**: «listo para imprimir» significa mostrar el N.° de orden; no se implementa impresión.
- **Documentos de la iteración 001**: la especificación, el contrato y el plan de 001 indican «sin autenticación» y RNF-02 pendiente, y el contrato de «Listar técnicos disponibles» no incluye la cola. Esta funcionalidad los supera; deben actualizarse al planificar (constitución, principio II).
- **Dependencia**: requiere las operaciones de C1 ya existentes y al menos un técnico disponible para generar órdenes (precondición de CU-01).

## Alcance y Pendientes

**En alcance**: inicio de sesión, cierre de sesión y control de acceso por rol para las operaciones de CU-05, CU-06 y CU-01 (RNF-02); pantallas GUI-01 y GUI-02 con la alerta E01 y el ID de operación (RF-01, RF-02); RNF-04 en la interfaz.

### Fuera de alcance

- Listados (de órdenes, clientes, equipos o técnicos), búsquedas distintas de «Buscar cliente» por DNI, edición o eliminación de clientes, equipos u órdenes, y reportes.
- Gestión de usuarios: altas, roles, cambio o recuperación de contraseña.
- Pantallas y casos de uso GUI-03 a GUI-06, E02, CU-02, CU-03, CU-04, CU-07 y CU-08, y cualquier pantalla para el Técnico.
- Impresión real del comprobante de orden.


| Código | Descripción | Iteración prevista |
|--------|-------------|--------------------|
| RNF-02 (parte restante) | Restricciones de decisión y cobro al Recepcionista; de diagnóstico, cotización y finalización al Técnico, solo sobre sus órdenes asignadas (RN-03, parte de acceso) | Con CU-02, CU-03, CU-04 y CU-08 (C2 a C4) |
| RF-03 a RF-06 | Diagnóstico, decisión, cobro y entrega, finalización | C2 a C4 |
| RNF-01 | Reserva atómica de repuestos sobre stock libre | C2 (CU-02) |
| RNF-03 | Rendimiento: p95 ≤ 1 s con 5 sesiones concurrentes | Pendiente de planificar |
| RN-04 a RN-09, RN-11 | Reglas de presupuesto, decisión, reparación, cobro, transacción de entrega y cobro de revisión | C2 a C4 |

## Trazabilidad

Los casos de prueba usan la convención `CU-xx-<curso>` de la constitución; la verificación de acceso se nombra con su requisito (`RNF-02`).

**Cobertura**: `RNF-02` se prueba de forma automatizada sobre la API de esta funcionalidad. Los cursos `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a` y `CU-01-6a` ya están cubiertos por las pruebas automatizadas de la API de 001 (`tests/test_cu0*.py`), que se mantienen sin cambios. Lo que añade esta funcionalidad en la pantalla (campos, mensajes, alerta E01, ID de operación, doble clic, modal) se verifica con la lista de verificación manual [`checklists/verificacion-manual.md`](checklists/verificacion-manual.md), cuyos ítems citan el mismo código `CU-01-<curso>`. No se automatizan pruebas en navegador (decisión del usuario).

| Caso de prueba | Curso | Historia | Requisitos / reglas | Pantalla / alerta |
|----------------|-------|----------|---------------------|-------------------|
| RNF-02 | Acceso por rol: Recepcionista permitido; Técnico y sin sesión rechazados; cierre de sesión | US1 | RNF-02 | Inicio de sesión, GUI-01 |
| CU-01-B | Curso básico (incluye CU-05) en la interfaz | US2, US3 | RF-01, RF-02; RN-01, RN-02, RN-03 | GUI-01 |
| CU-01-2a | El DNI no existe (CU-06) | US2, US5 | RF-01; RN-01 | GUI-01, GUI-02 |
| CU-01-2b | DNI ya registrado en el modal | US5 | RF-01; RN-01 | GUI-02 |
| CU-01-5a | El equipo ya tiene una orden activa | US4 | RF-02; RN-02 | E01 en GUI-01 |
| CU-01-6a | Reintento de confirmación (ID OP) | US6 | RNF-04; RN-10 | GUI-01 (pie) |

### Matriz de trazabilidad: requisitos, pantallas, campos y operaciones

Cada fila indica el requisito de `docs/aup/requerimientos.md` (RF/RNF) o el prototipo del que proviene el elemento.

| Elemento | RF / RNF / prototipo de origen | Otros códigos |
|----------|-------------------------------|---------------|
| Pantalla de inicio de sesión (usuario, contraseña, mensaje de error) | RNF-02 | Precondición de CU-01 |
| Acción «Cerrar sesión» en el encabezado | RNF-02 («sesiones activas») | Sin prototipo |
| Rechazo por rol y por falta de sesión | RNF-02 | Riesgo R3 |
| Encabezado «Recepcionista · sesión activa» | GUI-01, GUI-02 | RNF-02 |
| Indicador de flujo de estados y «Estado inicial: RECEPCIONADO» | GUI-01 | CU-01 paso 6; solo informativo |
| GUI-01 §1: DNI, «Buscar cliente», datos del cliente, «Cliente encontrado» | RF-01; GUI-01 | CU-05; CU-01 pasos 1-2; RN-01 |
| GUI-01 §1: «Registrar nuevo cliente» (solo si el DNI no existe) | RF-01; GUI-01 | CU-01 curso 2a |
| GUI-01 §2: selector «Equipos del cliente», Marca, Modelo, N.° de serie | RF-01; GUI-01 | CU-01 paso 3; RN-01 |
| GUI-01 §2: Tipo (texto libre) | RF-01; CU-01 paso 3 | Desviación D1 |
| GUI-01 §2: casillas «Cargador original» y «Funda / maletín», «Estado físico al ingreso» | RF-02; GUI-01 | CU-01 paso 3 |
| GUI-01 §3: «Falla reportada» | RF-02; GUI-01 | CU-01 paso 4 |
| GUI-01 §3: «Técnico disponible» con su cola | RF-02 («asignar únicamente a un técnico con disponible = true»); GUI-01 | CU-01 pasos 4 y 6; RN-03 |
| GUI-01 §3: «Costo de revisión» | RF-02 («fijar costo de revisión»); GUI-01 | CU-01 paso 4 |
| Botón «Generar orden de servicio» y confirmación «N.° … listo para imprimir» | RF-02; GUI-01 | CU-01 pasos 5-6 |
| Alerta E01 | RF-02 («impedir la creación si el equipo ya posee una orden…»); GUI-01 | CU-01 curso 5a; RN-02 |
| ID de operación en el pie y leyenda | RNF-04; GUI-01 | CU-01 curso 6a; RN-10 |
| Botón «Cancelar» de GUI-01 | GUI-01 | Comportamiento supuesto: reinicia la pantalla |
| GUI-02: DNI, Nombres, Apellidos, Teléfono, Correo, «Guardar cliente», «Cancelar», aviso «El DNI ya está registrado» | RF-01 («registrar datos obligatorios del cliente»); GUI-02 | CU-06; CU-01 cursos 2a y 2b; RN-01 |
| Operación «Buscar cliente» | RF-01 | CU-05; se añade control de acceso (RNF-02) |
| Operación «Registrar nuevo cliente» | RF-01 | CU-06; se añade control de acceso (RNF-02) |
| Operación «Listar técnicos disponibles» | RF-02 | CU-01 paso 4; RN-03; se añade control de acceso (RNF-02) y la cola de cada técnico (D2) |
| Operación «Consultar costo de revisión inicial» | RF-02 | CU-01 paso 4; se añade control de acceso (RNF-02) |
| Operación «Registrar orden de servicio» | RF-02; RNF-04 | CU-01; RN-01, RN-02, RN-03, RN-10; se añade control de acceso (RNF-02) |
| Operaciones de inicio y cierre de sesión | RNF-02 | Nuevas; únicas operaciones nuevas de la funcionalidad |

### Desviaciones respecto de los prototipos

| Id | Prototipo | Implementación | Justificación |
|----|-----------|----------------|---------------|
| D1 | GUI-01 §2: «Tipo» es una lista desplegable con «Laptop» | Campo de texto libre obligatorio | CU-01 paso 3 solo pide «tipo» y ningún documento AUP enumera los tipos; no se inventan opciones (principio VIII). Decidido por el usuario. |
| D2 | GUI-01 §3: técnico mostrado como «T02 · Marco Salazar (2 en cola)» | «[nombres] [apellidos] ([N] en cola)», sin el código «T02» | El código de técnico no está definido en la documentación AUP; la cola sí (CU-01 paso 6). Requiere el dato adicional de solo lectura de FR-019. Decidido por el usuario. |
| D3 | El encabezado de GUI-01 y GUI-02 no muestra ninguna acción de sesión | Se añade «Cerrar sesión» | RNF-02 («sesiones activas»); permite cambiar de rol en la demostración. Decidido por el usuario. |
