# Implementation Plan: Recepción de equipos y registro de orden de servicio (Iteración C1)

**Branch**: `001-recepcion-orden-servicio` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-recepcion-orden-servicio/spec.md`

## Summary

La iteración C1 entrega la recepción funcional de ByteTrack: buscar cliente por DNI (CU-05), registrar cliente nuevo (CU-06) y registrar la orden de servicio (CU-01, curso básico y cursos 2a, 2b, 5a y 6a), con las reglas RN-01, RN-02, RN-03 (solo asignación a técnico disponible) y RN-10.

Enfoque técnico: API REST con FastAPI organizada en capas API → servicio → repositorio (SQLAlchemy sobre SQLite local). La interfaz de uso es la documentación Swagger que FastAPI genera (`/docs`); cada operación se etiqueta con su CU y su pantalla (GUI-01/GUI-02). La integridad se garantiza dos veces: en el servicio (reglas con sus códigos RN) y en la base de datos (restricciones únicas, incluido un índice único parcial que permite una sola orden activa por equipo). La creación de la orden es una sola transacción con escritura serializada y la idempotencia (RN-10) se implementa guardando el ID OP de cada operación confirmada junto con su resultado.

## Technical Context

**Language/Version**: Python 3.12 (fijado con `uv`; `requires-python = ">=3.12,<3.13"`)

**Primary Dependencies**: FastAPI (con Pydantic v2 y Swagger UI incluido), Uvicorn, SQLAlchemy 2.x. De desarrollo: pytest y httpx (cliente de pruebas de FastAPI). Versiones exactas fijadas por `uv.lock`.

**Storage**: SQLite local en un archivo (ruta por variable de entorno; archivo excluido de git). Sin PostgreSQL ni servicios de nube.

**Testing**: pytest (`uv run pytest`): pruebas de contrato/integración sobre la API con base SQLite temporal, pruebas unitarias de servicios y una prueba de concurrencia con conexiones independientes.

**Target Platform**: Equipo local de desarrollo (macOS/Linux) ejecutando `uv run uvicorn app.main:app --reload`. Sin despliegue en nube en esta entrega.

**Project Type**: web-service (API REST con documentación Swagger como interfaz; sin frontend propio).

**Performance Goals**: Sin objetivo formal en C1 (RNF-03, p95 ≤ 1 s con 5 sesiones, queda pendiente). Meta práctica de SC-001: recepción completa en menos de 3 minutos de trabajo humano; la API responde de forma interactiva en uso local.

**Constraints**: Una escritura a la vez (SQLite); operaciones de escritura de CU-01 y CU-06 atómicas (todo o nada); sin credenciales en el repositorio; sin autenticación dentro de C1 (incorporada después por la funcionalidad 002); sin llamadas a servicios externos.

**Scale/Scope**: Taller de ~30 equipos diarios; 3 casos de uso, 2 pantallas (GUI-01 y GUI-02 expresadas como operaciones Swagger), 5 entidades de datos, ~5 endpoints.

## Desviaciones respecto de la arquitectura candidata (AUP 2.6)

| Elemento AUP 2.6 | Adaptación en esta entrega | Justificación |
|------------------|----------------------------|---------------|
| PostgreSQL en RDS Multi-AZ | SQLite local con SQLAlchemy | La entrega es un prototipo local sin nube (indicación del usuario) y la constitución (principio V) fija SQLite local. SQLAlchemy mantiene el modelo portable a PostgreSQL. Las garantías que PostgreSQL daría (concurrencia, restricciones) se cubren con restricciones únicas, un índice único parcial y escritura serializada (ver [research.md](research.md)). |
| Frontend estático (S3 + CloudFront + WAF) | Sin frontend propio; la interfaz es Swagger UI de FastAPI | Indicación del usuario; reduce alcance sin perder la trazabilidad GUI-01/GUI-02 (cada operación Swagger declara su pantalla). |
| FastAPI en ECS Fargate tras balanceador | FastAPI ejecutado localmente con Uvicorn | Sin nube en esta entrega. |
| SES para avisos por correo | Fuera de alcance | C1 no envía correos. |
| OAuth2 con JWT | Fuera de alcance en C1; implementado después por la funcionalidad [002](../002-interfaz-recepcion-rol/plan.md) | Definido en el alcance de la iteración; RNF-02 se atiende con 002. |

Estas desviaciones están justificadas y registradas aquí; la arquitectura de tres capas de la API (interfaz, servicios, repositorios) y la unidad de trabajo transaccional del diseño AUP (sección 3.5) se conservan.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Verificación en este plan | Estado |
|-----------|---------------------------|--------|
| I. Documentación AUP como fuente de verdad | Se conservan CU-01/05/06, RN-01/02/03/10, E01, GUI-01/02; `docs/aup/` no se modifica; cada endpoint declara su `CU-xx` y cada validación su `RN-xx` (ver contratos). | PASA |
| II. Especificación antes que código | Existe `spec.md` validado; este plan precede a `tasks.md` y a cualquier código. | PASA |
| III. Pruebas automatizadas obligatorias | Cada RN en alcance y cada caso `CU-01-B`, `CU-01-2a`, `CU-01-2b`, `CU-01-5a`, `CU-01-6a` tiene prueba pytest nombrada con su código (ver [quickstart.md](quickstart.md)). | PASA |
| IV. Arquitectura en capas | `app/api` → `app/services` → `app/repositories` → `app/models`; las reglas viven en servicios; los endpoints no tocan la base directamente. | PASA |
| V. Simplicidad e integraciones con dobles de prueba | SQLite local; sin integraciones externas en C1 (no hay pagos, facturación ni correo), por lo que no se requieren dobles. | PASA |
| VI. Sin credenciales en el repositorio | Configuración por variables de entorno; sin secretos en C1 (002 agrega la clave de firma y las contraseñas, solo por entorno); `*.db` y `.env` en `.gitignore`. | PASA |
| VII. Alcance acotado por iteración | Fuera de alcance de C1: OAuth2/JWT (luego 002), CU-02/03/04/07/08; pendientes RNF-01/02/03 y RN-03 (acceso) registrados en la especificación. | PASA |

**Re-evaluación posterior al diseño (Fase 1)**: se mantiene PASA. El diseño no introduce capas, servicios ni tecnologías adicionales a las del stack. La tabla de operaciones idempotentes es el mecanismo pedido para RN-10 y no se considera complejidad extra.

## Project Structure

### Documentation (this feature)

```text
specs/001-recepcion-orden-servicio/
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0: decisiones técnicas
├── data-model.md        # Fase 1: entidades, restricciones y transiciones
├── quickstart.md        # Fase 1: guía de ejecución y validación
├── contracts/
│   └── api-c1.md        # Fase 1: contrato de la API de C1
├── checklists/
│   └── requirements.md  # Calidad de la especificación
└── tasks.md             # Fase 2 (/speckit-tasks; NO lo crea /speckit-plan)
```

### Source Code (repository root)

```text
app/
├── main.py                       # Aplicación FastAPI, routers, manejo de errores de dominio
├── config.py                     # Configuración desde variables de entorno (ruta de BD, costo de revisión)
├── database.py                   # Motor SQLAlchemy/SQLite, sesión y unidad de trabajo
├── errors.py                     # Excepciones de dominio con código (E01, ID_OP_CONFLICTO, ...)
├── seed.py                       # Datos de demostración (técnicos) para uso local
├── api/                          # Capa API: routers y dependencias (documentan CU/GUI en Swagger)
│   ├── clientes.py               # CU-05, CU-06 (GUI-01, GUI-02)
│   ├── tecnicos.py               # Lista de técnicos disponibles (CU-01 paso 4, RN-03)
│   └── ordenes.py                # CU-01 (GUI-01)
├── services/                     # Capa de servicio: reglas de negocio
│   ├── cliente_service.py        # RN-01
│   └── orden_service.py          # RN-01, RN-02, RN-03, RN-10
├── repositories/                 # Capa de repositorio: acceso a datos
│   ├── cliente_repository.py
│   ├── equipo_repository.py
│   ├── tecnico_repository.py
│   ├── orden_repository.py
│   └── operacion_repository.py   # Operaciones idempotentes (ID OP + resultado)
└── models/
    ├── entities.py               # Modelos SQLAlchemy
    └── schemas.py                # Esquemas Pydantic de entrada/salida

