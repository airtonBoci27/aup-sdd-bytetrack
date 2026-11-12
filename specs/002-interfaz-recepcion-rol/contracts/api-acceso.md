# Contrato de la API — Acceso por rol (RNF-02)

Complementa [../../001-recepcion-orden-servicio/contracts/api-c1.md](../../001-recepcion-orden-servicio/contracts/api-c1.md). Formato JSON salvo `POST /auth/token`, que es un formulario (flujo OAuth2 de contraseña, RFC 6749 §4.3). Errores en el formato uniforme `{codigo, mensaje, detalle}`.

Las dos operaciones nuevas se etiquetan en Swagger `CU-01 · Acceso (RNF-02)` y su descripción cita la precondición de CU-01 («sesión iniciada») y RNF-02.

## Resumen de operaciones nuevas

| Operación | Método y ruta | Requisito | Autenticación |
|-----------|---------------|-----------|---------------|
| Iniciar sesión | `POST /auth/token` | RNF-02; precondición de CU-01 | No |
| Cerrar sesión | `POST /auth/logout` | RNF-02 («sesiones activas») | Sí (cualquier rol) |

## POST /auth/token — iniciar sesión

Cuerpo `application/x-www-form-urlencoded`: `username`, `password` (campos del estándar OAuth2).

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 200 | Credenciales válidas (cualquier rol) | `{ "access_token": "<jwt>", "token_type": "bearer", "rol": "RECEPCIONISTA" }` |
| 401 | Usuario inexistente o contraseña incorrecta | `{ "codigo": "CREDENCIALES_INVALIDAS", "mensaje": "Usuario o contraseña incorrectos", "detalle": {} }` con `WWW-Authenticate: Bearer` (FR-002) |
| 422 | Falta `username` o `password` | Error de validación de FastAPI |

- Un usuario con rol `TECNICO` **sí** obtiene token (200): el rechazo se produce en las operaciones de recepción (FR-004).
- `rol` es informativo para la interfaz; la API no lo toma del token (research D2).
- El JWT se firma con HS256 y lleva `sub`, `jti`, `iat` y `exp`.

## POST /auth/logout — cerrar sesión

Cabecera `Authorization: Bearer <jwt>`. Sin cuerpo.

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 204 | Sesión activa cerrada; el `jti` queda revocado | — |
| 401 | Sin sesión activa (`NO_AUTENTICADO`) | Formato uniforme |

Tras el 204, cualquier solicitud con ese token recibe 401 `NO_AUTENTICADO` (FR-007).

## Cambios en las operaciones existentes de C1

Las cinco operaciones de recepción exigen `Authorization: Bearer <jwt>` de una sesión activa con rol `RECEPCIONISTA` (FR-003). Sus reglas y respuestas de éxito no cambian, salvo el dato de solo lectura de la última fila.

| Operación | Ruta | Cambio |
|-----------|------|--------|
| Buscar cliente (CU-05) | `GET /clientes/{dni}` | + 401 y 403 |
| Registrar nuevo cliente (CU-06) | `POST /clientes` | + 401 y 403 |
| Listar técnicos disponibles | `GET /tecnicos/disponibles` | + 401 y 403; cada elemento suma `cola` (entero, `Tecnico.cola`) |
| Consultar costo de revisión inicial | `GET /ordenes/costo-revision-inicial` | + 401 y 403 |
| Registrar orden de servicio (CU-01) | `POST /ordenes` | + 401 y 403 |

Respuestas de rechazo comunes a las cinco:

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 401 | Sin cabecera, token vencido, firma inválida, sesión cerrada o usuario inexistente | `{ "codigo": "NO_AUTENTICADO", "mensaje": "Debe iniciar sesión", "detalle": {} }` con `WWW-Authenticate: Bearer` |
| 403 | Sesión válida con rol `TECNICO` | `{ "codigo": "ROL_NO_PERMITIDO", "mensaje": "Su rol no tiene acceso a las operaciones de recepción", "detalle": {} }` |

Garantías:

- Un rechazo 401/403 no devuelve datos, no crea ni modifica registros y no registra el `id_op`.
- La comprobación de acceso ocurre antes de validar el cuerpo: sin sesión, un cuerpo inválido devuelve 401 y no 422.
- `GET /tecnicos/disponibles` con `cola`: `[ {id, nombres, apellidos, cola} ]`; el conjunto de técnicos devueltos no cambia (RN-03).
- `/docs` y `/openapi.json` no están protegidos (no son operaciones de recepción).
