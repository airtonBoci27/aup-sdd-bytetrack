# Lista de verificación manual: interfaz de recepción con acceso por rol

**Propósito**: verificar en un navegador lo que las pruebas automatizadas de la API no cubren (la pantalla). Se ejecuta al cerrar la implementación y se registra el resultado en esta misma lista.
**Spec**: [spec.md](../spec.md) · **Contrato de interfaz**: [ui-gui01-gui02.md](../contracts/ui-gui01-gui02.md) · **Prototipos**: `docs/aup/img/media/image7.png` (GUI-01) e `image10.png` (GUI-02)
**Código de caso**: cada ítem cita el `CU-01-<curso>` o el requisito que verifica; los cursos ya están cubiertos de forma automatizada en la API (001) y aquí se comprueba su efecto en pantalla.

## Preparación

- [ ] `.env` creado a partir de `.env.example`, con valores propios (nunca versionados), y `uv run python -m app.seed` ejecutado.
- [ ] `uv run uvicorn app.main:app --reload` en marcha; página abierta en `http://127.0.0.1:8000/`.
- [ ] Hay al menos un técnico disponible y uno no disponible (el seed carga tres técnicos; uno no está disponible).
- [ ] `uv run pytest` pasa completo antes de iniciar la verificación (resultado: ___ pruebas).

Anote en cada ítem: ✔ cumple · ✘ no cumple (con observación) · fecha y navegador usado: ____________

## A. Acceso por rol (RNF-02) — US1

| Ítem | Pasos | Resultado esperado | FR | ✔/✘ |
|------|-------|--------------------|----|-----|
| A1 | Abrir `/` sin sesión | Solo se ve el inicio de sesión (usuario, contraseña, «Iniciar sesión»); no hay datos de recepción | FR-001 | |
| A2 | Iniciar con contraseña incorrecta, y luego con un usuario inexistente | No se abre sesión y se muestra «Usuario o contraseña incorrectos» | FR-002 | |
| A3 | Iniciar como Recepcionista | Se muestra GUI-01 con «Recepcionista · sesión activa» y el botón «Cerrar sesión» | FR-006, FR-007 | |
| A4 | Recargar la página con la sesión activa | Se mantiene en GUI-01 (sesión en la pestaña) | FR-001 | |
| A5 | «Cerrar sesión», luego iniciar como Técnico | Tras cerrar: vuelve al inicio de sesión. Como Técnico: mensaje de rol sin acceso; ninguna pantalla ni dato de recepción | FR-004, FR-007 | |
| A6 | Con la sesión cerrada, pulsar «Atrás» del navegador | No se muestran datos de recepción; se exige iniciar sesión | FR-005, FR-007 | |
| A7 | Iniciar con `BYTETRACK_SESION_MINUTOS=1`, esperar 70 s y pulsar «Buscar cliente» | Vuelve al inicio de sesión con «Su sesión expiró»; no se crea nada | FR-005 | |

## B. Estructura de GUI-01 frente al prototipo — US2, US3

| Ítem | Qué revisar | FR | ✔/✘ |
|------|-------------|----|-----|
| B1 | Encabezado «ByteTrack v2.0 · Recepción GUI-01 · CU-01 / CU-05» y el indicador de estados con «Recepcionado» resaltado, sin acciones | FR-008 | |
| B2 | Sección 1: campo DNI, «Buscar cliente» y «Registrar nuevo cliente» (deshabilitado al inicio) | FR-009, FR-012 | |
| B3 | Sección 2: selector «Equipos del cliente», Tipo (texto libre), Marca, Modelo, N.° de serie, casillas «Cargador original» y «Funda / maletín», «Estado físico al ingreso (obligatorio)» | FR-014, FR-015, FR-016 | |
| B4 | Sección 3: «Falla reportada (obligatorio)», «Técnico disponible (solo disponibles)», «Costo de revisión» de solo lectura (S/ 40.00) y «Estado inicial: RECEPCIONADO» | FR-017 | |
| B5 | Pie: «ID de operación OP-… · repetir el envío no duplica la orden (RNF-04)», «Cancelar» y «Generar orden de servicio» | FR-026 | |
| B6 | No hay listados, edición, reportes ni gestión de usuarios en ninguna vista | Fuera de alcance | |

## C. Buscar cliente y registrar orden — `CU-01-B`

