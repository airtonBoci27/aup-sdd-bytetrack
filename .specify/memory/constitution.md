<!--
Sync Impact Report
- Version change: 1.3.0 → 1.4.0
- Aprobación: el usuario (Airton) aprobó explícitamente la enmienda (2026-11-26) para alinear la
  constitución con la culminación de las iteraciones C2, C3 y C4 (specs/003-flujo-integral-taller)
  y la fase de Transición (specs/004-transicion-despliegue).
- Principios modificados:
  - VIII. Alcance cerrado: se formaliza la resolución de las dos decisiones de construcción de
    `docs/aup/caso.md` §4.1 (precondición `APROBADO` en CU-08 y liquidación por devolución en estado
    `RECHAZADO` cobrando `costo_revision` según RN-11) y la trazabilidad de vistas operativas de
    seguimiento paginado (`RF-01`, `RF-02`, `RF-03`, `RN-03`, `RNF-02`).
- Secciones modificadas:
  - Restricciones Técnicas: soporte multiplataforma (Windows PowerShell `scripts/arrancar.ps1` y
    POSIX `scripts/arrancar.sh`) para los scripts reproducibles de la fase de Transición.
- Justificación MINOR: amplía la guía arquitectónica y formaliza decisiones de dominio de C2–C4 y
  Transición sin eliminar ni contradecir principios previos (1.0.0 a 1.3.0).
