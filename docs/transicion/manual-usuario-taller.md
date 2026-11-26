# Manual de Usuario por Rol — ByteTrack v1.0 (ByteFix Lab)

**Fase AUP**: Transición (`T1`) · **Cobertura**: `GUI-01` a `GUI-06` (`CU-01` a `CU-08`)

---

## 1. Inicio y Cierre de Sesión (`RNF-02`)

1. Abrir `http://127.0.0.1:8000` en el navegador.
2. Ingresar el usuario asignado (`recepcion` para mostrador o `tecnico` para laboratorio) y su contraseña configurada.
3. El encabezado superior confirmará el perfil activo (`Recepcionista · sesión activa` o `Técnico de laboratorio · sesión activa`) y habilitará en la barra lateral únicamente los módulos autorizados para su rol.
4. Al finalizar su turno, presionar **Cerrar sesión** para revocar inmediatamente el token activo.

---

## 2. Guía para el Rol Recepcionista

### 2.1. Recepción de Equipos (`GUI-01` y `GUI-02` — `CU-05`, `CU-06`, `CU-01`)
1. Abrir **Recepción de Equipos** en la barra lateral.
2. **Paso 1 — Cliente**: ingresar el DNI de 8 dígitos y presionar **Buscar cliente**.
   - Si existe, se cargan sus nombres, teléfono y equipos previos.
   - Si no existe, se habilita **Registrar nuevo cliente** (`GUI-02`): completar DNI, nombres, apellidos, teléfono y correo opcional, y presionar **Guardar cliente**.
3. **Paso 2 — Equipo**: elegir un equipo registrado o seleccionar *Ingresar equipo nuevo* indicando tipo, marca, modelo y número de serie único; marcar accesorios dejados y detallar el **estado físico al ingreso**.
4. **Paso 3 — Orden**: describir la **falla reportada**, elegir un **técnico disponible** (se visualiza su cola actual) y verificar el costo de revisión (`S/ 40.00`).
5. Presionar **Generar orden de servicio**. Se mostrará el código `OS-AAAA-NNNN` listo para imprimir.

### 2.2. Decisión de Presupuesto (`GUI-04` — `CU-03`)
1. Abrir **Decisión de Presupuesto**, ingresar el código `OS-AAAA-NNNN` en estado `PRESUPUESTADO` y presionar **Buscar orden**.
2. Seleccionar **Aprobado** (mantiene repuestos reservados) o **Rechazado** (libera inmediatamente los repuestos al stock libre), elegir el **canal** (`WhatsApp`, `Llamada` o `Presencial`) y escribir la **evidencia textual** antes de confirmar.

### 2.3. Cobro y Entrega (`GUI-06` — `CU-04` y `RN-11`)
1. Abrir **Cobro y Entrega** y buscar una orden en estado `LISTO` (cobra presupuesto total) o `RECHAZADO` (cobra revisión inicial `S/ 40.00` por devolución).
2. Seleccionar método de pago (`Efectivo`, `Tarjeta` o `Transferencia`), ingresar el **monto total exacto**, marcar la casilla de **conformidad de entrega del equipo y accesorios** y presionar **Cobrar y entregar**.
3. Emitido el comprobante `CP-AAAA-NNNN`, presionar **Imprimir comprobante**; el equipo queda en `ENTREGADO` y su número de serie queda libre para futuros ingresos.

---

## 3. Guía para el Rol Técnico de Laboratorio

### 3.1. Diagnóstico y Presupuesto (`GUI-03` — `CU-07` y `CU-02`)
1. Abrir **Diagnóstico y Stock** y cargar una orden propia en estado `RECEPCIONADO` (el sistema bloquea órdenes asignadas a otros técnicos, `RN-03`).
2. Redactar el **informe técnico** e indicar el **costo de mano de obra**.
3. Si requiere piezas, buscar por SKU o nombre (`CU-07`), verificar las **unidades libres** y añadir al presupuesto (si es reparación de software, puede emitir con cero repuestos).
4. Presionar **Emitir diagnóstico y presupuesto** para reservar atómicamente el stock y pasar la orden a `PRESUPUESTADO`.

### 3.2. Finalizar Reparación (`GUI-05` — `CU-08`)
1. Abrir **Finalizar Reparación** y cargar una orden propia en estado `APROBADO`.
2. Detallar el **trabajo realizado**, marcar obligatoriamente **Prueba de funcionamiento conforme** (`RN-07`), describir el resultado de la prueba y presionar **Finalizar reparación**. El sistema consume definitivamente los repuestos y pasa la orden a `LISTO`.

---

## 4. Resolución de Alertas Frecuentes

| Código / Aviso | Significado | Acción del usuario |
|----------------|-------------|--------------------|
| **Alerta `E01`** (`GUI-01`) | El número de serie ya tiene una orden activa sin entregar (`RN-02`). | Consultar la orden activa indicada en el panel antes de abrir otra. |
| **Alerta `E02`** (`GUI-03`) | Otro técnico reservó el stock libre antes de confirmar (`RN-04`). Ningún ítem quedó reservado a medias. | Volver a buscar el repuesto actualizado o ajustar el presupuesto. |
| **`ID de operación OP-…`** | Protección contra doble clic o caída momentánea de red (`RNF-04`). | Puede reenviar con seguridad: el sistema devolverá la operación ya registrada sin duplicar órdenes, reservas ni cobros. |
