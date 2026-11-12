# Contrato de interfaz — Inicio de sesión, GUI-01 y GUI-02

Define lo que la interfaz web debe contener y cómo se comporta. Es la fuente de las pruebas estáticas (cada elemento lleva `data-trace` con su código AUP) y de la lista de verificación manual ([../checklists/verificacion-manual.md](../checklists/verificacion-manual.md)). Prototipos: `docs/aup/img/media/image7.png` (GUI-01) e `image10.png` (GUI-02). Operaciones consumidas: [api-acceso.md](api-acceso.md) y el contrato de C1.

Cada elemento del HTML que figura abajo lleva `id` y `data-trace`. **No puede existir en las vistas ningún elemento interactivo ni campo con `id` que no esté en estas tablas** (principio VIII).

## Vistas y navegación

| Vista (`id`) | Cuándo se muestra |
|--------------|-------------------|
| `vista-login` | Sin sesión, al vencer o cerrarse la sesión, o ante un 401 |
| `vista-rechazo-rol` | Sesión de un rol distinto de Recepcionista |
| `vista-recepcion` (GUI-01) | Sesión de Recepcionista; contiene el modal `modal-cliente` (GUI-02) |

Solo una vista es visible a la vez. Al cargar la página se lee la sesión de `sessionStorage` (D9); sin ella se muestra `vista-login`.

## Inicio de sesión (RNF-02)

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `login-usuario` | Campo usuario | RNF-02 | Obligatorio |
| `login-clave` | Campo contraseña (oculta) | RNF-02 | Obligatorio |
| `login-entrar` | Botón «Iniciar sesión» | RNF-02 | `POST /auth/token`; con rol Recepcionista → `vista-recepcion`; con otro rol → `vista-rechazo-rol`; con 401 → `login-error` |
| `login-error` | Mensaje de error | RNF-02 | Muestra «Usuario o contraseña incorrectos» o «Su sesión expiró» |

## Rechazo por rol (FR-004)

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `rechazo-mensaje` | Texto «Su rol no tiene acceso a las operaciones de recepción» | RNF-02 | No se muestra ningún dato ni pantalla de recepción |

## Encabezado (GUI-01, GUI-02; FR-006, FR-007, FR-008)

Visible en `vista-recepcion` y `vista-rechazo-rol`.

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `encabezado-titulo` | «ByteTrack v2.0 · Recepción  GUI-01 · CU-01 / CU-05» | GUI-01 | — |
| `sesion-etiqueta` | «Recepcionista · sesión activa» | GUI-01, RNF-02 | Solo con rol Recepcionista |
| `cerrar-sesion` | Botón «Cerrar sesión» | RNF-02 | `POST /auth/logout`; borra `sessionStorage`; → `vista-login`. Aunque falle la llamada, la interfaz vuelve al inicio de sesión (desviación D3) |
| `flujo-estados` | Indicador Recepcionado · Presupuestado · Aprobado · Listo · Entregado, con «Recepcionado» resaltado | GUI-01 | Solo informativo (sin acciones) |

## GUI-01 §1 Cliente (CU-05; RF-01)

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `dni` | Campo «DNI (8 dígitos)» | RF-01, RN-01 | — |
| `buscar-cliente` | Botón «Buscar cliente» | RF-01 | Valida 8 dígitos (`dni-error`); `GET /clientes/{dni}` |
| `dni-error` | Mensaje «El DNI debe tener 8 dígitos» | RN-01 | — |
| `registrar-cliente-abrir` | Botón «Registrar nuevo cliente» | RF-01 | Deshabilitado salvo que la búsqueda devolviera 404 `CLIENTE_NO_ENCONTRADO` (FR-012); abre `modal-cliente` |
| `cliente-resumen` | «[Nombres Apellidos] · [teléfono] · Cliente encontrado» o «Cliente no encontrado» | RF-01 | — |

## GUI-01 §2 Equipo (RF-01 / RF-02)

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `equipo-selector` | «Equipos del cliente»: equipos del cliente + opción «Ingresar equipo nuevo» | RF-01 | Al elegir uno existente, se rellenan y bloquean los campos de equipo; con «nuevo» quedan editables |
| `equipo-tipo` | Campo de texto «Tipo» (obligatorio) | RF-01 | Texto libre (desviación D1) |
| `equipo-marca` | «Marca» | RF-01 | Obligatorio |
| `equipo-modelo` | «Modelo» | RF-01 | Obligatorio |
| `equipo-serie` | «N.° de serie» | RF-01, RN-01 | Obligatorio |
| `acc-cargador` | Casilla «Cargador original» | RF-02 | Opcional |
| `acc-funda` | Casilla «Funda / maletín» | RF-02 | Opcional; las casillas marcadas se envían como un texto único en `accesorios` |
| `estado-fisico` | «Estado físico al ingreso (obligatorio)» | RF-02 | Obligatorio |
| `alerta-e01` | Alerta roja «Este número de serie ya posee la Orden activa N.° [X] en laboratorio» | RF-02, RN-02 | Visible solo tras un 409 `E01`; se oculta al cambiar de equipo o de datos (FR-023) |

