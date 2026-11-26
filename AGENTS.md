# AGENTS.md

Reglas operativas para agentes de desarrollo (Google Antigravity / Spec Kit) en el proyecto **ByteTrack**.

## Contexto

Sistema web de gestión de taller técnico para **ByteFix Lab**, derivado de la documentación AUP (Agile Unified Process). La documentación en `docs/aup/` (`caso.md` y `requerimientos.md`) es la **fuente de verdad** de los requisitos (casos de uso `CU-01` a `CU-08`, reglas de negocio `RN-01` a `RN-11`, requerimientos funcionales `RF-01` a `RF-06` y no funcionales `RNF-01` a `RNF-04`) y **no se modifica**.

Los casos de prueba se derivan del curso básico y de los cursos alternos de las narrativas (`docs/aup/caso.md`) y se identifican como `CU-xx-<curso>`: `CU-01-B` para el curso básico y `CU-01-5a`, `CU-02-9a`, `CU-04-3a`, etc. para los cursos alternos. Ojo: `CP-AAAA-NNNN` es el número del comprobante de pago interno emitido en `CU-04` (dato del dominio), **no** un caso de prueba.

## Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, Uvicorn
- **Persistencia**: SQLAlchemy 2.x + SQLite local (`WAL` + `BEGIN IMMEDIATE` para atomicidad `RNF-01`)
- **Frontend**: HTML5, CSS3 y JavaScript ES Modules nativo sin framework (`app/web/`)
- **Seguridad** (`RNF-02`, constitución 1.4.0): OAuth2 Password Flow con `pyjwt` (HS256), `python-multipart`, `python-dotenv` y hash de contraseñas con `hashlib.scrypt` + revocación de `jti`
- **Pruebas y entorno**: `pytest`, `httpx` y gestor `uv`

## Estructura

```text
app/
  api/              # Routers/endpoints FastAPI (auth, clientes, tecnicos, ordenes, taller, seguridad)
  services/         # Lógica de negocio y transacciones (auth, cliente, orden, flujo_taller)
  models/           # Entidades SQLAlchemy y esquemas Pydantic
  repositories/     # Acceso a datos (cliente, equipo, tecnico, orden, repuesto, operacion, usuario)
  web/              # Interfaz web estática (GUI-01 a GUI-06, panel KPI y almacén)
  config.py         # Lectura validada de variables de entorno (.env)
  database.py       # Motor SQLite, sesiones y BEGIN IMMEDIATE
  errors.py         # Excepciones de dominio con código estable (E01, E02, ...)
  security.py       # Hash scrypt y firma/verificación JWT HS256
  seed.py           # Carga idempotente de datos iniciales para Transición
  main.py           # Punto de entrada FastAPI, cabeceras HTTP defensivas y archivos estáticos
docs/
  aup/              # Documentación AUP de referencia (solo lectura)
  transicion/       # Entregables de la fase de Transición (despliegue, manuales, hitos IOC/PR)
scripts/            # Scripts reproducibles de arranque y verificación local (.ps1 / .sh)
specs/*/            # Artefactos SDD por iteración (spec.md, plan.md, data-model.md, contracts/, tasks.md)
tests/              # Suite automatizada pytest (trazabilidad CU/RN/RNF, concurrencia y humo)
```

## Comandos

```bash
uv run python -m app.seed              # Inicializar usuarios, técnicos, repuestos y órdenes demo
uv run uvicorn app.main:app --reload   # Levantar servidor local (API /docs + Web /)
uv run pytest                          # Ejecutar toda la suite automatizada de pruebas
powershell -ExecutionPolicy Bypass -File scripts/arrancar.ps1   # Arranque reproducible en Windows
```

## Reglas

1. **Alcance de trabajo:** trabaja únicamente sobre tareas definidas en `specs/*/tasks.md`. No implementes nada fuera de una especificación y lista de tareas aprobadas.
2. **Trazabilidad de endpoints:** cada endpoint se traza a su caso de uso y pantalla (`CU-xx · GUI-xx`) en sus etiquetas OpenAPI y documenta las reglas que aplica.
3. **Trazabilidad de validaciones e interfaz:** cada validación en código cita su `RN-xx` o `RNF-xx`, y cada elemento interactivo en `app/web/index.html` declara `data-trace` con códigos AUP válidos.
4. **Pruebas obligatorias:** toda regla `RN-xx` y `RNF-xx` en alcance debe contar con pruebas automatizadas en `tests/` que identifiquen el código verificado (`RN-xx`, `RNF-xx` o `CU-xx-<curso>`).
5. **Documentación protegida:** no modifiques `docs/aup/` salvo instrucción explícita del usuario; los artefactos de despliegue y operación van en `docs/transicion/`.
6. **Credenciales:** prohibido incluir contraseñas, claves JWT o secretos en código, pruebas o repositorio. Usa variables de entorno (`.env` ignorado y `.env.example` vacío).
7. **Capas:** respeta estrictamente `api` → `services` → `repositories` → `models`; la lógica de negocio y el control transaccional viven en `services`.

## Definición de terminado

Una tarea termina cuando `uv run pytest` pasa al 100 % sin errores y se reporta el conteo total de pruebas ejecutadas.

## Ante la duda

Si un requisito de `docs/aup/` presenta ambigüedad o vacío de diseño, consulta al usuario antes de asumir y registra la decisión en la especificación correspondiente.

## Mapa de funcionalidades

| Carpeta | Fase / Iteración AUP | Alcance |
|---------|----------------------|---------|
| `specs/001-recepcion-orden-servicio/` | Construcción — C1 (API) | `CU-05` Buscar cliente, `CU-06` Registrar nuevo cliente y `CU-01` Registrar orden de servicio (curso básico y alternos `2a`, `2b`, `5a` E01 y `6a` idempotencia). Reglas: `RN-01`, `RN-02`, `RN-03` (asignación) y `RN-10` (`RNF-04`). |
| `specs/002-interfaz-recepcion-rol/` | Construcción — C1 (Web + Seguridad) | Inicio/cierre de sesión OAuth2 + JWT HS256 y control de acceso por rol (`RNF-02`), cabeceras de seguridad HTTP y pantallas `GUI-01` y `GUI-02` (`RF-01`, `RF-02`, `RNF-04`). |
| `specs/003-flujo-integral-taller/` | Construcción — C2, C3 y C4 (IOC) | `CU-07` Consultar stock, `CU-02` Emitir diagnóstico y presupuesto (`GUI-03`, reserva atómica `RN-04`/`RNF-01`, alerta `E02`), `CU-03` Registrar decisión (`GUI-04`, `RN-05`, `RN-06`), `CU-08` Finalizar reparación (`GUI-05`, `RN-07`), `CU-04` Liquidar orden y entregar equipo (`GUI-06`, `RN-08`, `RN-09`, `RN-11`), restricción de bandeja por técnico (`RN-03`) y vistas operativas de trazabilidad (`RF-01` a `RF-06`). |
| `specs/004-transicion-despliegue/` | Transición — T1 (Hitos IOC y PR) | Despliegue local reproducible (`scripts/arrancar.ps1` y `scripts/arrancar.sh`), semilla integral (`app.seed`), pruebas de humo end-to-end, prueba de concurrencia y rendimiento (`RNF-03`, p95 ≤ 1 s), manuales de usuario por rol y acta de evaluación de hitos IOC/PR en `docs/transicion/`. |
