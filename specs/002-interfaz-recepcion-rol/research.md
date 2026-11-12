# Research (Fase 0): Interfaz web de recepción con acceso por rol

Decisiones técnicas para [spec.md](spec.md). No quedan marcadores `NEEDS CLARIFICATION`. Las dependencias nuevas se justifican en D12.

## D1. Interfaz: archivos estáticos servidos por FastAPI, sin framework ni compilación

- **Decisión**: la interfaz vive en `app/web/` (HTML, CSS y JavaScript con módulos ES nativos) y la aplicación existente la sirve con `StaticFiles` montado en `/`, **después** de registrar los routers. Una sola página (`index.html`) con tres vistas que se alternan: inicio de sesión, rechazo por rol y recepción (GUI-01, con el modal GUI-02).
- **Justificación**: es lo que fija la constitución (Restricciones Técnicas) y la indicación del usuario. Una sola aplicación y un solo origen: no hace falta CORS. Los módulos ES nativos permiten separar el código sin empaquetador.
- **Alternativas**: páginas separadas (login y recepción), que duplican el encabezado y el manejo de sesión; un framework de frontend, que la constitución prohíbe.
- **Nota**: `/docs` y `/openapi.json` siguen públicos; no son operaciones de recepción (FR-003).

## D2. Autenticación: flujo OAuth2 de contraseña con JWT firmado (HS256)

- **Decisión**: `POST /auth/token` recibe `username` y `password` como formulario (`OAuth2PasswordRequestForm`) y devuelve `{access_token, token_type: "bearer", rol}`. El token es un JWT HS256 con `sub` (nombre de usuario), `jti` (identificador único), `iat` y `exp`. Las operaciones protegidas leen `Authorization: Bearer …`. La clave de firma sale de `BYTETRACK_JWT_SECRET`.
- **Justificación**: la arquitectura candidata (`caso.md` §2.6) y el riesgo R3 piden OAuth2 con JWT; RNF-02 exige roles y sesiones activas. El esquema `OAuth2PasswordBearer` hace que Swagger UI muestre el botón «Authorize» y permita probar el rechazo del Técnico sin la interfaz.
- **Rol**: no va en el token. En cada solicitud se carga el usuario por `sub` y se lee su rol de la base; así un usuario eliminado o con rol cambiado pierde acceso de inmediato. El campo `rol` de la respuesta de login es solo informativo para la interfaz.
- **Alternativas**: HS256 frente a RS256 (par de claves): en una aplicación de un solo servicio no hay verificadores externos, y una clave compartida es más simple. Un endpoint de login con JSON: más simple, pero no es el flujo OAuth2 ni funciona con «Authorize».

## D3. Cierre de sesión: lista de tokens revocados

- **Decisión**: `POST /auth/logout` guarda el `jti` del token con su fecha de expiración en la tabla `token_revocado`. Cada solicitud protegida rechaza un token cuyo `jti` esté en esa tabla. Al cerrar sesión se purgan de paso las filas ya vencidas.
- **Justificación**: un JWT por sí solo no se puede anular; FR-007 exige que la sesión deje de ser válida al cerrarla. La lista es la forma más simple de cumplirlo y no crece sin límite porque solo guarda tokens aún vigentes.
- **Alternativas**: tabla de sesiones con una fila por inicio de sesión (más escrituras, sin beneficio aquí); tokens de vida muy corta (no cumple FR-007).

## D4. Contraseñas: `scrypt` de la biblioteca estándar

- **Decisión**: `hashlib.scrypt` (n=2^14, r=8, p=1, sal aleatoria de 16 bytes) y comparación con `hmac.compare_digest`. Formato guardado: `scrypt$n$r$p$sal$hash` en base64.
- **Justificación**: scrypt es una función de derivación aprobada para contraseñas y ya está en Python 3.12, así que **no suma dependencia** (principio V).
- **Alternativas**: `pwdlib`/`argon2-cffi`/`bcrypt` (dependencia extra sin necesidad con ≤ 2 usuarios); SHA-256 simple (inadecuado para contraseñas).

## D5. Usuarios iniciales: tabla `usuario` cargada desde variables de entorno

- **Decisión**: la tabla `usuario` (nombre de usuario, hash, rol) se llena con `uv run python -m app.seed`, que lee `BYTETRACK_RECEPCIONISTA_USUARIO` / `BYTETRACK_RECEPCIONISTA_CLAVE` y `BYTETRACK_TECNICO_USUARIO` / `BYTETRACK_TECNICO_CLAVE`. Los nombres de usuario tienen valor por defecto (`recepcion` y `tecnico`); las contraseñas **no** tienen valor por defecto y la carga falla si faltan. La carga crea el usuario o actualiza su hash si ya existe (un cambio de contraseña en `.env` se aplica al volver a ejecutarla).
- **Justificación**: la especificación pide usuarios preexistentes sin pantallas ni operaciones de gestión, y la constitución (VI) impide guardar contraseñas en el repositorio. Guardar solo el hash en la base evita mantener contraseñas en claro en memoria.
- **Alternativas**: comparar directamente contra las variables de entorno en cada inicio de sesión (contraseñas en claro en el proceso; sin hash); un archivo de usuarios en el repositorio (viola VI).