- Artefactos afectados: AGENTS.md, specs/003-flujo-integral-taller/* y specs/004-transicion-despliegue/*.
- Pendientes: despliegue productivo en infraestructura AWS (RDS PostgreSQL Multi-AZ + ECS Fargate)
  previsto como evolución posterior al cierre local.
-->
# aup-sdd-caso Constitution

## Core Principles

### I. Documentación AUP como fuente de verdad
Los documentos AUP en `docs/aup/` (`caso.md` y `requerimientos.md`) son la fuente de verdad de los
requisitos. Sus códigos de trazabilidad (casos de uso `CU-xx`, reglas de negocio `RN-xx`,
requerimientos `RF-xx` / `RNF-xx`, alertas `E01`/`E02` y prototipos `GUI-01` a `GUI-06`) MUST
conservarse tal cual en especificaciones, planes, tareas, código y pruebas; no se renombran,
renumeran ni reutilizan. Todo endpoint MUST trazarse a un `CU-xx` y toda validación a una `RN-xx`
o `RNF-xx`. El código `CP-AAAA-NNNN` es el número del comprobante de pago interno emitido en `CU-04`
(dato del dominio) y NO es un caso de prueba; los casos de prueba se derivan del curso básico y de
los cursos alternos de las narrativas con la convención `CU-xx-<curso>` (`CU-01-B`, `CU-01-5a`,
`CU-02-9a`, etc.). `docs/aup/` MUST NOT modificarse salvo petición explícita del usuario.

### II. Especificación antes que código
Toda iteración o fase se documenta mediante su especificación (`specs/*/spec.md`), plan técnico
(`plan.md`) y lista de tareas (`tasks.md`). El trabajo de implementación y verificación MUST estar
respaldado por tareas trazables en `tasks.md`. Si el código y la especificación divergen, se alinea
primero la especificación y luego el código.

### III. Pruebas automatizadas obligatorias (NON-NEGOTIABLE)
Cada regla de negocio `RN-xx` y requerimiento no funcional `RNF-xx` dentro del alcance de la
iteración MUST contar con al menos una prueba automatizada con `pytest` que identifique el código
que cubre. Los casos de prueba (`CU-xx-B` y `CU-xx-<curso alterno>`) también MUST automatizarse
cuando su `CU-xx` esté en el alcance. Ninguna tarea se considera terminada mientras `uv run pytest`
no pase al 100 % sin omisiones ni pruebas desactivadas.

### IV. Arquitectura en capas
El flujo de dependencias es `API` → `servicio` → `repositorio` → `modelos`. Los endpoints
(`app/api`) validan entrada, exigen permisos por rol (`RNF-02`), delegan y serializan; la lógica de
negocio, el control transaccional (`BEGIN IMMEDIATE`, `RNF-01`) y las reglas `RN-xx` viven en
`app/services`; el acceso a datos vive en `app/repositories` sobre `app/models`. Una capa MUST NOT
saltarse a la siguiente.

### V. Simplicidad e integraciones con dobles de prueba
Se usa SQLite local como única base de datos del entorno local reproducible, garantizando portabilidad
hacia PostgreSQL mediante SQLAlchemy 2.x y transacciones serializadas (`BEGIN IMMEDIATE`). Las
integraciones externas (pasarelas, facturación tributaria, correo SES) quedan fuera del alcance o
aisladas tras dobles de prueba; ninguna prueba realiza llamadas de red externas.

### VI. Sin credenciales en el repositorio
Contraseñas, tokens, claves de firma JWT y cualquier otro secreto MUST NOT aparecer en el código,
las pruebas, los datos de ejemplo (`app/seed.py`) ni el historial de git. Los secretos se inyectan
por variables de entorno (`.env` excluido en `.gitignore`). Se versiona únicamente `.env.example` con
nombres de variables y valores vacíos; las pruebas generan claves aleatorias en tiempo de ejecución.

### VII. Alcance acotado por iteración
Cada especificación cubre un conjunto explícito de iteraciones AUP (`001` y `002` para C1; `003`
para C2–C4; `004` para Transición T1). Todo elemento pendiente respecto de la arquitectura objetivo
en nube se registra explícitamente con su código para trazabilidad futura.

### VIII. Alcance cerrado y decisiones registradas
Solo se especifica e implementa lo que se traza a un `RF-xx`, `RNF-xx`, `CU-xx`, `RN-xx` o `GUI-xx`
de `docs/aup/`. Toda especificación (`spec.md`) MUST incluir matriz de trazabilidad y sección "Fuera
de alcance". En la interfaz web (`app/web/index.html`), todo elemento con `id` MUST declarar su
atributo `data-trace` validado por prueba estática. Las decisiones pendientes identificadas en
`docs/aup/caso.md` §4.1 quedan resueltas así: (a) `CU-08` exige precondición `APROBADO`; (b) las
órdenes en `RECHAZADO` permiten devolución y cierre en `CU-04` cobrando el costo de revisión inicial
(`RN-11`), liberando el número de serie para futuros ingresos (`RN-02`); y (c) los paneles paginados
de seguimiento de órdenes, clientes y almacén materializan el objetivo AUP de «trazabilidad de cada
equipo por estado» (`RF-01`, `RF-02`, `RF-03`, `RN-03`, `RNF-02`).

## Restricciones Técnicas

- **Stack**: Python 3.12, FastAPI, SQLAlchemy 2.x, SQLite y pytest, gestionado con `uv`.
- **Estructura**: `app/` (`api`, `services`, `models`, `repositories`, `web`), `tests/`, `docs/` y `scripts/`.
- **Interfaz web**: HTML, CSS y JavaScript modular nativo sin framework ni compilación (`app/web/`), servida por FastAPI con cabeceras de seguridad (`CSP`, `X-Frame-Options`, `X-Content-Type-Options`) e inserción segura mediante `textContent` (prohibido `innerHTML`).
- **Artefactos de la fase de Transición**: se almacenan en `docs/transicion/` y los scripts de arranque local en `scripts/` (`arrancar.ps1` para Windows y `arrancar.sh` para Linux/macOS), sin modificar `docs/aup/`.
- **Dependencias de ejecución aprobadas** (enmienda 1.3.0): `pyjwt`, `python-multipart` y `python-dotenv`; hash de contraseñas con `hashlib.scrypt` de la biblioteca estándar.

## Flujo de Desarrollo

- Orden SDD en entorno agéntico (Google Antigravity + Spec Kit): constitución → especificar (`spec.md`) → planificar (`plan.md`, `data-model.md`, `contracts/`) → desglosar tareas (`tasks.md`) → implementar y verificar (`pytest`).
- Toda entrega MUST superar las pruebas de reglas de negocio, control de acceso por rol, trazabilidad OpenAPI/Swagger y trazabilidad estática del DOM.

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Las enmiendas requieren
descripción de impacto, aprobación explícita del usuario y versionado semántico (MAJOR, MINOR, PATCH).
La guía operativa diaria para agentes reside en `AGENTS.md`.

**Version**: 1.4.0 | **Ratified**: 2026-11-10 | **Last Amended**: 2026-11-26