| Ítem | Pasos | Resultado esperado | FR | ✔/✘ |
|------|-------|--------------------|----|-----|
| C1 | Buscar un DNI con formato inválido (7 dígitos, letras) | Mensaje «El DNI debe tener 8 dígitos»; no se consulta | FR-010 | |
| C2 | Buscar el DNI de un cliente con dos equipos | Nombres, apellidos, teléfono y «Cliente encontrado»; el selector lista sus dos equipos | FR-011 | |
| C4 | Elegir un equipo existente | Sus datos se muestran y no se pueden editar | FR-014 | |
| C5 | Elegir «Ingresar equipo nuevo» y escribir un tipo cualquiera (p. ej. «Tablet») | El campo Tipo acepta texto libre | FR-016 | |
| C6 | Abrir el selector de técnico | Solo técnicos disponibles, con el formato «Nombre Apellido (N en cola)» | FR-018, FR-019 | |
| C7 | Pulsar «Generar orden de servicio» con falla, estado físico o técnico vacíos | No se envía; se señalan los campos faltantes | FR-020 | |
| C8 | Completar todo y generar | Recuadro «N.° OS-AAAA-NNNN listo para imprimir · el técnico recibe +1 en su cola»; al recargar el selector, la cola del técnico subió en 1 | FR-022 | |
| C9 | Dejar sin técnicos disponibles (marcar a todos como no disponibles en la base) | Mensaje de que no hay técnicos y «Generar orden de servicio» deshabilitado | FR-018 | |

## D. Cliente nuevo y modal GUI-02 — `CU-01-2a`, `CU-01-2b`

| Ítem | Pasos | Resultado esperado | FR | ✔/✘ |
|------|-------|--------------------|----|-----|
| D1 | Buscar un DNI inexistente | «Cliente no encontrado» y se habilita «Registrar nuevo cliente» (`CU-01-2a`) | FR-012 | |
| D2 | Abrir el modal | Título «Registrar nuevo cliente · CU-06 / GUI-02»; DNI precargado; campos Nombres, Apellidos, Teléfono (*) y Correo (opcional); nota «(*) campo obligatorio»; «Guardar cliente» y «Cancelar» | FR-028 | |
| D3 | Guardar con un campo obligatorio vacío o un DNI inválido | No se registra; se señala cada campo a corregir | FR-029 | |
| D4 | Guardar un cliente válido sin correo | El modal se cierra y GUI-01 muestra al cliente cargado con el selector de equipos vacío | FR-030 | |
| D5 | Abrir el modal con un DNI ya registrado y guardar (`CU-01-2b`) | Aviso «El DNI ya está registrado» en el modal, que sigue abierto con «Guardar cliente» deshabilitado; al pulsar «Cancelar», GUI-01 conserva al cliente existente con sus equipos; sin duplicados | FR-031 | |
| D6 | Abrir el modal y pulsar «Cancelar» | Se cierra sin registrar; GUI-01 conserva lo que tenía | FR-032 | |

## E. Alerta E01 — `CU-01-5a`

| Ítem | Pasos | Resultado esperado | FR | ✔/✘ |
|------|-------|--------------------|----|-----|
| E1 | Generar una orden para un equipo que ya tiene una orden activa | Alerta roja «Este número de serie ya posee la Orden activa N.° [X] en laboratorio» con el N.° correcto; no se crea otra orden y la cola del técnico no cambia | FR-023 | |
| E2 | Con E01 visible, elegir otro equipo | La alerta desaparece | FR-023 | |
| E3 | Provocar otros rechazos (serie de otro cliente, técnico que deja de estar disponible) | Se muestra el mensaje del servidor en el área de errores; no se genera la orden | FR-024 | |

## F. ID de operación y reintento — `CU-01-6a`

| Ítem | Pasos | Resultado esperado | FR | ✔/✘ |
|------|-------|--------------------|----|-----|
| F1 | Anotar el ID de operación; pulsar «Generar orden de servicio» dos veces seguidas | Una sola orden; el botón se deshabilita durante el envío; el mismo N.° en pantalla | FR-021 | |
| F2 | Provocar un rechazo (p. ej. E01), corregir y reenviar | El ID de operación no cambió entre intentos | FR-027 | |
| F3 | Tras confirmar una orden, iniciar otra recepción | El ID de operación es distinto | FR-027 | |
| F4 | Completar datos y pulsar «Cancelar» | GUI-01 vuelve al estado inicial, sin orden creada y con un ID de operación nuevo | FR-025, FR-027 | |
| F5 | Detener el servidor, pulsar «Generar orden de servicio», reiniciarlo y reenviar | Mensaje general de error sin datos técnicos y lo ingresado se conserva; el reenvío usa el mismo ID de operación | FR-024, FR-027 | |

## Resultado

- Ítems verificados: ___ / 35 · No cumplen: ___ (detallar abajo)
- Observaciones:
- Responsable y fecha:
