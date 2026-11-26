# Feature Specification: Fase de Transición, despliegue reproducible y validación de hitos IOC / PR (Iteración T1)

**Feature Branch**: `004-transicion-despliegue`

**Created**: 2026-11-26

**Status**: Implemented

**Input**: User description: "Desarrolla la especificación SDD de la fase de Transición (iteración T1) de ByteTrack sobre el sistema completo C1–C4: despliegue local reproducible con scripts de arranque y semilla idempotente, pruebas de humo end-to-end, prueba de concurrencia y rendimiento RNF-03 (5 sesiones concurrentes y 100 intentos con p95 <= 1 s), manual de usuario para Recepcionista y Técnico, y evaluación formal de los hitos IOC y PR en docs/transicion/."

**Fuente de verdad**: `docs/aup/caso.md` (Tabla 1, Tabla 3, riesgos `R4`, `R5` y `R7`, hito LCA §3.7.3 y plan §4.1), `docs/aup/requerimientos.md` (`RF-01` a `RF-06`, `RNF-01` a `RNF-04`) y `.specify/memory/constitution.md` v1.4.0.

## Contexto

Con las cuatro iteraciones de Construcción (`C1` a `C4`) completadas en `001`, `002` y `003`, ByteTrack cuenta con los ocho casos de uso (`CU-01` a `CU-08`) y las seis pantallas (`GUI-01` a `GUI-06`) operativas. En AUP, la fase de **Transición (`T1`)** tiene como objetivo validar la solución lista para operación en el taller **ByteFix Lab**, ejecutar pruebas de humo y rendimiento (`RNF-03`), entregar capacitación documental para mitigar el riesgo de adopción (`R4`) y evaluar los hitos **IOC (Capacidad Operativa Inicial)** y **PR (Liberación del Producto)**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Puesta en marcha local reproducible en un comando (Priority: P1)

El encargado de TI de ByteFix Lab clona el proyecto, configura `.env` a partir de `.env.example` y ejecuta el script de despliegue (`scripts/arrancar.ps1` en Windows o `scripts/arrancar.sh` en Linux/macOS). El script valida variables obligatorias, sincroniza el entorno Python 3.12 con `uv`, carga de manera idempotente usuarios, técnicos, catálogo de repuestos y datos iniciales (`app.seed`), ejecuta la verificación de humo e inicia el servidor.

**Independent Test**: Ejecutar `app.seed` dos veces seguidas sobre una base limpia y comprobar que no duplica registros ni expone contraseñas en claro.

---

### User Story 2 - Pruebas de humo y benchmark de rendimiento RNF-03 (Priority: P1)

Antes de habilitar la estación de recepción y laboratorio, el equipo ejecuta la suite de transición que valida: (a) disponibilidad de la interfaz web, Swagger, inicio de sesión por rol y datos semilla; y (b) el objetivo de rendimiento `RNF-03` con **5 sesiones concurrentes y 100 intentos sobre stock libre**, verificando percentil 95 de respuesta `<= 1.0 s` y cero violaciones de atomicidad (`RNF-01`).

**Independent Test**: Ejecutar `uv run pytest tests/test_transicion_humo_rnf03.py` y comprobar que `p95 <= 1.0 s` y `stock_reservado <= stock_disponible`.

---

### User Story 3 - Operación guiada por rol y evaluación de hitos IOC / PR (Priority: P2)

La Recepcionista y el Técnico de laboratorio consultan su manual operativo (`docs/transicion/manual-usuario-taller.md`) para ejecutar cada pantalla (`GUI-01` a `GUI-06`) e interpretar alertas (`E01`, `E02`), mientras el equipo registra en `docs/transicion/evaluacion-hitos-ioc-pr.md` el cumplimiento del hito **IOC** y el estado del hito **PR**.

## Requirements *(mandatory)*

- **FR-001**: El proyecto MUST proveer scripts reproducibles `scripts/arrancar.ps1` y `scripts/arrancar.sh` que verifiquen `.env`, ejecuten `python -m app.seed` y levanten `uvicorn` sin incluir credenciales fijas (Principio VI).
- **FR-002**: `app.seed` MUST cargar de forma idempotente los roles `RECEPCIONISTA` y `TECNICO` (con hash `scrypt` y vínculo `tecnico_id`), técnicos iniciales, repuestos de almacén y órdenes demostrativas para capacitación.
- **FR-003**: `tests/test_transicion_humo_rnf03.py` MUST automatizar una prueba de humo integral post-semilla y una prueba de carga concurrente de 5 sesiones y 100 intentos que verifique `p95 <= 1.0 s` (`RNF-03`) e integridad de stock (`RNF-01`).
- **FR-004**: `docs/transicion/` MUST contener el plan de despliegue y respaldo (`plan-despliegue.md`), el manual de usuario por rol (`manual-usuario-taller.md`) y el acta de verificación de hitos IOC/PR (`evaluacion-hitos-ioc-pr.md`), sin alterar `docs/aup/` (Principio I).

## Success Criteria *(mandatory)*

- **SC-001**: `app.seed` ejecutado repetidamente produce cero duplicados de usuarios, técnicos, repuestos u órdenes demo.
- **SC-002**: En la prueba automatizada `RNF-03` (5 sesiones concurrentes, 100 intentos de reserva), el percentil 95 de latencia es `<= 1.0 s` y el inventario conserva `stock_reservado <= stock_disponible` en el 100 % de las ejecuciones.
- **SC-003**: El 100 % de la suite global (`uv run pytest`) pasa en verde incluyendo Construcción (`C1–C4`) y Transición (`T1`).

## Fuera de Alcance

- Aprovisionamiento real de infraestructura AWS (`ECS Fargate`, `RDS Multi-AZ`, `CloudFront`, `SES`) y migración de datos históricos desde hojas Excel del taller.