## GUI-01 §3 Orden de servicio (CU-01; RF-02)

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `falla` | «Falla reportada por el cliente (obligatorio)» | RF-02 | Obligatorio |
| `tecnico` | «Técnico disponible (solo disponibles)»; cada opción «[nombres] [apellidos] ([N] en cola)» | RF-02, RN-03 | `GET /tecnicos/disponibles`; vacío → mensaje y `generar-orden` deshabilitado (FR-018) |
| `costo-revision` | «Costo de revisión» (solo lectura, «S/ 40.00») | RF-02 | `GET /ordenes/costo-revision-inicial` |
| `estado-inicial` | «Estado inicial: RECEPCIONADO» | GUI-01 | Informativo |

## GUI-01 resultados y pie

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `alerta-error` | Mensaje de los demás rechazos (`CLIENTE_NO_ENCONTRADO`, `TECNICO_NO_DISPONIBLE`, `SIN_TECNICOS_DISPONIBLES`, `SERIE_EN_OTRO_CLIENTE`, `ID_OP_CONFLICTO`, error inesperado) | RF-02, RNF-04 | Muestra el `mensaje` del servidor; un error inesperado muestra un texto general sin datos técnicos y conserva lo ingresado |
| `confirmacion-orden` | Recuadro verde «N.° [código] listo para imprimir · el técnico recibe +1 en su cola» | RF-02 | Tras 201 o 200 (reintento) |
| `id-operacion` | «ID de operación OP-… · repetir el envío no duplica la orden (RNF-04)» | RNF-04 | `OP-` + 12 hex; nuevo al iniciar, al confirmar y al cancelar; igual en reenvíos (FR-027) |
| `cancelar-orden` | Botón «Cancelar» | GUI-01 | Descarta lo ingresado y reinicia GUI-01 (cliente, equipo, orden) con un ID OP nuevo |
| `generar-orden` | Botón «Generar orden de servicio» | RF-02 | Valida obligatorios y señala los faltantes (marca el campo, sin enviar); se deshabilita durante el envío (FR-021); `POST /ordenes` |

## GUI-02 Modal «Registrar nuevo cliente · CU-06» (RF-01)

| `id` | Elemento | `data-trace` | Comportamiento |
|------|----------|--------------|----------------|
| `modal-cliente` | Contenedor con título «Registrar nuevo cliente · CU-06 / GUI-02» y encabezado «Recepcionista · sesión activa» | GUI-02 | Se abre con el DNI buscado precargado (FR-028) |
| `cli-dni` | «DNI (*)» con la nota «8 dígitos. Si ya existe se avisa «El DNI ya está registrado» y se abre el cliente existente, sin duplicar» | RF-01, RN-01 | 8 dígitos |
| `cli-nombres` | «Nombres (*)» | RF-01 | Obligatorio |
| `cli-apellidos` | «Apellidos (*)» | RF-01 | Obligatorio |
| `cli-telefono` | «Teléfono (*)» | RF-01 | Obligatorio |
| `cli-correo` | «Correo (opcional)» | RF-01 | Opcional |
| `cli-guardar` | Botón «Guardar cliente» | RF-01 | `POST /clientes`; 201 → cierra y carga el cliente en GUI-01 (curso 2a); 200 con `ya_registrado` → muestra `cli-aviso`, carga al cliente existente y sus equipos en GUI-01 y deja el modal abierto con «Guardar cliente» deshabilitado hasta que se edite el DNI; «Cancelar» lo cierra sin deshacer la carga (curso 2b) |
| `cli-aviso` | «El DNI ya está registrado» | RF-01, RN-01 | — |
| `cli-error` | Mensaje de campos a corregir | RF-01 | Marca cada campo obligatorio vacío o el DNI inválido |
| `cli-cancelar` | Botón «Cancelar» | GUI-02 | Cierra el modal sin registrar y conserva GUI-01 |
| `cli-nota` | «(*) campo obligatorio · al guardar vuelve a GUI-01 con el cliente cargado» | GUI-02 | Informativo |

## Reglas transversales

- Toda llamada a la API lleva `Authorization: Bearer`. Un 401 en cualquier llamada borra la sesión y lleva a `vista-login` con «Su sesión expiró»; un 403 lleva a `vista-rechazo-rol`.
- Todo texto del servidor se inserta con `textContent` (D9).
- No hay listados, edición, reportes ni gestión de usuarios (fuera de alcance).
- El diseño visual sigue los prototipos (colores y distribución); la fidelidad exacta de píxeles no es un requisito.