## D6. Configuración y archivo `.env`

- **Decisión**: se carga con `python-dotenv` mediante una función explícita `cargar_entorno()` que se invoca al arrancar la aplicación (inicio del ciclo de vida) y en `app.seed`; nunca al importar módulos. `override=False`: una variable ya definida en el entorno prevalece sobre el archivo. La ruta es `./.env` y se puede cambiar con `BYTETRACK_ENV_FILE` (por ejemplo, un archivo fuera del directorio del proyecto). `.env` ya está en `.gitignore`.
- **«Fuera del repositorio»**: se cumple en los dos sentidos: el archivo no se versiona (ignorado por git) y puede vivir en cualquier ruta externa.
- **Validación al arrancar**: `BYTETRACK_JWT_SECRET` es obligatoria y debe tener al menos 32 caracteres; si falta o es corta, la aplicación no arranca con un mensaje claro. `BYTETRACK_SESION_MINUTOS` (duración de la sesión) tiene valor por defecto 60 y es configurable; el valor por defecto no proviene de AUP (ver Assumptions de la spec).
- **Plantilla `.env.example`**: se versiona con los nombres de las variables y **sin valores secretos** (vacíos o con una descripción), para que se sepa qué configurar. La constitución 1.3.0 lo permite expresamente en el principio VI. Una prueba estática comprueba que no contiene valores en las variables secretas.
- **Pruebas aisladas**: como no se carga al importar, un `.env` local no afecta a las pruebas; estas fijan sus variables con valores generados en tiempo de ejecución (sin secretos en el repositorio).
- **Alternativas**: un analizador propio de `.env` (código extra que mantener y probar); `uvicorn --env-file` (también requiere python-dotenv y no cubre el seed ni las pruebas).

## D7. La verificación de sesión usa una sesión de base de datos propia (hallazgo)

- **Problema**: en C1, las escrituras abren la transacción con `BEGIN IMMEDIATE` antes de cualquier consulta (`iniciar_escritura`, research D4 de 001), y de ello dependen RN-02 y RN-10 bajo concurrencia. Si la dependencia de seguridad consultara el usuario con la **misma** sesión de la solicitud, la transacción ya estaría abierta con `BEGIN` diferido y `iniciar_escritura` no tendría efecto.
- **Decisión**: la verificación de sesión (usuario y revocación) usa una dependencia propia, `get_session_seguridad`, que abre y cierra una sesión independiente y breve antes de que la operación abra la suya. En las pruebas se sobrescriben ambas dependencias con la misma fábrica de sesiones.
- **Verificación**: una prueba (RN-02/RN-10 con la ruta autenticada) confirma que la concurrencia de 001 sigue cumpliéndose con el control de acceso activo.

## D8. Respuestas de rechazo

- **Decisión**: se mantiene el formato uniforme `{codigo, mensaje, detalle}`:

| Situación | HTTP | Código | Mensaje (resumen) |
|-----------|------|--------|-------------------|
| Credenciales inválidas | 401 | `CREDENCIALES_INVALIDAS` | «Usuario o contraseña incorrectos» |
| Sin token, vencido, firma inválida o cerrado | 401 | `NO_AUTENTICADO` | «Debe iniciar sesión» |
| Rol distinto de Recepcionista | 403 | `ROL_NO_PERMITIDO` | «Su rol no tiene acceso a las operaciones de recepción» |

  Las respuestas 401 incluyen `WWW-Authenticate: Bearer`. `OAuth2PasswordBearer(auto_error=False)` evita el error por defecto de FastAPI para poder devolver el formato uniforme.
- **Orden de evaluación**: la comprobación de acceso se declara como dependencia del router, de modo que un cuerpo inválido sin sesión devuelve 401 y no 422 (no se revela información a quien no tiene acceso). Una prueba lo verifica.

## D9. Dónde guarda el navegador el token

- **Decisión**: `sessionStorage` (token y rol), que se borra al cerrar la pestaña, y envío por cabecera `Authorization`. Todo texto que viene del servidor se inserta con `textContent`, nunca como HTML.
- **Justificación**: sin cookies no hay riesgo de CSRF; el riesgo restante es XSS, que se reduce al no usar `innerHTML` y no cargar scripts externos. Es coherente con el esquema Bearer de OAuth2.
- **Alternativas**: cookie `HttpOnly` (requiere manejo de CSRF y cambia el esquema Bearer de D2); `localStorage` (persiste tras cerrar el navegador, innecesario).

