---

description: "Lista de tareas de la funcionalidad 002: interfaz web de recepción con acceso por rol (iteración C1)"
---

# Tasks: Interfaz web de recepción con acceso por rol (Iteración C1)

**Input**: Documentos de diseño en `/specs/002-interfaz-recepcion-rol/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/api-acceso.md](contracts/api-acceso.md), [contracts/ui-gui01-gui02.md](contracts/ui-gui01-gui02.md), [quickstart.md](quickstart.md)

**Tests**: OBLIGATORIOS para el acceso por rol (principio III): pruebas automatizadas de la API, nombradas con el código que cubren (`test_rnf02_...`). La pantalla NO tiene pruebas en navegador (decisión del usuario): se verifica con [checklists/verificacion-manual.md](checklists/verificacion-manual.md), y los cursos `CU-01-B`, `2a`, `2b`, `5a` y `6a` siguen cubiertos por las pruebas de API de 001, que no se modifican. Escribir cada prueba antes de su implementación y comprobar que falla.

**Organization**: Tareas agrupadas por historia de usuario de la spec (US1 a US6).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario (US1 a US6); Setup, Foundational y Polish no llevan etiqueta
- Todas las rutas son relativas a la raíz del repositorio

## Path Conventions

Proyecto único según el plan: `app/` (`api`, `services`, `repositories`, `models`, `web`) y `tests/`. Capas obligatorias: API → servicio → repositorio (principio IV). Solo se trabaja sobre estas tareas (principios II, VII y VIII); `docs/aup/` no se modifica; no se agrega ningún elemento de interfaz que no esté en [contracts/ui-gui01-gui02.md](contracts/ui-gui01-gui02.md). Todo texto del servidor se inserta en la página con `textContent` (nunca `innerHTML`). Las pruebas generan sus propias contraseñas y clave de firma en tiempo de ejecución: no escribir ningún secreto en el código, las pruebas ni los datos de ejemplo (principio VI).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependencias aprobadas (constitución 1.3.0) y plantilla de configuración

- [X] T001 Agregar las dependencias de ejecución aprobadas con `uv add pyjwt python-multipart python-dotenv` (sin dependencias de desarrollo nuevas) y confirmar que `pyproject.toml` y `uv.lock` quedan actualizados; verificar con `uv run python -c "import jwt, multipart, dotenv"` que se importan. No agregar ninguna otra dependencia (research D12)
- [X] T002 [P] Crear `.env.example` en la raíz con solo nombres de variables y **sin ningún valor secreto**: `BYTETRACK_JWT_SECRET=`, `BYTETRACK_RECEPCIONISTA_CLAVE=` y `BYTETRACK_TECNICO_CLAVE=` con valor vacío y un comentario cada una (mínimo 32 caracteres para la clave de firma; generar con `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`); y comentadas, con su valor por defecto no secreto, `# BYTETRACK_RECEPCIONISTA_USUARIO=recepcion`, `# BYTETRACK_TECNICO_USUARIO=tecnico`, `# BYTETRACK_SESION_MINUTOS=60`, `# BYTETRACK_ENV_FILE=./.env`, `# BYTETRACK_DB_PATH=./bytetrack.db` y `# BYTETRACK_COSTO_REVISION=40.00`. Confirmar con `git check-ignore -v .env .env.example` que `.env` está ignorado y `.env.example` no (principio VI, constitución 1.3.0)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Configuración, errores, entidades, utilidades de seguridad, repositorio, servicio y dependencias de acceso que DEBEN existir antes de cualquier historia (RNF-02)

**⚠️ CRITICAL**: Ninguna historia puede empezar hasta terminar esta fase

