# Evaluación de Aceptación y Lista de Verificación de Hitos IOC y PR

**Proyecto**: ByteTrack — ByteFix Lab · **Fase AUP**: Cierre de Construcción (`IOC`) y Transición (`PR`)

## 1. Matriz de Pruebas de Aceptación por Iteración (`caso.md` §4.1)

| Iteración | Casos de Uso y Pantallas | Criterio de aceptación AUP | Evidencia automatizada (`pytest`) | Resultado |
|-----------|--------------------------|----------------------------|-----------------------------------|-----------|
| **C1** | `CU-05`, `CU-06`, `CU-01` (`GUI-01`, `GUI-02`) | Valida DNI 8 dígitos, serie única, bloqueo `E01` de orden activa, técnico disponible, acceso Recepcionista e idempotencia `ID OP`. | `test_cu05_*.py`, `test_cu06_*.py`, `test_cu01_*.py`, `test_rnf02_*.py` | **ACEPTADO** |
| **C2** | `CU-07`, `CU-02` (`GUI-03`) | Consulta paginada de stock libre, cálculo en servidor, reserva atómica todo-o-nada (`E02`), soporte sin repuestos y restricción `RN-03`. | `test_flujo_taller.py`, `test_transicion_humo_rnf03.py` | **ACEPTADO** |
| **C3** | `CU-03`, `CU-08` (`GUI-04`, `GUI-05`) | Registra canal, fecha y evidencia; mantiene o libera reservas según decisión; consume stock solo con `prueba_conforme = true`. | `test_flujo_taller.py` | **ACEPTADO** |
| **C4** | `CU-04` (`GUI-06`) e integración | Cobro único exacto en `LISTO` (y devolución `RN-11` en `RECHAZADO`), conformidad obligatoria, emisión `CP-AAAA-NNNN` y paso a `ENTREGADO`. | `test_flujo_taller.py`, `test_trazabilidad_swagger.py`, `test_interfaz_estatica.py` | **ACEPTADO** |

## 2. Evaluación del Hito IOC (Capacidad Operativa Inicial — Fin de Construcción)

- [X] Ocho casos de uso (`CU-01` a `CU-08`) implementados y trazados en los 17 endpoints REST.
- [X] Seis pantallas AUP (`GUI-01` a `GUI-06`) operativas sin recursos externos ni `innerHTML`, con trazabilidad `data-trace` al 100 %.
- [X] Once reglas de negocio (`RN-01` a `RN-11`) y cuatro requerimientos no funcionales (`RNF-01` a `RNF-04`) verificados con pruebas automatizadas.
- [X] Cero credenciales o secretos versionados en el repositorio (`.env.example` limpio auditado por prueba).

**Dictamen IOC**: **CUMPLIDO AL 100 %**.

## 3. Evaluación del Hito PR (Product Release — Fase de Transición)

- [X] Scripts reproducibles de instalación, semilla y arranque (`scripts/arrancar.ps1` y `scripts/arrancar.sh`) operativos.
- [X] Pruebas de humo integrales sobre datos semilla (`app.seed`) superadas.
- [X] Prueba de concurrencia y rendimiento `RNF-03` (5 sesiones concurrentes, 100 intentos, `p95 <= 1.0 s`) superada sin corrupción de stock.
- [X] Plan de despliegue, respaldo WAL y manual de usuario por rol entregados en `docs/transicion/`.
- [ ] Validación presencial del manual con personal real del taller ByteFix Lab (tarea humana `T010` previa al corte del talonario físico) y despliegue futuro en nube AWS (`sa-east-1`).

**Dictamen PR**: **APTO PARA OPERACIÓN LOCAL EN TALLER** (pendiente únicamente el acta humana `T010` y el paso opcional a nube AWS).
