<!--
Sync Impact Report
- Version change: (plantilla sin ratificar) → 1.0.0
- Principios modificados: ninguno renombrado (se instancian por primera vez)
- Principios añadidos: I. Fuente de verdad AUP; II. Especificación antes que código;
  III. Pruebas automatizadas obligatorias; IV. Arquitectura en capas; V. Simplicidad e
  integraciones con dobles de prueba; VI. Sin credenciales en el repositorio;
  VII. Alcance acotado por iteración
- Secciones añadidas: Restricciones Técnicas; Flujo de Desarrollo
- Secciones eliminadas: ninguna (la plantilla se amplió de 5 a 7 principios)
- Pendientes: ninguno
-->
# aup-sdd-caso Constitution

## Core Principles

### I. Documentación AUP como fuente de verdad
Los documentos AUP en `docs/aup/` son la fuente de verdad de los requisitos. Sus códigos de
trazabilidad (casos de uso `UC-xx`, reglas de negocio `RN-xx` y casos de prueba `CP-xx`) MUST
conservarse tal cual en especificaciones, planes, tareas, código y pruebas; no se renombran,
renumeran ni reutilizan. Todo endpoint MUST trazarse a un `UC-xx` y toda validación a una `RN-xx`.
`docs/aup/` MUST NOT modificarse salvo petición explícita del usuario; si un requisito parece
incorrecto o incompleto, se reporta en lugar de corregirlo en silencio.

### II. Especificación antes que código
Ninguna funcionalidad se implementa sin una especificación (`specs/*/spec.md`), un plan y una lista
de tareas (`tasks.md`) aprobados. El trabajo de implementación MUST limitarse a tareas de
`tasks.md`. Si el código y la especificación divergen, se corrige primero la especificación y luego
el código.

### III. Pruebas automatizadas obligatorias (NON-NEGOTIABLE)
Cada regla de negocio `RN-xx` y cada caso de prueba `CP-xx` MUST tener al menos una prueba
automatizada con pytest que identifique el código que cubre. Una tarea no se considera terminada
mientras sus pruebas no existan y pasen (`uv run pytest`). Las pruebas se escriben junto con el
cambio que verifican, nunca se omiten ni se desactivan para hacer pasar una entrega.

### IV. Arquitectura en capas
El flujo de dependencias es API → servicio → repositorio. Los endpoints (`app/api`) solo validan
entrada, delegan y serializan; la lógica de negocio y las reglas `RN-xx` viven en `app/services`;
el acceso a datos vive en `app/repositories` sobre los modelos de `app/models`. Una capa MUST NOT
saltarse a la siguiente (p. ej. un endpoint no accede directamente a la base de datos).

### V. Simplicidad e integraciones con dobles de prueba
Se usa SQLite local como única base de datos y se prefiere la solución más simple que cumpla el
requisito (sin servicios, colas ni capas adicionales sin justificación escrita). Las integraciones
externas (pagos, facturación, correo) MUST aislarse tras una interfaz y reemplazarse por dobles de
prueba (fakes/mocks); ninguna prueba ni el entorno de desarrollo realiza llamadas reales a
servicios externos.

### VI. Sin credenciales en el repositorio
Contraseñas, tokens, claves de API y cualquier otro secreto MUST NOT aparecer en el código, las
pruebas, los datos de ejemplo ni el historial de git. Los secretos se leen de variables de entorno;
los archivos locales con secretos (p. ej. `.env`) MUST estar en `.gitignore`.

### VII. Alcance acotado por iteración
Cada iteración tiene un alcance explícito, definido por sus especificaciones y tareas. Trabajo fuera
de ese alcance (funcionalidades extra, refactors oportunistas, requisitos nuevos) MUST registrarse
para una iteración futura en lugar de incluirse en la actual.

## Restricciones Técnicas

- Stack: Python 3.12, FastAPI, SQLAlchemy, SQLite y pytest, gestionado con `uv`.
- Estructura: `app/` (`api`, `services`, `models`, `repositories`) y `tests/`.
- Ejecución: `uv run uvicorn app.main:app --reload`; pruebas: `uv run pytest`.
- Añadir dependencias o tecnologías fuera de este stack requiere justificación en el plan de la
  funcionalidad y enmienda de esta constitución si es permanente.

## Flujo de Desarrollo

- Orden: especificar → planificar → generar tareas → implementar, usando los comandos de Spec Kit.
- `.specify/memory/` MUST NOT modificarse salvo petición explícita del usuario, salvo mediante el
  flujo de enmienda de la sección Governance.
- Toda revisión de cambios MUST verificar: trazabilidad UC/RN/CP, existencia de pruebas, respeto de
  las capas y ausencia de credenciales.

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Las enmiendas requieren
descripción del cambio, aprobación explícita del usuario y, cuando afecten a artefactos existentes,
un plan de migración de los mismos. El versionado es semántico: MAJOR para eliminar o redefinir
principios de forma incompatible, MINOR para añadir principios o ampliar guía de forma material,
PATCH para aclaraciones y correcciones de redacción. Cada plan y revisión MUST incluir una
verificación de cumplimiento de estos principios; cualquier complejidad adicional MUST justificarse
por escrito. La guía operativa para agentes está en `AGENTS.md`.

**Version**: 1.0.0 | **Ratified**: 2026-11-10 | **Last Amended**: 2026-11-10