tests/
├── conftest.py                   # BD SQLite temporal, cliente de pruebas, datos base
├── test_cu05_buscar_cliente.py   # CU-05 (pasos 1-2 de CU-01), RN-01
├── test_cu06_registrar_cliente.py# CU-06: CU-01-2a, CU-01-2b, RN-01
├── test_cu01_registrar_orden.py  # CU-01-B, RN-01, RN-02, RN-03
├── test_cu01_5a_orden_activa.py  # CU-01-5a, RN-02, E01
└── test_cu01_6a_idempotencia.py  # CU-01-6a, RN-10 (incluye concurrencia)

pyproject.toml, uv.lock, .python-version, .gitignore
```

**Structure Decision**: proyecto único (web-service) con la estructura de `AGENTS.md`. Se escogió porque coincide con las capas de la constitución (principio IV) y no requiere frontend: Swagger UI cumple el rol de interfaz. Los archivos de pruebas se nombran por caso de uso y cada prueba lleva en su nombre el código que cubre (`CU-xx-<curso>` o `RN-xx`).

## Complexity Tracking

> No hay violaciones de la constitución. Se registran únicamente las desviaciones justificadas respecto de la arquitectura candidata AUP (tabla "Desviaciones respecto de la arquitectura candidata").

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Ninguna | — | — |