- [X] T003 [P] Escribir primero `tests/test_rnf02_configuracion.py` (RNF-02; principio VI), con `monkeypatch` y archivos `.env` temporales (`tmp_path`), y comprobar que falla. Casos: `test_rnf02_clave_jwt_ausente_o_vacia_falla`; `test_rnf02_clave_jwt_menor_de_32_caracteres_falla` (31 falla, 32 se acepta); `test_rnf02_sesion_minutos_por_defecto_60_y_configurable`; `test_rnf02_cargar_entorno_no_sobrescribe_variables_ya_definidas`; `test_rnf02_cargar_entorno_usa_BYTETRACK_ENV_FILE`; `test_rnf02_variable_vacia_se_trata_como_no_definida` (incluye `BYTETRACK_DB_PATH=` vacío → ruta por defecto); `test_rnf02_importar_la_app_no_lee_el_env`; `test_rnf02_credenciales_iniciales_exigen_las_dos_claves_y_usan_usuarios_por_defecto` (`recepcion` y `tecnico`). Hash: `test_rnf02_hash_scrypt_formato_y_verificacion` (formato `scrypt$n$r$p$sal$hash`, clave correcta → verdadero, incorrecta → falso), `test_rnf02_hash_con_sal_distinta_por_llamada`, `test_rnf02_hash_no_contiene_la_contraseña`, `test_rnf02_verificar_hash_con_formato_invalido_devuelve_falso`. JWT: `test_rnf02_jwt_crear_y_decodificar_sub_jti_exp`, `test_rnf02_jwt_vencido_se_rechaza`, `test_rnf02_jwt_con_firma_de_otra_clave_se_rechaza`, `test_rnf02_jwt_alg_none_se_rechaza`, `test_rnf02_jwt_sin_jti_o_sin_sub_se_rechaza`
- [X] T004 Implementar `app/config.py` (RNF-02; principio VI): añadir `ConfiguracionError`; una función interna `_leer(nombre)` que devuelve `None` si la variable no existe o está vacía/en blanco, y usarla también en `ruta_base_datos()` y `costo_revision_inicial()` (comportamiento de 001 sin cambios); `cargar_entorno()` que usa `dotenv.load_dotenv(ruta, override=False)` con `ruta = BYTETRACK_ENV_FILE` o `./.env` y **nunca se llama al importar el módulo**; `clave_jwt()` que lanza `ConfiguracionError` si `BYTETRACK_JWT_SECRET` falta o tiene menos de 32 caracteres, con mensaje claro; `minutos_sesion()` (entero > 0, por defecto `60`, de `BYTETRACK_SESION_MINUTOS`); `credenciales_iniciales()` que devuelve tuplas `(nombre_usuario, clave, rol)` para Recepcionista (`BYTETRACK_RECEPCIONISTA_USUARIO` por defecto `recepcion`, `BYTETRACK_RECEPCIONISTA_CLAVE`) y Técnico (`BYTETRACK_TECNICO_USUARIO` por defecto `tecnico`, `BYTETRACK_TECNICO_CLAVE`), lanzando `ConfiguracionError` si falta una contraseña. Sin ningún valor secreto por defecto
- [X] T005 [P] Ampliar `app/errors.py` (RNF-02): en `ErrorDominio` añadir el atributo de clase `headers: dict[str, str]` (vacío por defecto) y las subclases `CredencialesInvalidas` (401, código `CREDENCIALES_INVALIDAS`, mensaje «Usuario o contraseña incorrectos»), `NoAutenticado` (401, código `NO_AUTENTICADO`, mensaje «Debe iniciar sesión») —ambas con `headers = {"WWW-Authenticate": "Bearer"}`— y `RolNoPermitido` (403, código `ROL_NO_PERMITIDO`, mensaje «Su rol no tiene acceso a las operaciones de recepción»), cada una con docstring que cite `RNF-02`
- [X] T006 [P] Agregar a `app/models/entities.py` las entidades de [data-model.md](data-model.md) (RNF-02): `Usuario` (tabla `usuario`: `id` PK entero; `nombre_usuario` texto obligatorio y único; `clave_hash` texto obligatorio, «formato `scrypt$n$r$p$sal$hash`; nunca la contraseña»; `rol` texto obligatorio con `CHECK rol IN ('RECEPCIONISTA','TECNICO')`) y `TokenRevocado` (tabla `token_revocado`: `jti` texto PK; `expira_en` entero obligatorio, «segundos desde la época, UTC»); constantes `ROL_RECEPCIONISTA = "RECEPCIONISTA"` y `ROL_TECNICO = "TECNICO"`. No modificar las entidades de C1
- [X] T007 [P] Implementar `app/security.py` con utilidades puras sin acceso a datos (RNF-02; research D2 y D4): `hashear_clave(clave) -> str` con `hashlib.scrypt` (n=2^14, r=8, p=1, sal aleatoria de 16 bytes, formato `scrypt$n$r$p$sal$hash` en base64); `verificar_clave(clave, almacenado) -> bool` con `hmac.compare_digest`, que devuelve `False` (sin excepción) ante un formato inválido; `crear_token(sub, minutos, clave_firma) -> (token, jti, exp)` con JWT HS256 y reclamos `sub`, `jti` (UUID aleatorio), `iat` y `exp`; `decodificar_token(token, clave_firma) -> dict` con `algorithms=["HS256"]` y reclamos `exp`, `sub` y `jti` obligatorios, que lanza `TokenInvalido` (clase propia) ante cualquier fallo de PyJWT
- [X] T008 [P] Agregar a `app/models/schemas.py` el esquema `TokenOut` (RNF-02): `access_token: str`, `token_type: str = "bearer"`, `rol: str` (informativo para la interfaz; la API no lo toma del token)
- [X] T009 Implementar `app/repositories/usuario_repository.py` (RNF-02; capa de repositorio): `UsuarioRepository(sesion)` con `obtener_por_nombre(nombre)`, `crear_o_actualizar(nombre_usuario, clave_hash, rol)` (crea o actualiza el hash y el rol), `esta_revocado(jti)`, `revocar(jti, expira_en)` (idempotente) y `purgar_vencidos(ahora)` (borra filas con `expira_en` menor que `ahora`). Depende de T006
- [X] T010 Implementar `app/services/auth_service.py` (RNF-02; precondición de CU-01; las reglas viven en el servicio): `iniciar_sesion(sesion, usuario, clave) -> TokenOut` (usuario inexistente o contraseña incorrecta → `CredencialesInvalidas`; la duración sale de `config.minutos_sesion()` y la firma de `config.clave_jwt()`; un Técnico con credenciales válidas sí obtiene token); `verificar_sesion(sesion, token) -> Usuario` (token ausente, vencido, con firma inválida, con `jti` revocado o con `sub` de un usuario inexistente → `NoAutenticado`; el rol se lee de la base, no del token; termina la transacción de lectura con `sesion.rollback()` para no retenerla); `exigir_recepcionista(usuario)` (rol distinto de `RECEPCIONISTA` → `RolNoPermitido`); `cerrar_sesion(sesion, token)` (revoca el `jti` con su `exp`, purga los vencidos y confirma). Depende de T004, T005, T007 y T009
- [X] T011 Implementar `app/api/seguridad.py` y agregar a `app/api/etiquetas.py` la etiqueta `CU01_ACCESO = "CU-01 · Acceso (RNF-02)"` con su descripción («Inicio y cierre de sesión; precondición de CU-01 y RNF-02»). En `seguridad.py`: `esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)` (para que Swagger muestre «Authorize» y el error sea el formato uniforme); `get_session_seguridad()` dependencia que entrega una **sesión de base de datos propia e independiente de la de la solicitud** (research D7: usar la sesión de la operación deshabilitaría el `BEGIN IMMEDIATE` del que dependen RN-02 y RN-10), tomada de `app.database._fabrica_por_defecto()`; `usuario_actual(token, sesion)` que delega en `auth_service.verificar_sesion` (cualquier rol); y `exigir_recepcionista(usuario)` que delega en `auth_service.exigir_recepcionista`. Los endpoints no contienen lógica de acceso (principio IV). Depende de T010

