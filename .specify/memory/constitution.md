<!--
Sync Impact Report
- Version change: 1.2.0 → 1.3.0
- Aprobación: el usuario aprobó la enmienda de forma explícita (2026-11-12) al planificar
  specs/002-interfaz-recepcion-rol, con las dependencias que quedan sin Playwright.
- Principios modificados: VI. Sin credenciales en el repositorio (aclaración: se permite versionar una
  plantilla `.env.example` con los nombres de las variables y sin valores secretos).
- Principios añadidos: ninguno
- Secciones modificadas: Restricciones Técnicas (el stack incorpora las dependencias de ejecución
  `pyjwt`, `python-multipart` y `python-dotenv`, con su motivo; se fija la regla para futuras
  dependencias permanentes)
- Secciones eliminadas: ninguna
- Justificación MINOR: amplía de forma material la guía técnica (nuevas dependencias permanentes y una
  aclaración al principio VI); no elimina ni redefine ningún principio, por lo que no es incompatible
  hacia atrás con los artefactos existentes.
- Plantillas revisadas: .specify/templates/plan-template.md (solo remite al archivo de la constitución,
  sin cambios), spec-template.md, tasks-template.md y checklist-template.md (no citan la versión ni el
  stack; sin cambios).
- Artefactos afectados: specs/002-interfaz-recepcion-rol/plan.md (la condición de enmienda queda
  resuelta); AGENTS.md (la sección Stack se alinea con esta versión). specs/001-recepcion-orden-servicio
  no requiere migración: sus dependencias no cambian.
- Pendientes: ninguno
-->
# aup-sdd-caso Constitution

## Core Principles

### I. Documentación AUP como fuente de verdad
Los documentos AUP en `docs/aup/` son la fuente de verdad de los requisitos. Sus códigos de
trazabilidad (casos de uso `CU-xx` y reglas de negocio `RN-xx`) MUST conservarse tal cual en
especificaciones, planes, tareas, código y pruebas; no se renombran, renumeran ni reutilizan.
Todo endpoint MUST trazarse a un `CU-xx` y toda validación a una `RN-xx`. El código `CP-AAAA-NNNN`
es el número del comprobante de pago interno (un dato del dominio) y NO es un caso de prueba; los
casos de prueba se derivan del curso básico y de los cursos alternos de las narrativas de los
casos de uso, y se identifican con el código `CU-xx-<curso>`: `CU-01-B` para el curso básico y
`CU-01-5a`, `CU-01-6a`, etc. para los cursos alternos, con la misma numeración que las narrativas
en `docs/aup/caso.md`. `docs/aup/` MUST NOT modificarse salvo petición explícita del usuario; si un requisito parece
incorrecto o incompleto, se reporta en lugar de corregirlo en silencio.

### II. Especificación antes que código
Ninguna funcionalidad se implementa sin una especificación (`specs/*/spec.md`), un plan y una lista
de tareas (`tasks.md`) aprobados. El trabajo de implementación MUST limitarse a tareas de
`tasks.md`. Si el código y la especificación divergen, se corrige primero la especificación y luego
el código.

### III. Pruebas automatizadas obligatorias (NON-NEGOTIABLE)
Cada regla de negocio `RN-xx` dentro del alcance de la iteración en curso MUST tener al menos una
prueba automatizada con pytest que identifique el código que cubre. Las `RN-xx` que queden fuera
del alcance de la iteración no requieren prueba en ella y MUST registrarse como pendientes según
el principio VII. Los casos de prueba (`CU-xx-B` y `CU-xx-<curso alterno>`, p. ej. `CU-01-5a`)
también MUST automatizarse cuando su `CU-xx` esté en el alcance de la iteración, y la prueba
MUST nombrar o documentar el código que cubre.
Una tarea no se considera terminada mientras sus pruebas no existan y pasen (`uv run pytest`). Las
pruebas se escriben junto con el cambio que verifican, nunca se omiten ni se desactivan para hacer
pasar una entrega.

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
los archivos locales con secretos (p. ej. `.env`) MUST estar en `.gitignore`. Se permite versionar una
plantilla `.env.example` que liste los nombres de las variables sin ningún valor secreto (valores
vacíos o descripciones), para que se sepa qué configurar; las pruebas generan sus propios valores en
tiempo de ejecución.

