---
description: "Lista de tareas de la fase de Transición (Iteración T1): despliegue, humo, RNF-03, manuales e hitos IOC/PR"
---

# Tasks: Fase de Transición y validación de hitos IOC / PR (Iteración T1)

**Input**: Documentos de diseño en `/specs/004-transicion-despliegue/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), iteraciones C1–C4 completadas (`001`, `002`, `003`)

## Phase 1: Automatización de Arranque y Semilla (`FR-001`, `FR-002`)

- [X] T001 Crear `scripts/arrancar.ps1` (Windows PowerShell) para validar `.env`, sincronizar dependencias con `uv sync`, ejecutar `uv run python -m app.seed` y levantar `uvicorn app.main:app`
- [X] T002 [P] Crear `scripts/arrancar.sh` (Linux/macOS) equivalente a `arrancar.ps1` sin credenciales embebidas (Principio VI)
- [X] T003 Verificar idempotencia de `app/seed.py` con usuarios por rol, vínculo `tecnico_id`, catálogo de 8 repuestos y 7 órdenes en los estados del ciclo AUP

---

## Phase 2: Pruebas de Humo y Rendimiento Concurrente `RNF-03` (`FR-003`)

- [X] T004 [P] Implementar en `tests/test_transicion_humo_rnf03.py` la prueba `test_transicion_humo_seed_y_salud_integral` que inicializa una base limpia con `app.seed` y verifica interfaz `/`, `/docs`, login de ambos roles, resumen KPI, almacén y aislamiento `RN-03`
- [X] T005 [P] Implementar en `tests/test_transicion_humo_rnf03.py` la prueba `test_rnf03_rendimiento_y_atomicidad_5_sesiones_100_intentos` (5 sesiones concurrentes de Técnico, 100 intentos de reserva, verificación de `p95 <= 1.0 s` e invariante `stock_reservado <= stock_disponible`)
- [X] T006 Ejecutar `uv run pytest` completo comprobando el paso del 100 % de las pruebas de Construcción y Transición

---

## Phase 3: Documentación Operativa y Evaluación de Hitos (`FR-004`)

- [X] T007 [P] Redactar `docs/transicion/plan-despliegue.md` con requisitos previos, configuración de `.env`, comandos de despliegue, respaldo/restauración SQLite WAL y plan de evolución a AWS (`sa-east-1`)
- [X] T008 [P] Redactar `docs/transicion/manual-usuario-taller.md` para los actores Recepcionista (`GUI-01`, `GUI-02`, `GUI-04`, `GUI-06`) y Técnico de laboratorio (`GUI-03`, `GUI-05`, almacén `CU-07`), incluyendo resolución de alertas `E01` y `E02`
- [X] T009 [P] Redactar `docs/transicion/evaluacion-hitos-ioc-pr.md` con las pruebas de aceptación de `C1–C4` y la lista de verificación de los hitos **IOC** y **PR**
- [ ] T010 **[Tarea humana — Equipo / ByteFix Lab]** Ejecutar sesión presencial de capacitación y validación del manual con personal real de Recepción y Laboratorio ajeno al desarrollo para firmar el acta definitiva de puesta en producción (mitigación final del riesgo `R4`)
