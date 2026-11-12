# Research (Fase 0): Iteración C1 — Recepción y orden de servicio

No quedaron `NEEDS CLARIFICATION` en el contexto técnico. Este documento registra las decisiones de diseño tomadas para C1, con su justificación y las alternativas descartadas.

## D1. Base de datos: SQLite local con SQLAlchemy (desviación de PostgreSQL/AWS)

- **Decision**: SQLite en archivo local, accedida con SQLAlchemy 2.x; ruta configurable por variable de entorno.
- **Rationale**: La entrega es local y sin nube; la constitución (principio V) fija SQLite local. SQLAlchemy conserva la portabilidad hacia PostgreSQL (la arquitectura candidata de AUP 2.6).
- **Alternatives considered**: PostgreSQL local con Docker (descartada: complejidad y dependencia extra no pedidas); SQL puro sin ORM (descartada: no es el stack acordado).
- **Consecuencia**: SQLite no ofrece bloqueos de fila como PostgreSQL; la concurrencia se resuelve con D3 y D4.

## D2. Interfaz: documentación Swagger de FastAPI

- **Decision**: No hay frontend propio. Swagger UI (`/docs`) es la interfaz de uso. Cada operación se etiqueta con su caso de uso y su pantalla (por ejemplo `CU-05 · GUI-01`), y su descripción cita las reglas `RN-xx` que valida.
- **Rationale**: Indicación del usuario; mantiene la trazabilidad con GUI-01/GUI-02 sin construir interfaz.
- **Alternatives considered**: Frontend estático mínimo (descartado: fuera de lo pedido).

## D3. Integridad en la base de datos (RN-01, RN-02)

- **Decision**: Las reglas se verifican en el servicio y además se respaldan con restricciones:
  - `cliente.dni` único con restricción de formato de 8 dígitos (RN-01).
  - `equipo.numero_serie` único (RN-01).
  - Índice único parcial sobre `orden_servicio(equipo_id)` donde `estado <> 'ENTREGADO'` (RN-02). SQLite admite índices parciales y SQLAlchemy los declara con `sqlite_where`.
  - `orden_servicio.id_op` único y `operacion_idempotente.id_op` como clave primaria (RN-10).
- **Rationale**: Garantiza "una sola orden activa por equipo" aunque dos solicitudes concurrentes pasen la validación del servicio; la segunda falla por restricción y se traduce a E01.
- **Alternatives considered**: Solo validar en el servicio (descartada: vulnerable a carreras); bloqueo a nivel de aplicación (descartada: no protege entre procesos).

## D4. Transacción de creación de orden con escritura serializada

- **Decision**: La operación de crear la orden se ejecuta en una sola transacción iniciada con `BEGIN IMMEDIATE` (toma el bloqueo de escritura desde el inicio). Se activan `PRAGMA foreign_keys=ON`, `journal_mode=WAL` y un `busy_timeout`. Para que SQLAlchemy con `pysqlite` respete el `BEGIN` explícito, se configura el control de transacciones del driver mediante los eventos `connect` y `begin` del motor (patrón documentado por SQLAlchemy).
- **Rationale**: Serializa los escritores: la verificación de ID OP, la validación de serie/orden activa, el alta de equipo/orden, el incremento de cola y el registro de la operación idempotente son atómicos y sin lecturas obsoletas.
- **Alternatives considered**: `BEGIN` diferido (descartada: dos transacciones pueden leer el mismo estado y fallar al escribir con `database is locked`); aislamiento serializable simulado (no existe como tal en SQLite).

## D5. Idempotencia (RN-10 / RNF-04): guardar el ID OP con su resultado

- **Decision** (indicación del usuario): tabla `operacion_idempotente` con `id_op` (clave primaria), `operacion` (`CU-01`), `huella` (hash SHA-256 de la solicitud normalizada), `orden_id` y `resultado` (respuesta serializada). Se inserta **solo cuando la operación se confirma**, dentro de la misma transacción que la orden y el incremento de cola.
- **Flujo**: (1) buscar `id_op`; (2) si existe y la huella coincide → devolver el resultado guardado (HTTP 200, sin escribir nada); (3) si existe y la huella difiere → rechazar (`ID_OP_CONFLICTO`, 409); (4) si no existe → ejecutar la operación y registrar el ID OP con su resultado.
- **Rationale**: Un reintento recupera exactamente la respuesta original sin recalcular, no duplica la orden ni vuelve a incrementar la cola; el rechazo con datos distintos sigue el diseño de AUP (los controles compartidos). Las solicitudes fallidas no registran ID OP, así que el usuario puede corregir y reintentar con el mismo ID.
- **Alternatives considered**: Solo la restricción única de `orden.id_op` (descartada: no devuelve la respuesta original ni detecta datos distintos); caché en memoria (descartada: no sobrevive reinicios ni procesos).
- **Formato del ID OP**: cadena generada por el cliente (Swagger lo muestra como campo del cuerpo `id_op`), obligatoria y no vacía; el AUP no fija longitud ni formato.

## D6. Tratamiento de errores y códigos

- **Decision**: Las reglas lanzan excepciones de dominio con un código estable (`E01`, `ID_OP_CONFLICTO`, `TECNICO_NO_DISPONIBLE`, `SIN_TECNICOS_DISPONIBLES`, `SERIE_EN_OTRO_CLIENTE`, `CLIENTE_NO_ENCONTRADO`) que `app/main.py` traduce a respuestas JSON uniformes (`codigo`, `mensaje`, datos adicionales como el número de la orden activa). E01 conserva el texto de la narrativa: "Este número de serie ya posee la Orden activa N.° [X] en laboratorio".
- **Rationale**: Mantiene los códigos AUP visibles en la API y verificables en pruebas.

## D7. Selección de equipo y datos de la solicitud

- **Decision**: La solicitud de crear orden identifica al cliente por DNI y el equipo por `equipo_id` (existente) **o** por los datos de un equipo nuevo (tipo, marca, modelo, serie); se exige exactamente uno. Si se envía una serie nueva ya registrada para otro cliente, se rechaza con `SERIE_EN_OTRO_CLIENTE` (RN-01).
- **Rationale**: Refleja el paso 3 de CU-01 y el supuesto de unicidad global del número de serie de la especificación.

## D8. Técnicos y disponibilidad (RN-03)

- **Decision**: `tecnico` tiene `disponible` (booleano) y `cola` (entero ≥ 0). La API ofrece `GET /tecnicos/disponibles`; al crear la orden se revalida la disponibilidad dentro de la transacción y la cola se incrementa con una actualización atómica (`cola = cola + 1`). Los técnicos se cargan con un script de datos de demostración (`app/seed.py`) y con datos de prueba en los tests; su mantenimiento queda fuera de C1.
- **Rationale**: Cumple la asignación solo a técnico disponible (RN-03, parte en alcance) sin gestionar la disponibilidad.

## D9. Costo de revisión inicial

- **Decision**: Importe configurable por variable de entorno; la API lo expone para su verificación (`GET /ordenes/costo-revision-inicial`) y se guarda en la orden al crearla (no lo envía el cliente). Valor por defecto de prototipo: 40.00, **pendiente de confirmar con el taller** (la documentación solo menciona S/ 40 como propuesta de RN-11, que está fuera de alcance).
- **Rationale**: Evita que el Recepcionista lo manipule y deja el valor ajustable sin tocar código.

## D10. Código de orden

- **Decision**: Código único con formato `OS-AAAA-NNNN` (año de la recepción y correlativo de 4 dígitos que se reinicia cada año; ejemplo `OS-2026-0146`), tomado del prototipo GUI-01 y calculado dentro de la misma transacción. La respuesta lo devuelve en un campo apto para impresión; la impresión no forma parte de C1.
- **Rationale**: Cumple "código de orden generado listo para imprimir" con un formato simple. El formato exacto no está definido en AUP; se registra como decisión de diseño.

## D11. Estrategia de pruebas

- **Decision**: pytest con base SQLite temporal por prueba (archivo, no memoria, para poder abrir conexiones independientes). Pruebas de API con `TestClient` (httpx). La prueba de concurrencia de CU-01-6a lanza solicitudes simultáneas con el mismo ID OP desde hilos con sesiones propias. Cada prueba lleva en su nombre el código que cubre.
- **Rationale**: Principio III de la constitución y evidencia verificable de RN-02 y RN-10 bajo concurrencia.
- **Alternatives considered**: Base en memoria compartida (descartada: dificulta la concurrencia real entre conexiones).

## Pendientes registrados (no se resuelven en C1)

- RNF-01 (reserva atómica), RNF-02 (OAuth2/JWT y reglas en la API), RNF-03 (rendimiento p95 ≤ 1 s con 5 sesiones) y la parte de acceso de RN-03 (el técnico solo ve sus órdenes), conforme a la especificación.
