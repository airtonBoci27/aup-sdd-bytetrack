# Quickstart: validación de la interfaz de recepción con acceso por rol

Guía para ejecutar y validar la funcionalidad. Contratos: [api-acceso.md](contracts/api-acceso.md) y [ui-gui01-gui02.md](contracts/ui-gui01-gui02.md). Modelo de datos: [data-model.md](data-model.md). Decisiones: [research.md](research.md).

## Prerrequisitos

- `uv` instalado (gestiona Python 3.12 y dependencias).
- Ningún secreto en el repositorio: la clave de firma y las contraseñas se leen del entorno (ver abajo).

## Configuración (archivo `.env` fuera del repositorio)

Copie la plantilla `.env.example` (solo nombres de variables, sin valores secretos) a `.env` en la raíz (ya está en `.gitignore`) —o a otra ruta, apuntada con `BYTETRACK_ENV_FILE`— y complete los valores. Las variables ya definidas en el entorno prevalecen sobre el archivo.

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `BYTETRACK_JWT_SECRET` | Sí | Clave de firma de los tokens, mínimo 32 caracteres |
| `BYTETRACK_RECEPCIONISTA_CLAVE` | Sí (para `app.seed`) | Contraseña del usuario Recepcionista |
| `BYTETRACK_TECNICO_CLAVE` | Sí (para `app.seed`) | Contraseña del usuario Técnico |
| `BYTETRACK_RECEPCIONISTA_USUARIO` | No (`recepcion`) | Nombre de usuario del Recepcionista |
| `BYTETRACK_TECNICO_USUARIO` | No (`tecnico`) | Nombre de usuario del Técnico |
| `BYTETRACK_SESION_MINUTOS` | No (`60`) | Duración de la sesión |
| `BYTETRACK_ENV_FILE` | No (`./.env`) | Ruta del archivo de entorno |
| `BYTETRACK_DB_PATH`, `BYTETRACK_COSTO_REVISION` | No | Heredadas de C1 |

Genere valores propios, por ejemplo: `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`. No los copie a ningún archivo versionado.

## Preparación y ejecución

```bash
uv sync                                    # instala dependencias (incluye las nuevas, ver research D12)
uv run python -m app.seed                  # técnicos de demostración y usuarios iniciales (idempotente)
uv run uvicorn app.main:app --reload       # abrir http://127.0.0.1:8000/
```

La interfaz se sirve en `/`; Swagger UI sigue en `/docs` (con el botón «Authorize»).

## Escenarios de validación manual

| Código | Escenario | Pasos | Resultado esperado |
|--------|-----------|-------|--------------------|
| RNF-02 | Acceso por rol | Iniciar sesión como Técnico; luego «Cerrar sesión» e iniciar como Recepcionista | Técnico: mensaje de rol sin acceso y sin pantalla de recepción. Recepcionista: GUI-01 con «Recepcionista · sesión activa» |
| RNF-02 | Sin sesión / sesión cerrada | En `/docs`, llamar `GET /clientes/12345678` sin «Authorize»; cerrar sesión y repetir con el token anterior | 401 `NO_AUTENTICADO` en ambos casos |
| RNF-02 | Técnico en la API | En `/docs`, autorizar con el usuario Técnico y llamar a cualquier operación de recepción | 403 `ROL_NO_PERMITIDO` |
| CU-01-B | Orden para cliente existente | Buscar el DNI de un cliente con equipos, elegir equipo, completar estado físico y falla, elegir técnico, «Generar orden de servicio» | Recuadro «N.° OS-AAAA-NNNN listo para imprimir»; la cola del técnico sube en 1 |
| CU-01-2a | DNI inexistente | Buscar un DNI nuevo; «Registrar nuevo cliente»; completar y «Guardar cliente» | GUI-01 queda con el cliente cargado |
| CU-01-2b | DNI ya registrado en el modal | En el modal, guardar un DNI existente | «El DNI ya está registrado»; carga el cliente existente |
| CU-01-5a | Equipo con orden activa | Generar una orden con la misma serie | Alerta E01 con el N.° de la orden activa; no se crea otra |
| CU-01-6a | Reintento | Presionar dos veces «Generar orden de servicio» (o reenviar tras un fallo) | Una sola orden; mismo N.°; ID de operación sin cambios hasta confirmar |

## Validación automatizada

```bash
uv run pytest
```

| Archivo | Cubre |
|---------|-------|
| `tests/test_rnf02_acceso.py` | RNF-02: login válido/inválido, 401 sin sesión/vencida/manipulada/cerrada, 403 al Técnico en las cinco operaciones, 401 antes que 422, cierre de sesión |
| `tests/test_rnf02_configuracion.py` | RNF-02: clave de firma obligatoria y de ≥ 32 caracteres; carga de `.env` sin sobrescribir el entorno; hash de contraseñas |
| `tests/test_rnf02_seed_usuarios.py` | RNF-02: carga de usuarios desde variables de entorno (idempotente; falla si falta una contraseña) |
| `tests/test_cu01_tecnicos_cola.py` | RN-03 / CU-01 paso 6: `cola` en técnicos disponibles |
| `tests/test_interfaz_estatica.py` | Servicio de la interfaz, trazabilidad de cada elemento (`data-trace`, ids del contrato de interfaz) y `.env.example` sin valores secretos |
| `tests/test_trazabilidad_swagger.py` | Actualizado: 7 operaciones, las de acceso con su etiqueta |
| Pruebas de C1 (`tests/test_cu0*.py`) | Pasan con el fixture `client` autenticado como Recepcionista. Único cambio: `test_rn03_solo_tecnicos_disponibles_en_lista` ahora espera el campo `cola` (FR-019) |

Criterio de aceptación: `uv run pytest` pasa completo (con `RNF-02` probado en la API y los casos `CU-01-<curso>` de 001 sin cambios) y la lista de verificación manual queda completada y registrada.

## Verificación manual de la pantalla

La pantalla (GUI-01, GUI-02, E01, ID de operación, cierre de sesión) se verifica con [checklists/verificacion-manual.md](checklists/verificacion-manual.md): 35 ítems con pasos, resultado esperado y requisito que verifican. Se ejecuta tras `uv run pytest` y se registra el resultado en esa misma lista. No hay pruebas automatizadas en navegador; los cursos `CU-01-B`, `2a`, `2b`, `5a` y `6a` están cubiertos de forma automatizada por las pruebas de API de 001.

## Fuera de alcance (no validar aquí)

Listados, edición, reportes, gestión de usuarios, GUI-03 a GUI-06, CU-02, CU-03, CU-04, CU-07, CU-08, RNF-01, RNF-03 y la parte restante de RNF-02 (roles de decisión, cobro, diagnóstico y finalización).