**Checkpoint**: `uv run pytest tests/test_rnf02_configuracion.py` pasa; la base de seguridad está lista

---

## Phase 3: User Story 1 - Iniciar sesión y acceder según el rol (Priority: P1) 🎯 MVP

**Goal**: Solo un usuario con rol Recepcionista y sesión activa usa las cinco operaciones de recepción; el Técnico y quien no tiene sesión son rechazados; se puede iniciar y cerrar sesión desde la interfaz (RNF-02; precondición de CU-01; FR-001 a FR-007).

**Independent Test**: Con un usuario Recepcionista y uno Técnico, iniciar sesión con cada uno en la interfaz y verificar que solo el primero llega a la pantalla de recepción; invocar cada operación sin sesión, con sesión de Técnico y con sesión de Recepcionista (pruebas `test_rnf02_...` y ítems A1 a A7 de la lista manual).

### Tests for User Story 1 ⚠️

> **NOTA: escribir primero y comprobar que FALLAN antes de implementar**

- [X] T012 [P] [US1] Escribir `tests/test_rnf02_acceso.py` (RNF-02; FR-002 a FR-007), parametrizando sobre las cinco operaciones de recepción (`GET /clientes/{dni}`, `POST /clientes`, `GET /tecnicos/disponibles`, `GET /ordenes/costo-revision-inicial`, `POST /ordenes`) y usando las fixtures de T014. Casos: `test_rnf02_login_recepcionista_devuelve_token_bearer_y_rol` (200, `token_type == "bearer"`, `rol == "RECEPCIONISTA"`, el JWT trae `sub`, `jti` y `exp`); `test_rnf02_login_tecnico_obtiene_token_con_rol_tecnico`; `test_rnf02_login_credenciales_invalidas_devuelve_401` (contraseña incorrecta y usuario inexistente devuelven 401 con el cuerpo `CREDENCIALES_INVALIDAS` y `WWW-Authenticate: Bearer`, sin token); `test_rnf02_login_sin_campos_devuelve_422`; `test_rnf02_sin_sesion_devuelve_401_no_autenticado`; `test_rnf02_token_vencido_devuelve_401`; `test_rnf02_token_con_firma_ajena_devuelve_401`; `test_rnf02_token_de_usuario_inexistente_devuelve_401`; `test_rnf02_tecnico_devuelve_403_rol_no_permitido_sin_datos`; `test_rnf02_recepcionista_accede_a_las_cinco_operaciones`; `test_rnf02_sin_sesion_cuerpo_invalido_devuelve_401_y_no_422` (POST `/ordenes` y `/clientes`, también con Técnico → 403); `test_rnf02_rechazo_no_crea_ni_modifica_registros` (cuenta clientes, equipos, órdenes y la cola; el `id_op` no queda registrado); `test_rnf02_rol_se_lee_de_la_base_en_cada_solicitud` (cambiar el rol del usuario tras iniciar sesión cambia el resultado); `test_rnf02_logout_devuelve_204_y_revoca_el_token` (después, cualquier operación con ese token → 401); `test_rnf02_logout_dos_veces_el_segundo_devuelve_401`; `test_rnf02_logout_sin_sesion_devuelve_401`; `test_rnf02_logout_permitido_a_cualquier_rol`; `test_rnf02_logout_purga_tokens_revocados_vencidos`; `test_rnf02_docs_y_openapi_siguen_publicos`; `test_rnf02_rn10_concurrencia_con_sesion_de_recepcionista` (varias solicitudes simultáneas de `POST /ordenes` con el mismo `id_op`, reutilizando el patrón de `tests/test_cu01_6a_idempotencia.py`: una sola orden y cola +1; confirma que el control de acceso no rompe la serialización, research D7)
- [X] T013 [P] [US1] Escribir `tests/test_rnf02_seed_usuarios.py` (RNF-02; principio VI): `test_rnf02_seed_crea_los_dos_usuarios_con_hash_y_rol`; `test_rnf02_seed_es_idempotente_no_duplica`; `test_rnf02_seed_actualiza_el_hash_si_cambia_la_contraseña`; `test_rnf02_seed_falla_con_mensaje_claro_si_falta_una_contraseña`; `test_rnf02_seed_no_guarda_la_contraseña_en_claro`. Las contraseñas se generan con `secrets` en la prueba; `cargar_usuarios` debe aceptar una fábrica de sesiones para usar la base temporal
- [X] T014 [US1] Actualizar `tests/conftest.py` sin romper las pruebas de 001 (RNF-02): fixture automática que fija `BYTETRACK_JWT_SECRET` con `secrets.token_urlsafe(48)` y borra `BYTETRACK_SESION_MINUTOS` del entorno (con `monkeypatch`); fixture `crear_usuario(nombre_usuario, clave, rol)` que inserta con `hashear_clave`; sobrescribir `get_session` **y** `get_session_seguridad` con la misma fábrica de sesiones; `client` pasa a iniciar sesión por `POST /auth/token` como un Recepcionista creado con una contraseña aleatoria y deja la cabecera `Authorization: Bearer` en el cliente (así las pruebas de C1 `tests/test_cu0*.py` no cambian); fixtures `client_sin_sesion` y `client_tecnico`. Depende de T011
- [X] T015 [P] [US1] Actualizar `tests/test_trazabilidad_swagger.py` (principio I): 7 operaciones; la etiqueta de las operaciones de acceso es `CU-01 · Acceso (RNF-02)` (ajustar la expresión para aceptar `GUI-xx` o `Acceso (RNF-02)`); `/auth/token` y `/auth/logout` citan `RNF-02` y `CU-01` en su descripción; cada una de las cinco operaciones de recepción declara respuestas 401 y 403 en el esquema OpenAPI

