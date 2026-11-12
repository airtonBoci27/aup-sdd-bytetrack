# Data Model: Interfaz de recepción con acceso por rol

Las entidades de C1 (`Cliente`, `Equipo`, `Tecnico`, `OrdenServicio`, `OperacionIdempotente`) **no cambian** (ver [../001-recepcion-orden-servicio/data-model.md](../001-recepcion-orden-servicio/data-model.md)). Se agregan dos tablas para RNF-02; `Base.metadata.create_all` las crea al arrancar, sin migraciones.

## Entidades nuevas

### Usuario (`usuario`) — RNF-02

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `id` | entero | PK |
| `nombre_usuario` | texto | obligatorio, único |
| `clave_hash` | texto | obligatorio; formato `scrypt$n$r$p$sal$hash` (D4); nunca la contraseña |
| `rol` | texto | obligatorio; `CHECK rol IN ('RECEPCIONISTA','TECNICO')` |

- Se llena solo con `app.seed` a partir de variables de entorno (D5). No hay operación para crear, editar ni listar usuarios (fuera de alcance).
- Los roles son los dos actores de `caso.md` (Recepcionista y Técnico de laboratorio). No hay relación con la tabla `tecnico`: el usuario Técnico de esta funcionalidad solo prueba el rechazo; vincularlo a un `Tecnico` pertenece al pendiente RN-03 (acceso).

### Token revocado (`token_revocado`) — RNF-02, cierre de sesión

| Campo | Tipo | Restricciones |
|-------|------|---------------|
| `jti` | texto | PK; identificador único del token |
| `expira_en` | entero | obligatorio; instante de expiración (segundos desde la época, UTC) |

- Una fila por cada sesión cerrada. Se purgan las filas con `expira_en` vencido en cada cierre de sesión.

## Sesión (no se guarda)

Una sesión activa es un JWT vigente (`exp` no vencido, firma válida) cuyo `jti` no está en `token_revocado` y cuyo `sub` corresponde a un usuario existente.

| Reclamo | Contenido |
|---------|-----------|
| `sub` | `nombre_usuario` |
| `jti` | UUID aleatorio |
| `iat`, `exp` | emisión y vencimiento (`BYTETRACK_SESION_MINUTOS`) |

## Cambio en un esquema de salida (sin cambio de datos)

`TecnicoOut` (respuesta de `GET /tecnicos/disponibles`) suma `cola: int`, que ya existe en `Tecnico` (RN-03; CU-01 paso 6).

## Reglas de validación (trazabilidad)

| Regla | Dónde se aplica | Código |
|-------|-----------------|--------|
| Sin token, vencido, firma inválida, revocado o usuario inexistente → 401 `NO_AUTENTICADO` | Dependencia de acceso | RNF-02 |
| Rol ≠ RECEPCIONISTA → 403 `ROL_NO_PERMITIDO` | Dependencia de acceso | RNF-02 |
| Credenciales incorrectas → 401 `CREDENCIALES_INVALIDAS` (sin distinguir usuario o contraseña) | `auth_service` | RNF-02 |
| Clave de firma obligatoria y de ≥ 32 caracteres | `config` | RNF-02, principio VI |

## Transiciones

La sesión pasa de *inexistente* → *activa* (login válido) → *cerrada* (logout) o *vencida* (`exp`). No hay otras.
