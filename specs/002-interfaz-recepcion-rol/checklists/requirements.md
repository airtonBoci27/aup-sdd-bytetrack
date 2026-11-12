# Specification Quality Checklist: Interfaz web de recepción con acceso por rol (Iteración C1)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-12
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Constitución (principio VIII, alcance cerrado)

- [x] Matriz de trazabilidad: cada historia, requisito, pantalla, campo y operación con su código AUP
- [x] Lista «Fuera de alcance» presente
- [x] Ningún elemento sin código AUP (el inicio de sesión se traza a RNF-02 y a la precondición de CU-01)

## Notes

- Validación 2: sin marcadores [NEEDS CLARIFICATION]. Q1 (Tipo como texto libre, D1) y Q2 (cola en el selector, D2) resueltas por el usuario y registradas como desviaciones justificadas respecto de GUI-01.
- Trazabilidad rehecha contra `docs/aup/requerimientos.md` (RF-01, RF-02, RNF-02, RNF-04). «Cerrar sesión» incorporado por RNF-02 («sesiones activas», D3).
- Parte restante de RNF-02 (roles de decisión, cobro, diagnóstico y finalización) registrada como pendiente.
- Al planificar: actualizar spec, contrato y plan de 001 («sin autenticación», cola en «Listar técnicos disponibles»).
- Validación 3 (2026-11-12, al planificar): SC-007 y la tabla de casos de prueba se ajustaron a la decisión del usuario de no automatizar pruebas en navegador; la pantalla se verifica con [verificacion-manual.md](verificacion-manual.md) y los cursos CU-01 siguen cubiertos por las pruebas de API de 001. Se añadió la plantilla `.env.example` (sin valores secretos) a las Assumptions. Sin cambios en el alcance.
- Validación 4 (2026-11-12): se eliminaron los elementos sin origen en `docs/aup/`: la cláusula «no revelar cuál dato falló» de FR-002 (queda el rechazo de credenciales inválidas, RNF-02), FR-013 (descartar el cliente al cambiar el DNI), SC-002 (plazos) y SC-005 (comprensión de mensajes). Los números FR-013, SC-002 y SC-005 se conservan como «eliminado» para no alterar referencias.