### Implementation for User Story 1

- [X] T016 [US1] Implementar `app/api/auth.py` (RNF-02; etiqueta `CU01_ACCESO`; descripciones que citan «precondición de CU-01» y `RNF-02`): `POST /auth/token` con `OAuth2PasswordRequestForm`, `response_model=TokenOut`, usando `get_session_seguridad` y `auth_service.iniciar_sesion`; `POST /auth/logout` con `status_code=204`, que obtiene el token con `esquema_oauth2`, usa `usuario_actual` (sin exigir rol) y `auth_service.cerrar_sesion`; respuestas 401 documentadas según [contracts/api-acceso.md](contracts/api-acceso.md). Depende de T011
- [X] T017 [P] [US1] Proteger `app/api/clientes.py` (RNF-02): `APIRouter(dependencies=[Depends(exigir_recepcionista)])`, añadir `401` y `403` (`ErrorOut`) a `responses` de `GET /clientes/{dni}` y `POST /clientes` y citar `RNF-02` en sus descripciones, sin cambiar firmas ni reglas
- [X] T018 [P] [US1] Proteger `app/api/tecnicos.py` (RNF-02): misma dependencia a nivel de router, respuestas 401/403 documentadas y `RNF-02` citado en la descripción de `GET /tecnicos/disponibles`
- [X] T019 [P] [US1] Proteger `app/api/ordenes.py` (RNF-02): misma dependencia a nivel de router, respuestas 401/403 documentadas y `RNF-02` citado en las descripciones de `GET /ordenes/costo-revision-inicial` y `POST /ordenes`
- [X] T020 [US1] Actualizar `app/main.py` (RNF-02; research D1, D6 y D8): en el ciclo de vida llamar primero a `config.cargar_entorno()`, luego `config.clave_jwt()` (la aplicación no arranca sin una clave válida) y después `crear_tablas()`; el manejador de `ErrorDominio` debe pasar `headers=error.headers`; incluir el router de `app/api/auth.py`; montar `StaticFiles(directory=<app/web>, html=True)` en `/` **después** de registrar todos los routers; actualizar la descripción de la aplicación para citar RNF-02. Depende de T005, T016 a T019
- [X] T021 [P] [US1] Ampliar `app/seed.py` (RNF-02; principio VI): `cargar_usuarios(fabrica=None)` que, con `config.credenciales_iniciales()`, crea o actualiza cada usuario usando `hashear_clave` y `UsuarioRepository`; `python -m app.seed` llama primero a `config.cargar_entorno()`, mantiene la carga de técnicos de 001 y, si falta una contraseña, termina con código distinto de cero y un mensaje que nombra la variable faltante. Sin contraseñas en el código
- [X] T022 [P] [US1] Crear `app/web/index.html` y `app/web/css/estilos.css` (RNF-02; GUI-01; contrato de interfaz): documento `lang="es"` con `<script type="module" src="/js/app.js">`, sin scripts en línea ni recursos externos. Vistas (todas con `hidden` salvo la activa): `vista-login` con `login-usuario`, `login-clave` (tipo contraseña), `login-entrar` («Iniciar sesión») y `login-error`; `vista-rechazo-rol` con `rechazo-mensaje` («Su rol no tiene acceso a las operaciones de recepción»); `vista-recepcion` (contenedor vacío por ahora). Encabezado visible en rechazo y recepción con `sesion-etiqueta` («Recepcionista · sesión activa», solo con ese rol) y `cerrar-sesion` («Cerrar sesión»). Cada elemento lleva `id` y `data-trace` según el contrato (`RNF-02`, `GUI-01`). Estilos con los colores y la distribución de los prototipos (encabezado azul marino, botones azules, tarjetas blancas), diseño de una columna que funcione en pantallas estrechas
- [X] T023 [P] [US1] Crear `app/web/js/api.js` (RNF-02; research D9): guardar y leer la sesión (`token` y `rol`) en `sessionStorage` con `try/catch` (puede no estar disponible); `llamar(metodo, ruta, { cuerpo, formulario })` que envía `Authorization: Bearer`, devuelve `{ estado, datos }` con el JSON del servidor y, ante **401** en cualquier llamada que no sea el inicio de sesión, borra la sesión y avisa a `app.js` para volver a `vista-login` con «Su sesión expiró»; ante **403** avisa para mostrar `vista-rechazo-rol`; los fallos de red se lanzan como un error propio para que cada pantalla muestre un mensaje general sin datos técnicos. No usar `innerHTML` ni cargar scripts externos
- [X] T024 [US1] Crear `app/web/js/login.js` y `app/web/js/app.js` (RNF-02; FR-001 a FR-007): `app.js` expone `mostrarVista(nombre)` (muestra una sola vista y el encabezado según corresponda; sin sesión → `vista-login`; rol `TECNICO` → `vista-rechazo-rol`; rol `RECEPCIONISTA` → `vista-recepcion`), lee la sesión de `sessionStorage` al cargar y escucha el aviso de 401/403 de `api.js`. `login.js` envía `POST /auth/token` como `application/x-www-form-urlencoded` (`username`, `password`), guarda `access_token` y `rol`, muestra «Usuario o contraseña incorrectos» en `login-error` ante 401, valida usuario y contraseña obligatorios, deshabilita `login-entrar` durante el envío y, en `cerrar-sesion`, llama a `POST /auth/logout`, borra la sesión y vuelve a `vista-login` **aunque la llamada falle** (desviación D3). Todo texto con `textContent`. Depende de T022 y T023

**Checkpoint**: `uv run pytest` pasa completo (las pruebas de 001 siguen intactas con el `client` autenticado) y los ítems A1 a A7 de [checklists/verificacion-manual.md](checklists/verificacion-manual.md) se verifican en el navegador

---

## Phase 4: User Story 2 - Buscar un cliente por DNI y cargar sus equipos en GUI-01 (Priority: P1)

