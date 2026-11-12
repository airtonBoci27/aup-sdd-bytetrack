# Implementation Plan: Interfaz web de recepción con acceso por rol (Iteración C1)

**Branch**: `002-interfaz-recepcion-rol` | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-interfaz-recepcion-rol/spec.md`

## Summary

Se entrega la pantalla de recepción (GUI-01) con el modal de registro de cliente (GUI-02) y se protege la API de C1 con inicio de sesión y acceso por rol (RNF-02): solo un usuario con rol Recepcionista y sesión activa usa CU-05, CU-06 y CU-01; el Técnico recibe un rechazo; la sesión se puede cerrar.

Enfoque técnico, según la indicación del usuario y la arquitectura candidata (`caso.md` §2.6):

- **Interfaz**: HTML, CSS y JavaScript sin framework en `app/web/`, servidos por la misma aplicación FastAPI en `/`. Consume la API de 001 sin cambiar sus reglas.
- **Acceso**: flujo OAuth2 de contraseña (`POST /auth/token`) que emite un JWT HS256 (PyJWT); una dependencia de FastAPI aplicada a los routers de recepción exige sesión activa y rol Recepcionista (401 `NO_AUTENTICADO`, 403 `ROL_NO_PERMITIDO`). El cierre de sesión revoca el `jti` del token en una tabla.
- **Usuarios y secretos**: la tabla `usuario` guarda solo hashes `scrypt` (biblioteca estándar) y se llena con `app.seed` desde variables de entorno. La clave de firma (`BYTETRACK_JWT_SECRET`) y las contraseñas se leen de un `.env` ignorado por git, cargado con `python-dotenv` al arrancar (nunca al importar). Un `.env.example` versionado, con los nombres de las variables y sin valores secretos, indica qué configurar (principio VI; datos iniciales de la fase de Transición).
- **Único cambio en una operación existente, además del acceso**: `GET /tecnicos/disponibles` agrega `cola` (solo lectura) para mostrar «(N en cola)» como en GUI-01.
- **Hallazgo de diseño** (research D7): la verificación de sesión usa una sesión de base de datos propia y breve, porque consultar con la misma sesión de la solicitud deshabilitaría el `BEGIN IMMEDIATE` del que dependen RN-02 y RN-10.

## Technical Context

**Language/Version**: Python 3.12 (sin cambios); JavaScript del navegador (módulos ES nativos, sin compilación).

**Primary Dependencies**: FastAPI, Uvicorn y SQLAlchemy 2.x (de 001). **Nuevas (ejecución)**, aprobadas en la enmienda 1.3.0 de la constitución: `pyjwt` (JWT HS256), `python-multipart` (formulario OAuth2 de FastAPI) y `python-dotenv` (`.env`). Sin dependencias nuevas de desarrollo ni de pruebas. Justificación y alternativas en [research.md](research.md) D12. Versiones exactas por `uv.lock` (resueltas hoy: pyjwt 2.15.1, python-multipart 0.0.33, python-dotenv 1.2.4).

**Storage**: SQLite local (sin cambios) con dos tablas nuevas: `usuario` y `token_revocado` (ver [data-model.md](data-model.md)). Sin migraciones: se crean con `create_all`.

**Testing**: pytest (`uv run pytest`): pruebas de API con `TestClient` (acceso por rol, configuración, usuarios iniciales, cola de técnicos) y pruebas estáticas de la interfaz (trazabilidad de cada elemento). El comportamiento de la pantalla se verifica con la lista de verificación manual [checklists/verificacion-manual.md](checklists/verificacion-manual.md); los cursos `CU-01-B`, `2a`, `2b`, `5a` y `6a` siguen cubiertos por las pruebas de API de 001. No se automatizan pruebas en navegador (decisión del usuario). Las contraseñas y la clave de firma de las pruebas se generan al ejecutarlas.

**Target Platform**: Equipo local (macOS/Linux) con `uv run uvicorn app.main:app --reload`; navegador moderno con módulos ES. Sin nube.

**Project Type**: web-service con interfaz web estática (una sola aplicación y un solo origen).

**Performance Goals**: Sin objetivo formal (RNF-03 sigue pendiente). Sin metas de tiempo propias: AUP no las define para esta funcionalidad.

**Constraints**: Sin secretos en el repositorio (VI); `.env` ignorado por git y ubicable fuera del proyecto; la clave de firma es obligatoria (≥ 32 caracteres) y su ausencia impide arrancar; interfaz sin framework ni compilación; los textos del servidor se insertan con `textContent`; las reglas de C1 no cambian; sin llamadas a servicios externos.

**Scale/Scope**: 3 vistas (inicio de sesión, rechazo por rol, GUI-01 con modal GUI-02), 2 operaciones nuevas (`/auth/token`, `/auth/logout`), 5 operaciones existentes protegidas, 2 tablas nuevas, ~35 elementos de interfaz trazados.

## Desviaciones respecto de la arquitectura candidata (AUP 2.6) y de los prototipos

Se actualiza la tabla de [001](../001-recepcion-orden-servicio/plan.md): con esta funcionalidad **OAuth2 con JWT se implementa**.

| Elemento | Adaptación | Justificación |
|----------|-----------|---------------|
| Frontend estático en S3 + CloudFront + WAF | Archivos estáticos servidos por la propia aplicación FastAPI | Prototipo local sin nube; un solo origen evita CORS. Se conserva el carácter estático del frontend (sin framework). |
| OAuth2 con JWT | Implementado: flujo de contraseña + JWT HS256, usuarios en SQLite | Cierra el riesgo R3 para las operaciones de recepción. HS256 porque no hay verificadores externos (research D2). |
| GUI-01 «Tipo» como lista | Campo de texto libre | D1 de la spec: AUP no enumera tipos. |
| GUI-01 «T02 · Marco Salazar (2 en cola)» | «[nombres] [apellidos] ([N] en cola)» | D2 de la spec: el código de técnico no existe en AUP. |
| Encabezado sin acción de sesión | «Cerrar sesión» | D3 de la spec: RNF-02 («sesiones activas»). |

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Verificación en este plan | Estado |
|-----------|---------------------------|--------|
| I. Documentación AUP como fuente de verdad | Se conservan RF-01, RF-02, RNF-02, RNF-04, CU-01/05/06, RN-01/02/03/10, E01, GUI-01/02. `docs/aup/` no se modifica. Las operaciones nuevas citan `CU-01` (precondición) y `RNF-02` en su descripción y etiqueta. Cada validación nueva cita su código (`RNF-02`). | PASA |
| II. Especificación antes que código | `spec.md` validado (checklist completo) precede a este plan y a `tasks.md`. Se actualizan la spec, el contrato y el plan de 001 para que no digan «sin autenticación» (ver abajo). | PASA |
| III. Pruebas automatizadas obligatorias | `RNF-02` se prueba de forma automatizada en la API (nombre de prueba con su código). `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a`, `CU-01-6a` y RN-01/02/03/10 conservan las pruebas automatizadas de 001, que siguen pasando con sesión de Recepcionista (fixture `client` autenticado) y con el control de acceso activo. Lo propio de la pantalla (campos, mensajes, E01, ID OP, doble clic, modal) se verifica con una lista manual cuyos ítems citan el mismo código `CU-01-<curso>`; el usuario decidió no automatizarlo en navegador. | PASA |
| IV. Arquitectura en capas | `api` (routers y dependencia de acceso) → `services/auth_service.py` → `repositories/usuario_repository.py` → `models`. Las funciones de hash y JWT son utilidades puras en `app/security.py`, sin acceso a datos. La interfaz web llama a la API por HTTP; no toca la base. | PASA |
| V. Simplicidad e integraciones | SQLite, sin servicios nuevos. Hash con la biblioteca estándar (sin dependencia). Sin integraciones externas, por lo que no se requieren dobles. | PASA |
| VI. Sin credenciales en el repositorio | Clave de firma y contraseñas solo por entorno/`.env` ignorado; el seed falla si faltan; la base guarda hashes; las pruebas generan sus valores; `.env.example` versionado solo con nombres de variables y sin valores secretos (permitido por el principio VI desde la enmienda 1.3.0). | PASA |
| VII. Alcance acotado | Pendientes registrados en la spec: parte restante de RNF-02, RN-03 de acceso, RNF-01, RNF-03, RF-03 a RF-06. Sin bloqueo por intentos, recuperación de contraseña ni refresco de token (research, pendientes). | PASA |
| VIII. Alcance cerrado | Matriz de trazabilidad en la spec; cada elemento de interfaz lleva `data-trace` y una prueba estática impide elementos fuera del contrato ([ui-gui01-gui02.md](contracts/ui-gui01-gui02.md)). Las tres desviaciones de prototipo están decididas por el usuario y registradas. | PASA |
| Restricciones Técnicas (dependencias) | Se agregan 3 dependencias de ejecución justificadas en research D12; la enmienda 1.3.0 de la constitución (aprobada por el usuario) las incorpora al stack. | PASA |

**Re-evaluación posterior al diseño (Fase 1)**: se mantiene PASA. El diseño no agrega capas ni servicios; la tabla `token_revocado` es el mínimo para cumplir el cierre de sesión (FR-007) con JWT. La condición de enmienda quedó resuelta con la constitución 1.3.0.

### Actualización de los documentos de 001 (indicación del usuario)

Hecha junto con este plan, para que no digan «sin autenticación»: [spec.md](../001-recepcion-orden-servicio/spec.md) (Assumptions, Alcance y Pendientes), [contracts/api-c1.md](../001-recepcion-orden-servicio/contracts/api-c1.md) (encabezado, `cola` en técnicos, 401/403) y [plan.md](../001-recepcion-orden-servicio/plan.md) (Constraints, desviaciones y Check). `tasks.md` de 001 es el registro histórico de lo construido y no se modifica.

## Project Structure

### Documentation (this feature)

```text
specs/002-interfaz-recepcion-rol/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0: decisiones técnicas y justificación de dependencias
├── data-model.md        # Fase 1: tablas usuario y token_revocado
├── quickstart.md        # Fase 1: configuración, ejecución y validación
├── contracts/
│   ├── api-acceso.md        # Fase 1: /auth/token, /auth/logout, 401/403, cola
│   └── ui-gui01-gui02.md    # Fase 1: elementos, ids y comportamiento de la interfaz
├── checklists/
│   ├── requirements.md       # Calidad de la especificación
│   └── verificacion-manual.md # Lista de verificación manual de la interfaz (GUI-01, GUI-02, RNF-02)
└── tasks.md             # Fase 2 (/speckit-tasks; NO lo crea /speckit-plan)
```

### Source Code (repository root)

Archivos nuevos marcados con `+`; modificados con `~`.

```text
app/
├── main.py                       ~ cargar_entorno() y validación de la clave al arrancar; routers de auth; montaje de app/web en "/" (al final); cabecera WWW-Authenticate en errores 401
├── config.py                     ~ cargar_entorno(), clave JWT (≥ 32 caracteres), duración de la sesión, credenciales iniciales
├── errors.py                     ~ CredencialesInvalidas, NoAutenticado, RolNoPermitido
├── security.py                   + hash scrypt/verificación y creación/decodificación de JWT (utilidades puras)
├── seed.py                       ~ además de técnicos: carga/actualiza usuarios desde el entorno
├── api/
│   ├── auth.py                   + POST /auth/token y POST /auth/logout (CU-01 · Acceso, RNF-02)
│   ├── seguridad.py              + oauth2_scheme, get_session_seguridad, dependencia exigir_recepcionista
│   ├── etiquetas.py              ~ etiqueta "CU-01 · Acceso (RNF-02)"
│   ├── clientes.py               ~ router con dependencia de acceso; respuestas 401/403 en Swagger
│   ├── tecnicos.py               ~ ídem
│   └── ordenes.py                ~ ídem
├── services/
│   └── auth_service.py           + iniciar_sesion, verificar_sesion, cerrar_sesion (RNF-02)
├── repositories/
│   └── usuario_repository.py     + usuarios y tokens revocados
├── models/
│   ├── entities.py               ~ Usuario, TokenRevocado
│   └── schemas.py                ~ TokenOut; TecnicoOut.cola
└── web/                          + interfaz estática (sin framework ni compilación)
    ├── index.html                  vistas de inicio de sesión, rechazo y GUI-01 con modal GUI-02
    ├── css/estilos.css
    └── js/
        ├── app.js                  arranque, vistas y sesión
        ├── api.js                  llamadas HTTP con Bearer; manejo de 401/403
        ├── login.js                inicio y cierre de sesión
        ├── recepcion.js            GUI-01 (cliente, equipo, orden, E01, ID OP)
        └── modal_cliente.js        GUI-02