### VII. Alcance acotado por iteración
Cada iteración tiene un alcance explícito, definido por sus especificaciones y tareas. Trabajo fuera
de ese alcance (funcionalidades extra, refactors oportunistas, requisitos nuevos) MUST registrarse
para una iteración futura en lugar de incluirse en la actual. Las `RN-xx` y casos de uso que
queden fuera del alcance se registran como pendientes (con su código AUP) en la especificación o
en `tasks.md` de la iteración, de modo que ninguna se pierda ni se implemente sin prueba.

### VIII. Alcance cerrado
Solo se especifica e implementa lo que se traza a un `RF-xx`, `RNF-xx`, `CU-xx` o `RN-xx` de
`docs/aup/` (los RF y RNF están en `docs/aup/requerimientos.md`). Está prohibido agregar
funcionalidades, pantallas, campos o endpoints no pedidos, aunque parezcan útiles; una idea de ese
tipo se reporta al usuario en lugar de incluirse. Toda especificación (`spec.md`) MUST incluir una
matriz de trazabilidad (cada historia, requisito, endpoint, pantalla y campo con su código AUP) y
una lista "Fuera de alcance". Un elemento sin código AUP que lo respalde MUST eliminarse o
consultarse con el usuario antes de continuar.

## Restricciones Técnicas

- Stack: Python 3.12, FastAPI, SQLAlchemy, SQLite y pytest, gestionado con `uv`.
- Estructura: `app/` (`api`, `services`, `models`, `repositories`) y `tests/`.
- Interfaz web: se permite una interfaz con HTML, CSS y JavaScript sin framework (ni de frontend ni
  de compilación), servida por FastAPI. Cada pantalla y cada campo MUST cumplir el principio VIII.
- Artefactos de la fase de Transición: se guardan en `docs/transicion/` (no en `docs/aup/`, que
  permanece protegido por el principio I).
- Ejecución: `uv run uvicorn app.main:app --reload`; pruebas: `uv run pytest`.
- Dependencias de ejecución adicionales aprobadas (enmienda 1.3.0, para la autenticación OAuth2 con
  JWT de RNF-02 y la lectura de `.env`; justificación en `specs/002-interfaz-recepcion-rol/research.md`,
  D12): `pyjwt` (firma y verificación de JWT), `python-multipart` (la exige FastAPI para el formulario
  del flujo OAuth2 de contraseña) y `python-dotenv` (lectura de `.env`). El hash de contraseñas usa la
  biblioteca estándar (`hashlib.scrypt`), sin dependencia adicional.
- Añadir dependencias o tecnologías fuera de este stack y de las dependencias aprobadas arriba requiere
  justificación en el plan de la funcionalidad y enmienda de esta constitución si es permanente.

## Flujo de Desarrollo

- Orden: especificar → planificar → generar tareas → implementar, usando los comandos de Spec Kit.
- `.specify/memory/` MUST NOT modificarse salvo petición explícita del usuario, salvo mediante el
  flujo de enmienda de la sección Governance.
- Toda revisión de cambios MUST verificar: trazabilidad CU/RN, existencia de pruebas para las RN del alcance, respeto de
  las capas, ausencia de credenciales y alcance cerrado (nada sin código AUP).

## Governance

Esta constitución prevalece sobre cualquier otra práctica del proyecto. Las enmiendas requieren
descripción del cambio, aprobación explícita del usuario y, cuando afecten a artefactos existentes,
un plan de migración de los mismos. El versionado es semántico: MAJOR para eliminar o redefinir
principios de forma incompatible, MINOR para añadir principios o ampliar guía de forma material,
PATCH para aclaraciones y correcciones de redacción. Cada plan y revisión MUST incluir una
verificación de cumplimiento de estos principios; cualquier complejidad adicional MUST justificarse
por escrito. La guía operativa para agentes está en `AGENTS.md`.

**Version**: 1.3.0 | **Ratified**: 2026-11-10 | **Last Amended**: 2026-11-12