**Goal**: En GUI-01, la Recepcionista busca un cliente por DNI y ve sus datos y sus equipos; «Registrar nuevo cliente» solo se habilita si el DNI no existe (CU-05; RF-01; RN-01; FR-008 a FR-012).

**Independent Test**: Con un cliente de dos equipos y un DNI inexistente, buscar ambos en GUI-01 y comprobar datos, selector y habilitación del botón; ítems B1, B2, C1, C2 y D1 de la lista manual. La operación de API ya está probada (`tests/test_cu05_buscar_cliente.py`, de 001).

- [X] T025 [US2] Agregar a `app/web/index.html` y `app/web/css/estilos.css` (GUI-01; RF-01; contrato de interfaz) dentro de `vista-recepcion`: `encabezado-titulo` («ByteTrack v2.0 · Recepción  GUI-01 · CU-01 / CU-05»), `flujo-estados` (Recepcionado, Presupuestado, Aprobado, Listo, Entregado, con «Recepcionado» resaltado y sin ninguna acción) y la sección «1. Cliente (CU-05)» con `dni` («DNI (8 dígitos)»), `buscar-cliente` («Buscar cliente»), `registrar-cliente-abrir` («Registrar nuevo cliente», deshabilitado al inicio), `dni-error` («El DNI debe tener 8 dígitos») y `cliente-resumen`. Cada elemento con `id` y `data-trace` del contrato. Depende de T022
- [X] T026 [US2] Crear `app/web/js/recepcion.js` (CU-05; RF-01; RN-01; FR-009 a FR-012) con el estado de la recepción (`cliente`, `equipos`, `dniBuscado`) y `iniciarRecepcion()`, que `app.js` invoca al mostrar `vista-recepcion`: «Buscar cliente» valida `^[0-9]{8}$` (si no cumple, muestra `dni-error` y no consulta) y llama `GET /clientes/{dni}`; 200 → `cliente-resumen` con «[Nombres Apellidos] · [teléfono] · Cliente encontrado», guarda los equipos y deshabilita `registrar-cliente-abrir`; 404 `CLIENTE_NO_ENCONTRADO` → «Cliente no encontrado» y habilita `registrar-cliente-abrir`; deshabilita «Buscar cliente» durante la consulta. Exponer `cargarCliente(datos)` para la historia US5. Todo texto con `textContent`. Depende de T024 y T025

**Checkpoint**: Ítems B1, B2, C1, C2 y D1 de la lista manual verificados

---

## Phase 5: User Story 3 - Generar la orden de servicio desde GUI-01 (Priority: P1)

**Goal**: Con el cliente cargado, la Recepcionista completa equipo, falla y técnico, genera la orden y ve «N.° … listo para imprimir» (CU-01, curso básico; RF-01; RF-02; RN-03; FR-014 a FR-020, FR-022, FR-024, FR-025).

**Independent Test**: Con un cliente existente y un técnico disponible, completar y generar la orden y ver el N.° de orden; dejar campos obligatorios vacíos y ver que no se envía; ítems B3 a B5, C4 a C9 de la lista manual y `tests/test_cu01_tecnicos_cola.py`.

### Tests for User Story 3 ⚠️

- [X] T027 [P] [US3] Escribir `tests/test_cu01_tecnicos_cola.py` (RN-03; CU-01 paso 6; FR-019) y comprobar que falla: `test_rn03_tecnicos_disponibles_incluye_cola` (cada elemento trae `id`, `nombres`, `apellidos` y `cola` entera igual a `Tecnico.cola`); `test_rn03_cola_refleja_la_orden_recien_generada` (tras `POST /ordenes`, la cola del técnico sube en 1); `test_rn03_el_conjunto_de_tecnicos_devueltos_no_cambia` (solo `disponible = true`, lista vacía si no hay ninguno)

### Implementation for User Story 3

- [X] T028 [US3] Agregar `cola: int` a `TecnicoOut` en `app/models/schemas.py` (RN-03; CU-01 paso 6) como único cambio de esa respuesta, y confirmar que `app/services/orden_service.py` (`listar_tecnicos_disponibles`) devuelve objetos que lo llenan sin cambiar qué técnicos se devuelven. Actualizar la descripción de `GET /tecnicos/disponibles` en `app/api/tecnicos.py` para mencionar `cola`. Depende de T027 (prueba escrita antes)
- [X] T029 [US3] Agregar a `app/web/index.html` y `app/web/css/estilos.css` (RF-01; RF-02; GUI-01) dentro de `vista-recepcion`, tras la sección 1: sección «2. Equipo (RF-01 / RF-02)» con `equipo-selector`, `equipo-tipo` (campo de **texto libre**, desviación D1), `equipo-marca`, `equipo-modelo`, `equipo-serie`, `acc-cargador` («Cargador original»), `acc-funda` («Funda / maletín») y `estado-fisico`; sección «3. Orden de servicio» con `falla`, `tecnico`, `costo-revision` (solo lectura) y `estado-inicial` («Estado inicial: RECEPCIONADO»); y el pie con `alerta-error`, `confirmacion-orden` (recuadro verde), `cancelar-orden` («Cancelar») y `generar-orden` («Generar orden de servicio»). Etiquetas y notas «(obligatorio)» como en el prototipo `image7.png`; cada elemento con `id` y `data-trace` del contrato. Depende de T025
- [X] T030 [US3] Ampliar `app/web/js/recepcion.js` (CU-01; RF-01; RF-02; RN-03; FR-014 a FR-020, FR-022, FR-024, FR-025): al iniciar la recepción cargar `GET /ordenes/costo-revision-inicial` en `costo-revision` («S/ 40.00») y `GET /tecnicos/disponibles` en `tecnico` con el formato «[nombres] [apellidos] ([N] en cola)» (sin técnicos → mensaje «No hay técnicos disponibles» y `generar-orden` deshabilitado); `equipo-selector` lista los equipos del cliente más la opción «Ingresar equipo nuevo» (al elegir uno existente se rellenan sus datos y se bloquean los cuatro campos; con «nuevo» quedan editables); `accesorios` se arma con los textos de las casillas marcadas separados por «, » (`null` si no hay ninguna); validar antes de enviar cliente cargado, equipo (existente o los cuatro campos), `estado-fisico`, `falla` y `tecnico`, marcando cada campo faltante (`aria-invalid` y estilo) sin enviar; `POST /ordenes` con `id_op`, `dni` (el del cliente cargado), `equipo_id` **o** `equipo {tipo, marca, modelo, numero_serie}`, `accesorios`, `estado_fisico`, `falla_reportada` y `tecnico_id` numérico; 201 o 200 → `confirmacion-orden` «N.° [código] listo para imprimir · el técnico recibe +1 en su cola», limpiar el formulario conservando la confirmación, recargar los técnicos (cola actualizada) y generar un ID de operación nuevo; los demás rechazos (`CLIENTE_NO_ENCONTRADO`, `TECNICO_NO_DISPONIBLE`, `SIN_TECNICOS_DISPONIBLES`, `SERIE_EN_OTRO_CLIENTE`, `ID_OP_CONFLICTO`) → `alerta-error` con el `mensaje` del servidor; error de red o inesperado → texto general sin datos técnicos y se conserva lo ingresado; `cancelar-orden` descarta todo (DNI, cliente, equipo, orden, mensajes), oculta la confirmación y genera un ID de operación nuevo. El ID de operación se genera con `crypto.getRandomValues`: `OP-` + 12 caracteres hexadecimales (research D11). Depende de T026, T028 y T029

