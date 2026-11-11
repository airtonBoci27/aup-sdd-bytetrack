# Contrato de la API — Iteración C1

Contrato de las operaciones expuestas por la API REST (y documentadas en Swagger UI, `/docs`). La definición OpenAPI definitiva la genera FastAPI a partir de los esquemas; este documento fija el comportamiento esperado que las pruebas de contrato deben verificar. Formato JSON. Sin autenticación en C1 (RNF-02 pendiente).

Cada operación declara en Swagger su etiqueta `CU-xx · GUI-xx` y las reglas `RN-xx` que valida.

## Formato de error uniforme

```json
{ "codigo": "E01", "mensaje": "Este número de serie ya posee la Orden activa N.° OS-000012 en laboratorio", "detalle": { "orden_activa": "OS-000012" } }
```

Errores de formato del cuerpo o de los parámetros devuelven 422 con la estructura de validación de FastAPI.

## Resumen

| Operación | Método y ruta | CU | Pantalla | Reglas |
|-----------|---------------|----|----------|--------|
| Buscar cliente | `GET /clientes/{dni}` | CU-05 | GUI-01 | RN-01 |
| Registrar nuevo cliente | `POST /clientes` | CU-06 | GUI-02 | RN-01 |
| Listar técnicos disponibles | `GET /tecnicos/disponibles` | CU-01 (paso 4) | GUI-01 | RN-03 |
| Consultar costo de revisión inicial | `GET /ordenes/costo-revision-inicial` | CU-01 (paso 4) | GUI-01 | — |
| Registrar orden de servicio | `POST /ordenes` | CU-01 | GUI-01 | RN-01, RN-02, RN-03, RN-10 |

---

## GET /clientes/{dni} — CU-05 · GUI-01

Busca un cliente por DNI y devuelve sus equipos para llenar el selector (CU-01 pasos 1-2).

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 200 | Cliente encontrado | `{ "cliente": {dni, nombres, apellidos, telefono, correo}, "equipos": [{id, tipo, marca, modelo, numero_serie}] }` (lista vacía si no tiene equipos) |
| 404 | DNI inexistente (CU-01 curso 2a) | `{ "codigo": "CLIENTE_NO_ENCONTRADO", "mensaje": "...", "detalle": { "habilitar_registro": true } }` |
| 422 | `dni` no son 8 dígitos (RN-01) | Error de validación |

## POST /clientes — CU-06 · GUI-02

Cuerpo: `{ "dni": "12345678", "nombres": "...", "apellidos": "...", "telefono": "...", "correo": null }` (`correo` opcional).

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 201 | Cliente creado (curso 2a) | `{ "cliente": {...}, "equipos": [], "ya_registrado": false }` |
| 200 | DNI ya registrado (curso 2b; RN-01) | `{ "cliente": {...existente...}, "equipos": [...], "ya_registrado": true, "aviso": "El DNI ya está registrado" }` — no crea ni modifica nada |
| 422 | Falta un campo obligatorio o DNI inválido | Error de validación |

## GET /tecnicos/disponibles — CU-01 paso 4 · GUI-01

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 200 | Siempre | `[ {id, nombres, apellidos, cola} ]` solo con técnicos `disponible = true` (RN-03); lista vacía si no hay ninguno |

## GET /ordenes/costo-revision-inicial — CU-01 paso 4 · GUI-01

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 200 | Siempre | `{ "costo_revision": "40.00" }` (valor configurado; no lo envía el cliente al crear la orden) |

## POST /ordenes — CU-01 · GUI-01

Cuerpo:

```json
{
  "id_op": "3f2b9c1e-7a4d-4e0a-9d51-0c8f6b2a1e77",
  "dni": "12345678",
  "equipo_id": 7,
  "equipo": null,
  "accesorios": "Cargador",
  "estado_fisico": "Carcasa rayada",
  "falla_reportada": "No enciende",
  "tecnico_id": 2
}
```

- `id_op`: obligatorio (RN-10).
- Exactamente uno de `equipo_id` (equipo existente del cliente) o `equipo` (`{tipo, marca, modelo, numero_serie}`, equipo nuevo).
- `accesorios` opcional; `estado_fisico`, `falla_reportada` y `tecnico_id` obligatorios.

| Código | Cuándo | Cuerpo |
|--------|--------|--------|
| 201 | Orden creada (CU-01-B) | `{ "orden": {codigo, estado: "RECEPCIONADO", dni, equipo, tecnico, accesorios, estado_fisico, falla_reportada, costo_revision, creada_en}, "reintento": false }` y se incrementa en 1 la cola del técnico |
| 200 | Mismo `id_op` y mismos datos (CU-01-6a; RN-10) | Mismo cuerpo que la creación original con `"reintento": true`; no crea orden ni incrementa la cola |
| 404 | DNI inexistente | `CLIENTE_NO_ENCONTRADO` |
| 409 | La serie tiene una orden con estado distinto de ENTREGADO (CU-01-5a; RN-02) | `E01` con el número de la orden activa; no crea nada ni cambia la cola |
| 409 | `id_op` ya usado con datos distintos (RN-10) | `ID_OP_CONFLICTO` |
| 409 | Técnico no disponible o inexistente (RN-03) | `TECNICO_NO_DISPONIBLE` |
| 409 | No hay técnicos disponibles (precondición de CU-01; RN-03) | `SIN_TECNICOS_DISPONIBLES` |
| 409 | Serie nueva ya registrada para otro cliente (RN-01) | `SERIE_EN_OTRO_CLIENTE` |
| 422 | Faltan campos obligatorios, DNI inválido o no se envía exactamente uno de `equipo_id` / `equipo` | Error de validación |

### Garantías

- La operación es atómica: equipo nuevo, orden, incremento de cola y registro del ID OP se confirman juntos o no se confirma nada.
- Los fallos (409/422/404) no registran el ID OP: se puede corregir la solicitud y reintentar con el mismo `id_op`.
- Solicitudes simultáneas con el mismo `id_op` producen una sola orden; las demás reciben la respuesta original (200).