tests/
├── conftest.py                   ~ usuarios de prueba, clave de firma generada, `client` autenticado como Recepcionista; fixtures client_sin_sesion y client_tecnico
├── test_rnf02_acceso.py          + RNF-02 (API)
├── test_rnf02_configuracion.py   + RNF-02 (clave, .env, hash)
├── test_rnf02_seed_usuarios.py   + RNF-02 (usuarios desde el entorno)
├── test_cu01_tecnicos_cola.py    + RN-03 / CU-01 paso 6 (cola)
├── test_interfaz_estatica.py     + trazabilidad de la interfaz (principio VIII)
└── test_trazabilidad_swagger.py  ~ 7 operaciones; etiqueta de acceso

.env.example                      + plantilla de variables sin valores secretos (principio VI; Transición)
pyproject.toml, uv.lock           ~ dependencias nuevas (pyjwt, python-multipart, python-dotenv)
```

**Structure Decision**: se conserva el proyecto único de 001 y se agrega `app/web/` para la interfaz, fuera de las capas Python porque no contiene lógica de servidor. El control de acceso es una dependencia de FastAPI declarada a nivel de router (los endpoints no cambian de firma) que delega en `auth_service` (principio IV). Los archivos de prueba se nombran por requisito o caso de uso y cada prueba lleva en su nombre el código que cubre.

## Complexity Tracking

> La constitución se enmendó a 1.3.0 para aprobar las dependencias (ver la última fila). Las dependencias están justificadas en [research.md](research.md) D12.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Tres dependencias de ejecución (`pyjwt`, `python-multipart`, `python-dotenv`) fuera del stack de la constitución | OAuth2 con JWT es un requisito explícito del usuario y de la arquitectura candidata; `python-multipart` es obligatoria para el formulario OAuth2 de FastAPI; `python-dotenv` es lo que lee el `.env` pedido | Escribir JWT y su validación a mano es criptografía propia; un login JSON no es OAuth2; un analizador de `.env` propio duplica una función estándar |
| Tabla `token_revocado` | FR-007: el cierre de sesión debe invalidar el token | Tokens sin estado no se pueden anular; la tabla solo guarda tokens vigentes |
| **Enmienda de la constitución (aplicada, 1.3.0)** | Restricciones Técnicas: «Añadir dependencias… fuera de este stack requiere justificación en el plan y enmienda de esta constitución si es permanente» | El usuario aprobó la enmienda MINOR 1.3.0 (2026-11-12): incorpora `pyjwt`, `python-multipart` y `python-dotenv` y aclara el principio VI para permitir `.env.example` sin valores. Su informe de impacto está en `.specify/memory/constitution.md`. Playwright quedó descartado por decisión del usuario. |