**Checkpoint**: `uv run pytest` pasa completo; ítems B3 a B5 (salvo el pie, ver US6) y C4 a C9 de la lista manual verificados

---

## Phase 6: User Story 4 - Ver la alerta E01 cuando el equipo ya tiene una orden activa (Priority: P1)

**Goal**: Si el número de serie ya tiene una orden activa, GUI-01 bloquea la generación y muestra E01 con el N.° de la orden activa (CU-01 curso 5a; RF-02; RN-02; FR-023).

**Independent Test**: Generar una orden y, sin entregarla, intentar otra con el mismo número de serie; ver E01 con el N.° de la primera; ítems E1 a E3 de la lista manual. El comportamiento de la API ya está probado (`tests/test_cu01_5a_orden_activa.py`, de 001).

- [X] T031 [P] [US4] Agregar a `app/web/index.html` y `app/web/css/estilos.css` (RF-02; RN-02; GUI-01) el elemento `alerta-e01` (alerta roja, oculta por defecto, `data-trace="RF-02 RN-02"`) dentro de la sección «2. Equipo», como en el prototipo `image7.png`. Depende de T029
- [X] T032 [US4] Ampliar `app/web/js/recepcion.js` (CU-01 curso 5a; RN-02; FR-023): ante 409 con `codigo == "E01"` mostrar en `alerta-e01` el texto «Este número de serie ya posee la Orden activa N.° [X] en laboratorio» con `detalle.orden_activa`, sin mostrar `alerta-error`, sin limpiar lo ingresado y sin cambiar el ID de operación; ocultar `alerta-e01` al cambiar `equipo-selector` o cualquier campo de equipo, de orden o `dni`, y al cancelar. Depende de T030 y T031

**Checkpoint**: Ítems E1 a E3 de la lista manual verificados

---

## Phase 7: User Story 5 - Registrar un cliente nuevo desde el modal GUI-02 (Priority: P2)

**Goal**: Cuando el DNI no existe, la Recepcionista abre GUI-02, guarda el cliente y GUI-01 queda con el cliente cargado; si el DNI ya existía, se avisa y se carga el existente sin duplicar (CU-06; CU-01 cursos 2a y 2b; RF-01; RN-01; FR-028 a FR-032).

**Independent Test**: Buscar un DNI inexistente, abrir GUI-02, guardar y ver el cliente en GUI-01; repetir con el mismo DNI y ver el aviso sin duplicados; probar campos faltantes y «Cancelar»; ítems D1 a D6 de la lista manual. La API ya está probada (`tests/test_cu06_registrar_cliente.py`, de 001).

- [X] T033 [US5] Agregar a `app/web/index.html` y `app/web/css/estilos.css` (RF-01; GUI-02) el modal `modal-cliente` (`role="dialog"`, `aria-modal="true"`, oculto por defecto, fondo oscurecido como en `image10.png`) con el título «Registrar nuevo cliente · CU-06 / GUI-02» y los elementos `cli-dni` (nota «8 dígitos. Si ya existe se avisa «El DNI ya está registrado» y se abre el cliente existente, sin duplicar»), `cli-nombres`, `cli-apellidos`, `cli-telefono` (los cuatro con «(*)»), `cli-correo` («Correo (opcional)»), `cli-nota` («(*) campo obligatorio · al guardar vuelve a GUI-01 con el cliente cargado»), `cli-aviso`, `cli-error`, `cli-guardar` («Guardar cliente») y `cli-cancelar` («Cancelar»), cada uno con `id` y `data-trace` del contrato. Depende de T025
- [X] T034 [US5] Crear `app/web/js/modal_cliente.js` (CU-06; RN-01; FR-028 a FR-032): `abrirModal(dni)` muestra el modal con `cli-dni` precargado con el DNI buscado, limpia los demás campos y mensajes y enfoca el primer campo vacío; «Guardar cliente» valida DNI `^[0-9]{8}$` y que Nombres, Apellidos y Teléfono no estén vacíos tras recortar espacios (señalando cada campo en `cli-error` y con `aria-invalid`, sin enviar); `POST /clientes` con `correo` en `null` si está vacío; **201** → cierra el modal y llama a `cargarCliente(datos)` de `recepcion.js` (curso 2a); **200 con `ya_registrado`** → muestra «El DNI ya está registrado» en `cli-aviso`, carga el cliente existente y sus equipos en GUI-01 con `cargarCliente(datos)`, y deja el modal abierto con `cli-guardar` deshabilitado hasta que se edite `cli-dni` (curso 2b; cerrarlo con «Cancelar» no deshace la carga); `cli-cancelar` cierra sin registrar y conserva el estado de GUI-01; deshabilita «Guardar cliente» durante el envío; un error de red muestra un texto general en `cli-error`. Todo texto con `textContent`. Depende de T026 y T033
- [X] T035 [US5] Conectar el modal en `app/web/js/recepcion.js` (CU-01 curso 2a; FR-012, FR-028, FR-030): `registrar-cliente-abrir` llama a `abrirModal(dniBuscado)`; `cargarCliente(datos)` rellena `dni` con el DNI del cliente, actualiza `dniBuscado`, `cliente-resumen` y `equipo-selector` (vacío si el cliente no tiene equipos, solo con «Ingresar equipo nuevo»), deshabilita `registrar-cliente-abrir` y deja la recepción lista para el paso del equipo. Depende de T034

