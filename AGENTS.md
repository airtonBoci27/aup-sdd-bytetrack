# AGENTS.md

Reglas para agentes que trabajan en este proyecto.

## Contexto

Sistema web derivado de documentación AUP (Agile Unified Process). La documentación en `docs/aup/` es la **fuente de verdad** de los requisitos (casos de uso CU-xx, reglas de negocio RN-xx) y **no se modifica**. Los casos de prueba se derivan del curso básico y de los cursos alternos de las narrativas (`docs/aup/caso.md`) y se identifican como `CU-xx-<curso>`: `CU-01-B` para el curso básico y `CU-01-5a`, `CU-01-6a`, etc. para los alternos, con la numeración de la narrativa. Ojo: `CP-AAAA-NNNN` es el número del comprobante de pago interno (dato del dominio), **no** un caso de prueba.

## Stack

- Python 3.12
- FastAPI
- SQLAlchemy + SQLite
- pytest
- Gestor de entorno y dependencias: uv

## Estructura

```
app/
  api/            # Routers/endpoints FastAPI
  services/       # Lógica de negocio
  models/         # Modelos SQLAlchemy y esquemas
  repositories/   # Acceso a datos
  main.py         # Punto de entrada de la aplicación
tests/            # Pruebas automatizadas (pytest)
docs/aup/         # Documentación AUP (solo lectura)
specs/*/          # Especificaciones y tasks.md por funcionalidad
```

## Comandos

```bash
uv run uvicorn app.main:app --reload   # Ejecutar la aplicación
uv run pytest                          # Ejecutar las pruebas
```

## Reglas

1. **Alcance de trabajo:** trabaja solo sobre tareas definidas en `specs/*/tasks.md`. No implementes nada que no esté en una tarea.
2. **Trazabilidad de endpoints:** cada endpoint se traza a un caso de uso `CU-xx` (indícalo en el docstring o la descripción del endpoint).
3. **Trazabilidad de validaciones:** cada validación se traza a una regla de negocio `RN-xx` (indícalo en el código o mensaje de la validación).
4. **Pruebas obligatorias:** toda regla de negocio `RN-xx` dentro del alcance de la iteración en curso debe tener una prueba automatizada en `tests/`; los casos de prueba (`CU-xx-B`, `CU-xx-<curso alterno>`) de los casos de uso en alcance también se automatizan. Las `RN-xx` fuera del alcance se registran como pendientes (con su código) en la especificación o en `tasks.md`, no se implementan sin prueba. Nombra o documenta cada prueba con el código que cubre (`RN-xx` o `CU-xx-<curso>`).
5. **Documentación protegida:** no modifiques `docs/aup/` ni `.specify/memory/` salvo que el usuario lo pida explícitamente.
6. **Credenciales:** no incluyas credenciales, tokens ni secretos en el código ni en el repositorio. Usa variables de entorno.
7. **Capas:** respeta la separación `api` → `services` → `repositories` → `models`; la lógica de negocio va en `services`, no en los endpoints.
