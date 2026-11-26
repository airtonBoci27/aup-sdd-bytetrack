# Implementation Plan: Fase de Transición y validación de hitos IOC / PR (Iteración T1)

**Branch**: `004-transicion-despliegue` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

## Summary

Materializa la fase de Transición AUP para ByteTrack v1.0 (IOC completo sobre C1–C4): scripts de arranque automatizado para Windows PowerShell (`scripts/arrancar.ps1`) y sistemas POSIX (`scripts/arrancar.sh`), pruebas automatizadas de humo y concurrencia/rendimiento `RNF-03` (`tests/test_transicion_humo_rnf03.py`), y documentación de despliegue, operación por rol y evaluación de hitos IOC/PR en `docs/transicion/`.

## Technical Context

- **Platform**: Windows 11 (PowerShell) y Linux/macOS (Bash) con Python 3.12 gestionado mediante `uv`.
- **Database Operation**: SQLite local en modo `WAL` (`bytetrack.db`, `-wal`, `-shm`) con procedimiento documentado de respaldo en caliente y restauración.
- **Concurrency & Performance Benchmark (`RNF-03`)**: `concurrent.futures.ThreadPoolExecutor(max_workers=5)` ejecutando 100 intentos de reserva sobre instancias independientes de `TestClient` contra un archivo SQLite temporal compartido con `WAL` y `BEGIN IMMEDIATE`, midiendo `p95` con `time.perf_counter()`.

## Constitution Check (v1.4.0)

| Principio | Verificación | Estado |
|-----------|--------------|--------|
| I. Documentación AUP protegida | `docs/aup/` permanece intacto; todos los entregables van a `docs/transicion/` y `scripts/`. | PASA |
| III. Pruebas obligatorias | Se automatizan humo post-seed y `RNF-03` (5 sesiones, 100 intentos, `p95 <= 1.0 s`). | PASA |
| VI. Sin credenciales | Los scripts exigen `.env` configurado por el operador y jamás escriben claves fijas en el repositorio. | PASA |
| VIII. Alcance cerrado | Todos los documentos y pruebas trazan exclusivamente a `RF-01..06`, `RNF-01..04`, riesgo `R4`/`R5` e hitos IOC/PR. | PASA |

## Project Structure

```text
specs/004-transicion-despliegue/
├── spec.md                              # Especificación de Transición T1
├── plan.md                              # Plan de despliegue, pruebas y documentación
└── tasks.md                             # Tareas de transición (incluye validación humana final)

docs/transicion/
├── plan-despliegue.md                   # Instalación, .env, arranque, backup WAL y ruta AWS
├── manual-usuario-taller.md             # Guía operativa Recepcionista y Técnico (GUI-01 a GUI-06)
└── evaluacion-hitos-ioc-pr.md           # Matriz de aceptación C1–C4 y checklist de hitos IOC y PR

scripts/
├── arrancar.ps1                         # Script de despliegue local en Windows PowerShell
└── arrancar.sh                          # Script de despliegue local en Linux / macOS

tests/
└── test_transicion_humo_rnf03.py        # Pruebas de humo con app.seed y benchmark RNF-03 (p95 <= 1 s)
```