**Checkpoint**: Ítems D1 a D6 de la lista manual verificados

---

## Phase 8: User Story 6 - Reintentar la generación de la orden sin duplicarla (Priority: P2)

**Goal**: GUI-01 muestra el ID de operación y, ante doble clic o reenvío, conserva el mismo identificador para que el servidor devuelva la orden ya creada sin duplicarla (CU-01 curso 6a; RF-02; RNF-04; RN-10; FR-021, FR-026, FR-027).

**Independent Test**: Pulsar dos veces «Generar orden de servicio» y comprobar una sola orden con el mismo N.°; tras confirmar o cancelar, ver un ID de operación nuevo; ítems F1 a F5 de la lista manual. El comportamiento del servidor ya está probado (`tests/test_cu01_6a_idempotencia.py`, de 001, y T012 con el control de acceso activo).

- [X] T036 [P] [US6] Agregar a `app/web/index.html` (RNF-04; GUI-01) el elemento `id-operacion` en el pie de la pantalla (`data-trace="RNF-04"`, texto «ID de operación OP-… · repetir el envío no duplica la orden (RNF-04)») y su estilo en `app/web/css/estilos.css`. Depende de T029
- [X] T037 [US6] Ampliar `app/web/js/recepcion.js` (CU-01 curso 6a; RNF-04; RN-10; FR-021, FR-026, FR-027): mostrar en `id-operacion` el ID de operación vigente cada vez que cambie; mientras haya un envío en curso, `generar-orden` queda deshabilitado **y** una bandera interna ignora cualquier otro envío (doble clic); si el envío falla (rechazo de negocio, validación del servidor o error de red) el ID de operación **no cambia** y se reutiliza en el reintento; se genera uno nuevo solo al iniciar la recepción, tras confirmar la orden (201 o 200) y tras «Cancelar»; el 200 de reintento muestra la misma confirmación que el 201. Depende de T030 y T036

**Checkpoint**: Ítems B5 y F1 a F5 de la lista manual verificados

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Trazabilidad de la interfaz, verificación final y registro de resultados