## D10. Cola del técnico en «Listar técnicos disponibles» (D2 de la spec)

- **Decisión**: `TecnicoOut` suma `cola: int` (ya existe en el modelo `Tecnico`). No cambia qué técnicos se devuelven ni ninguna regla (RN-03). Formato en la interfaz: «[nombres] [apellidos] ([N] en cola)».
- **Alternativas**: un endpoint nuevo para las colas (más superficie, sin ventaja).

## D11. ID de operación generado en el cliente

- **Decisión**: la interfaz genera `OP-` + 12 caracteres hexadecimales aleatorios (`crypto.getRandomValues`) al abrir una recepción nueva (carga inicial, tras confirmar y tras «Cancelar») y lo conserva en todos los reenvíos de esa recepción (FR-026, FR-027). El botón «Generar orden de servicio» se deshabilita mientras hay un envío en curso (FR-021).
- **Justificación**: el formato imita el del prototipo («OP-7F3A91») con más entropía; la idempotencia real la garantiza el servidor (RN-10), la interfaz solo evita el doble clic y conserva el identificador.

## D12. Dependencias nuevas

La constitución (Restricciones Técnicas) exige justificarlas aquí y enmendarla si son permanentes. El usuario aprobó la enmienda 1.3.0, que incorpora las tres dependencias de ejecución. Playwright se evaluó y se **descartó** por decisión del usuario (las pantallas se verifican con una lista manual, D13).

| Dependencia | Versión resuelta (mínima pedida) | Tipo | Para qué | Por qué no otra cosa |
|-------------|----------------------------------|------|----------|----------------------|
| `pyjwt` | 2.15.1 (`>=2.8`) | Ejecución | Firmar y verificar el JWT HS256, incluida la validación de `exp` | Escribir HMAC/base64url/validación de reclamos a mano es criptografía propia y propensa a errores. `python-jose` tiene menos mantenimiento y `authlib` es un framework OAuth2 completo, desproporcionado. Sin dependencias transitivas para HS256. |
| `python-multipart` | 0.0.33 (`>=0.0.9`) | Ejecución | Lo exige FastAPI para leer el formulario de `OAuth2PasswordRequestForm` (RFC 6749, flujo de contraseña) | Sin ella, FastAPI falla al declarar la ruta. Alternativa (login JSON) descartada en D2. |
| `python-dotenv` | 1.2.4 (`>=1.0`) | Ejecución | Leer `.env` (D6) | Un analizador propio duplica una función estándar y exigiría pruebas propias. |

No se agrega ninguna dependencia para el hash de contraseñas (D4), el servidor de archivos estáticos (FastAPI/Starlette lo incluyen), la generación del ID OP (API del navegador) ni las pruebas (sin herramientas de navegador).

## D13. Estrategia de pruebas

- **API (pytest + `TestClient`)**: acceso por rol en las cinco operaciones (sin sesión, token vencido o manipulado, sesión cerrada, Técnico, Recepcionista), login (válido, inválido, usuario inexistente), cierre de sesión, hash de contraseñas, configuración obligatoria, cola en técnicos. Código de prueba: `RNF-02`.
- **Estáticas**: el servidor sirve la interfaz; cada elemento del HTML declara su código de trazabilidad (`data-trace`) y el conjunto de identificadores coincide con el contrato de interfaz, de modo que no puede existir un elemento sin código AUP (principio VIII, SC-006). Es la única comprobación automatizada de la interfaz.
- **Pantalla (manual)**: sin pruebas en navegador, por decisión del usuario. Se verifica con la lista [checklists/verificacion-manual.md](checklists/verificacion-manual.md), que cubre el efecto en pantalla de `RNF-02`, `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a` y `CU-01-6a` (campos, alerta E01, modal, doble clic, ID OP, sesión vencida). Los cursos de CU-01 siguen cubiertos de forma automatizada por las pruebas de API de 001.
- **Regresión de 001**: el fixture `client` de `tests/conftest.py` inicia sesión como Recepcionista para que las pruebas de 001 sigan sin cambios. `tests/test_trazabilidad_swagger.py` se actualiza (7 operaciones; las de acceso se etiquetan `CU-01 · Acceso (RNF-02)`).

## Pendientes registrados (no se resuelven aquí)

- Restricciones de RNF-02 para decisión, cobro, diagnóstico y finalización, y RN-03 de acceso (el técnico solo ve sus órdenes): llegan con CU-02, CU-03, CU-04 y CU-08.
- Bloqueo por intentos fallidos, recuperación de contraseña y refresco de token: no figuran en RNF-02 ni en los prototipos (principio VIII).
- RNF-01 y RNF-03: sin cambios respecto de 001.
