# Quickstart: validación de la iteración C1

Guía para ejecutar y validar la recepción de equipos (CU-05, CU-06, CU-01). Contratos: [contracts/api-c1.md](contracts/api-c1.md). Modelo de datos: [data-model.md](data-model.md).

## Prerrequisitos

- `uv` instalado (gestiona Python 3.12 y dependencias).
- Ninguna credencial ni servicio externo; la base es un archivo SQLite local.

## Preparación

```bash
uv sync                                    # instala dependencias (Python 3.12)
export BYTETRACK_DB_PATH=./bytetrack.db    # opcional; ruta del archivo SQLite
uv run python -m app.seed                  # carga técnicos de demostración (idempotente)
```

## Ejecutar la aplicación

```bash
uv run uvicorn app.main:app --reload
```

Abrir `http://127.0.0.1:8000/docs` (Swagger UI): es la interfaz de la entrega. Cada operación aparece etiquetada con su caso de uso y pantalla (GUI-01/GUI-02).

## Escenarios de validación manual (en Swagger UI)

| Código | Escenario | Pasos | Resultado esperado |
|--------|-----------|-------|--------------------|
| CU-01-B | Orden para cliente existente | 1) `POST /clientes` con un DNI nuevo. 2) `GET /clientes/{dni}`. 3) `GET /tecnicos/disponibles` y `GET /ordenes/costo-revision-inicial`. 4) `POST /ordenes` con un equipo nuevo y un `id_op` nuevo | 201; orden `RECEPCIONADO` con código `OS-AAAA-NNNN`; la cola del técnico aumenta en 1 |
| CU-01-2a | DNI inexistente | `GET /clientes/{dni}` con un DNI no registrado; luego `POST /clientes` | 404 con `habilitar_registro`; 201 al registrar |
| CU-01-2b | DNI ya registrado en el modal | `POST /clientes` con un DNI existente | 200, `ya_registrado: true`, aviso "El DNI ya está registrado"; sin duplicados |
| CU-01-5a | Equipo con orden activa | `POST /ordenes` con la misma serie y un `id_op` nuevo | 409 `E01` con el número de la orden activa; cola sin cambios |
| CU-01-6a | Reintento | Repetir `POST /ordenes` con el mismo `id_op` y los mismos datos | 200, `reintento: true`, misma orden; una sola orden y cola +1 una vez |

## Validación automatizada

```bash
uv run pytest
```

Pruebas esperadas (cada una nombrada con el código que cubre):

| Archivo | Cubre |
|---------|-------|
| `tests/test_cu05_buscar_cliente.py` | CU-05 / pasos 1-2 de CU-01; RN-01 (formato y búsqueda de DNI) |
| `tests/test_cu06_registrar_cliente.py` | CU-01-2a, CU-01-2b; RN-01 (DNI único, sin duplicados) |
| `tests/test_cu01_registrar_orden.py` | CU-01-B; RN-01 (serie única, varios equipos), RN-03 (solo técnico disponible, cola +1), campos obligatorios, atomicidad |
| `tests/test_cu01_5a_orden_activa.py` | CU-01-5a; RN-02 (E01, nueva orden permitida tras ENTREGADO, concurrencia sobre la misma serie) |
| `tests/test_cu01_6a_idempotencia.py` | CU-01-6a; RN-10 (reintento, solicitudes simultáneas, ID OP con datos distintos, ID OP no registrado tras un fallo) |

Criterio de aceptación de C1: todas las pruebas pasan y cada RN en alcance (RN-01, RN-02, RN-03 en su parte de asignación, RN-10) y cada caso `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a` y `CU-01-6a` tiene al menos una prueba.

## Fuera de alcance (no validar en C1)

Autenticación OAuth2/JWT, CU-02, CU-03, CU-04, CU-07, CU-08 y las pruebas de RNF-01, RNF-02 y RNF-03 (pendientes).