- [X] T038 [P] Escribir `tests/test_interfaz_estatica.py` (principio VIII; SC-006; principio VI): `test_interfaz_se_sirve_en_la_raiz_y_sus_modulos_js` (GET `/` → 200 HTML; `/js/app.js`, `/js/api.js`, `/js/login.js`, `/js/recepcion.js`, `/js/modal_cliente.js` y `/css/estilos.css` → 200); `test_interfaz_el_conjunto_de_ids_coincide_con_el_contrato` (con `html.parser`, las `id` de `index.html` son exactamente las de [contracts/ui-gui01-gui02.md](contracts/ui-gui01-gui02.md), más las de las vistas `vista-login`, `vista-rechazo-rol`, `vista-recepcion` y `modal-cliente`, escritas como constante en la prueba); `test_interfaz_cada_elemento_declara_data_trace_con_codigo_aup` (los códigos permitidos son `RNF-02`, `RF-01`, `RF-02`, `RN-01`, `RN-02`, `RN-03`, `RNF-04`, `GUI-01` y `GUI-02`); `test_interfaz_sin_controles_fuera_del_contrato` (todo `input`, `select`, `textarea` y `button` tiene un `id` del contrato; no hay `table`, `ul` ni `ol` de listados); `test_interfaz_sin_innerhtml_ni_recursos_externos` (los `.js` no contienen `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write` ni `eval(`; ni el HTML ni los `.js` contienen URL `http://` o `https://`); `test_env_example_no_contiene_valores_secretos` (`BYTETRACK_JWT_SECRET`, `BYTETRACK_RECEPCIONISTA_CLAVE` y `BYTETRACK_TECNICO_CLAVE` están presentes con valor vacío); `test_gitignore_ignora_env_pero_no_env_example`. Depende de T002 y de las historias US1 a US6
- [X] T039 Barrido de secretos y de alcance (principios I y VI): ejecutar `git grep -n -i -E "(secret|clave|password|contrase)[a-z_]*\s*[=:]\s*['\"][^'\"]+['\"]" -- app tests .env.example` y comprobar que no queda ninguna contraseña ni clave literal (las pruebas generan las suyas); confirmar con `git status` que no hay `.env`, `*.db` ni credenciales para confirmar, y con `git diff --stat -- docs/aup` que `docs/aup/` no cambió
- [X] T040 Ejecutar de principio a fin [quickstart.md](quickstart.md) en un entorno limpio: `uv sync`, copiar `.env.example` a `.env` y completar valores propios, `uv run python -m app.seed` (comprobar que falla con mensaje claro si se quita una contraseña) y `uv run uvicorn app.main:app --reload`; comprobar también que la aplicación **no arranca** sin `BYTETRACK_JWT_SECRET` o con menos de 32 caracteres, y que Swagger UI («Authorize») permite probar el 403 del Técnico. Corregir el quickstart si algún comando difiere
- [ ] T041 Ejecutar la lista completa [checklists/verificacion-manual.md](checklists/verificacion-manual.md) (35 ítems) en el navegador y registrar en ella el resultado de cada ítem, la fecha y el navegador; todo ítem que no cumpla se corrige en la historia correspondiente y se repite. Verificar además que no existe ningún listado, edición, reporte ni gestión de usuarios (ítem B6)
- [X] T042 Ejecutar `uv run pytest` y reportar el resultado completo (cuántas pruebas pasaron y, si alguna falla, su salida), confirmando que las pruebas de 001 siguen pasando sin modificaciones salvo `tests/conftest.py` y `tests/test_trazabilidad_swagger.py`. La funcionalidad termina cuando `uv run pytest` pasa completo **y** la lista manual está completada y registrada (definición de terminado de `AGENTS.md`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias; T001 antes de cualquier tarea que importe las bibliotecas
- **Foundational (Phase 2)**: depende de T001; **bloquea** todas las historias. Orden interno: T003 (prueba) → T004; T005, T006, T007, T008 en paralelo; T009 (tras T006); T010 (tras T004, T005, T007, T009); T011 (tras T010)
- **US1 (Phase 3)**: depende de Phase 2. Es la base de la interfaz (vistas, sesión) y del control de acceso que usan las demás
- **US2 → US3 → US4**: cada una amplía `index.html` y `recepcion.js`; se hacen en ese orden (P1)
- **US5 y US6 (P2)**: dependen de US3 (y US5 de US2); entre sí son independientes
- **Polish (Phase 9)**: depende de todas las historias

### User Story Dependencies

- **US1 (P1)**: tras Foundational; independiente de las demás
- **US2 (P1)**: tras US1 (necesita el esqueleto de la interfaz y la sesión)
- **US3 (P1)**: tras US2 (necesita el cliente cargado); la cola de técnicos (T027, T028) puede hacerse antes
- **US4 (P1)**: tras US3 (usa el envío de la orden)
- **US5 (P2)**: tras US2; se integra con `cargarCliente` de US2 y con el flujo de US3
- **US6 (P2)**: tras US3 (usa el ID de operación y el envío)

### Within Each User Story

- Las pruebas se escriben primero y deben fallar; luego modelos/servicios/endpoints; luego la interfaz
- Las tareas que tocan el mismo archivo (`index.html`, `recepcion.js`, `estilos.css`, `main.py`) no son paralelas entre sí

### Parallel Opportunities

- Phase 1: T002 con T001
- Phase 2: T005, T006, T007 y T008 a la vez (archivos distintos); T003 puede escribirse mientras tanto
- US1: T012, T013 y T015 (pruebas); T017, T018, T019 (routers), T021 (seed), T022 y T023 (interfaz) a la vez
- US3: T027 junto con T029; US4: T031; US6: T036; Polish: T038

---

## Parallel Example: User Story 1

```text
# Pruebas de US1 (archivos distintos):
Task: "T012 tests/test_rnf02_acceso.py"
Task: "T013 tests/test_rnf02_seed_usuarios.py"
Task: "T015 tests/test_trazabilidad_swagger.py"

# Protección de routers y base de la interfaz:
Task: "T017 app/api/clientes.py"   Task: "T018 app/api/tecnicos.py"   Task: "T019 app/api/ordenes.py"
Task: "T021 app/seed.py"           Task: "T022 app/web/index.html + css"   Task: "T023 app/web/js/api.js"
```

---

## Implementation Strategy

### MVP First (US1 a US4, todas P1)

1. Phase 1 y Phase 2
2. US1 y validar: acceso por rol funcionando, 401/403 y cierre de sesión
3. US2 → US3 → US4: la Recepcionista busca, genera la orden y ve E01; este es el **MVP funcional** de la interfaz
4. **PARAR y VALIDAR** con `uv run pytest` y los ítems A a C y E de la lista manual

### Incremental Delivery

1. Setup + Foundational → base de seguridad lista
2. US1 → probar → US2 → probar → US3 → probar → US4 → probar (MVP)
3. US5 (cliente nuevo) → probar
4. US6 (ID de operación visible y reintento) → probar
5. Polish → trazabilidad estática, barrido de secretos, quickstart y lista manual completa

### Alcance (principios VII y VIII)

Fuera de esta funcionalidad: listados, edición, reportes, gestión de usuarios, bloqueo por intentos fallidos, recuperación de contraseña, refresco de token, GUI-03 a GUI-06, CU-02, CU-03, CU-04, CU-07 y CU-08. Pendientes registrados en la spec: parte restante de RNF-02, RN-03 (parte de acceso), RF-03 a RF-06, RNF-01, RNF-03 y RN-04 a RN-09 y RN-11. No crear tareas para ellos ni agregar elementos a la interfaz que no estén en el contrato.

---

## Notes

- [P] = archivos distintos y sin dependencias pendientes
- La etiqueta [Story] vincula cada tarea con su historia para trazabilidad
- Cada operación nueva declara su `CU-xx` y `RNF-02` en la descripción y cada validación cita su código (AGENTS.md reglas 2 y 3)
- Las pruebas de 001 no se modifican salvo `tests/conftest.py` (T014) y `tests/test_trazabilidad_swagger.py` (T015)
- No hay pruebas en navegador: la pantalla se verifica con la lista manual (decisión del usuario); el JavaScript de FR-021 y FR-027 solo tiene esa red de seguridad
- Confirmar después de cada tarea o grupo lógico que `uv run pytest` sigue pasando
