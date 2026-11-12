# AGENTS.md

Reglas para agentes que trabajan en este proyecto.

## Contexto

Sistema web derivado de documentación AUP (Agile Unified Process). La documentación en `docs/aup/` es la **fuente de verdad** de los requisitos (casos de uso CU-xx, reglas de negocio RN-xx) y **no se modifica**. Los casos de prueba se derivan del curso básico y de los cursos alternos de las narrativas (`docs/aup/caso.md`) y se identifican como `CU-xx-<curso>`: `CU-01-B` para el curso básico y `CU-01-5a`, `CU-01-6a`, etc. para los alternos, con la numeración de la narrativa. Ojo: `CP-AAAA-NNNN` es el número del comprobante de pago interno (dato del dominio), **no** un caso de prueba.

Los requisitos funcionales (RF) y no funcionales (RNF) están en `docs/aup/requerimientos.md`.

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

## Definición de terminado

Una tarea termina cuando `uv run pytest` pasa completo y se reporta el resultado (cuántas pruebas pasaron y, si alguna falla, la salida del fallo).

## Ante la duda

Si un requisito de `docs/aup/` es ambiguo o contradictorio, pregunta antes de asumir.

## Mapa de funcionalidades

Lista de las carpetas de `specs/` con su alcance. Se actualiza al crear cada una.

| Carpeta | Alcance |
|---------|---------|
| `specs/001-recepcion-orden-servicio/` | Iteración C1: CU-05 Buscar cliente, CU-06 Registrar nuevo cliente y CU-01 Registrar orden de servicio (curso básico y cursos alternos 2a, 2b, 5a y 6a). Reglas: RN-01, RN-02, RN-03 (solo asignación a un técnico disponible) y RN-10. RNF-04 (idempotencia) cubierto por RN-10; RNF-01, RNF-02 y RNF-03 pendientes. Fuera de alcance: autenticación OAuth2/JWT y CU-02, CU-03, CU-04, CU-07 y CU-08. |
| `specs/002-interfaz-recepcion-rol/` | Interfaz web de recepción de C1 con acceso por rol: inicio de sesión y control de acceso (RNF-02: solo Recepcionista con sesión activa usa CU-01, CU-05 y CU-06; el Técnico es rechazado) y pantallas GUI-01 y GUI-02 con alerta E01 e ID de operación (RF-01, RF-02, RNF-04). Consume la API de la 001 sin cambiar sus reglas. Fuera de alcance: listados, edición, reportes, gestión de usuarios y cierre de sesión, GUI-03 a GUI-06 y CU-02, CU-03, CU-04, CU-07 y CU-08. Pendientes: RN-03 (parte de acceso), RNF-01 y RNF-03. |
