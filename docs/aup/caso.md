Índice

[**1. Enfoque AUP del proyecto 1**](#enfoque-aup-del-proyecto)

[**2. Fase de Inicio 3**](#fase-de-inicio)

> [2.1. Visión del producto 3](#visión-del-producto)
>
> [2.2. Reglas de negocio 4](#reglas-de-negocio)
>
> [2.3. Lista de trabajo priorizada 4](#lista-de-trabajo-priorizada)
>
> [2.4. Lista de riesgos 5](#lista-de-riesgos)
>
> [2.5. Modelo de dominio inicial y casos de uso
> 6](#modelo-de-dominio-inicial-y-casos-de-uso)
>
> [2.6. Arquitectura candidata 8](#arquitectura-candidata)
>
> [Hito LCO: Objetivos del Ciclo de Vida 8](#_b8ci166qhlyn)

[3. Fase de elaboración 8](#fase-de-elaboración)

# 

# 

# **Enfoque AUP del proyecto**

El proyecto ByteTrack se organiza según el Proceso Unificado Ágil (AUP,
por sus siglas en inglés) en cuatro fases secuenciales, cada una cerrada
por un hito, y en siete disciplinas que se ejecutan de forma iterativa a
lo largo de todas las fases. Cada iteración de Construcción entrega una
versión de desarrollo funcional.

Se eligió AUP porque la ampliación del sistema ya está planificada
(CU-03, CU-04 y CU-08) y porque los riesgos técnicos principales, la
reserva atómica de stock y la idempotencia de las confirmaciones, deben
probarse de forma temprana, en la Elaboración, antes de construir el
resto del sistema.

**Tabla 1**

*Fases e Hitos de AUP*

  -------------- ------------------------------ ------------------------
  Fase           Objetivo                       Hito

  Inicio         Acordar alcance, visión,       LCO: Objetivos del ciclo
                 riesgos y plan                 de vida

  Elaboración    Probar la arquitectura y       LCA: Arquitectura del
                 detallar los requisitos        ciclo de vida
                 críticos                       

  Construcción   Construir y probar el sistema  IOC: Capacidad operativa
                 por iteraciones                inicial

  Transición     Validar con usuarios y poner   PR: Liberación del
                 en producción                  producto
  -------------- ------------------------------ ------------------------

*Nota.* Elaboración propia.

**Tabla 2**

*Intensidad de Cada Disciplina por Fase*

  -------------------------- -------- ------------- -------------- ------------
  Disciplina                  Inicio   Elaboración   Construcción   Transición
  Modelo                      Media       Alta          Media          ---
  Implementación               ---        Baja           Alta          Baja
  Prueba                       ---        Baja           Alta         Media
  Despliegue                   ---        Baja           Baja          Alta
  Gestión de configuración     Baja       Baja          Media         Media
  Gestión del proyecto         Alta       Media         Media         Media
  Entorno                     Media       Media          Baja          Baja
  -------------------------- -------- ------------- -------------- ------------

*Nota.* Elaboración propia.

**Tabla 3**

*Plan de Fases e Iteraciones (Estimado)*

  -------------- ---------------- --------- -------------------------------------------------------------------------------------------------------------
  Fase           Iteraciones      Semanas   Entregable principal
  Inicio         I1               1--2      Visión, reglas de negocio, lista de trabajo priorizada y riesgos
  Elaboración    E1, E2           3--6      Arquitectura probada (reserva atómica e idempotencia)
  Construcción   C1, C2, C3, C4   7--14     Versión 1.0 funcional (IOC): C1--C2 iteración 1 (CU-01, 02, 05, 06, 07) y C3--C4 ampliación (CU-03, 04, 08)
  Transición     T1               15--16    Sistema en uso en el taller (PR)
  -------------- ---------------- --------- -------------------------------------------------------------------------------------------------------------

*Nota.* Iteraciones de 2 semanas. Las fechas son una estimación inicial
que se recalibra al cierre de cada iteración. Elaboración propia.

# **Fase de Inicio**

## Visión del producto

La Tabla 4 resume el problema que atiende ByteTrack, la solución
propuesta, los usuarios, los objetivos y lo que queda fuera del alcance.

**Tabla 4**

*Visión del Producto*

  ------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Elemento           Descripción
  Problema           El taller pasó de 8 a 30 equipos diarios y gestiona las órdenes con talonario, hojas de cálculo y mensajes de presupuesto, lo que provoca pérdida de trazabilidad, asignación simultánea de repuestos y errores de liquidación.
  Solución           Sistema web que registra cada ingreso, mantiene una orden por equipo activo, reserva repuestos al emitir el presupuesto y controla el cobro antes de la entrega.
  Usuarios           Recepcionista y Técnico de laboratorio.
  Objetivos          Una sola orden activa por equipo; cero repuestos asignados a dos órdenes; 100 % de entregas con cobro y comprobante registrados; trazabilidad de cada equipo por estado.
  Fuera de alcance   Pagos parciales, pasarela bancaria, comprobantes tributarios electrónicos, compras, mantenimiento del catálogo y acceso directo del cliente.
  ------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

*Nota.* Elaboración propia.

**Tabla 5**

*Interesados del Proyecto*

  ------------------------ -------------------------------------------
  Interesado               Interés principal

  Dueño o administración   Control, trazabilidad y menos pérdidas por
  de ByteFix Lab           errores

  Recepcionista            Atender rápido sin duplicar órdenes ni
                           cobros

  Técnico de laboratorio   Ver solo sus órdenes y reservar repuestos
                           sin conflictos

  Persona de almacén       Stock confiable (administra físicamente los
                           componentes)

  Cliente                  Conocer el costo y el estado de su equipo
                           (no accede directamente al sistema)
  ------------------------ -------------------------------------------

*Nota.* Elaboración propia.

## **Reglas de negocio**

Las reglas de negocio de la Tabla 6 se derivan de los requerimientos
funcionales (RF-01 a RF-06) y no funcionales (RNF-01 a RNF-04) del
proyecto.

**Tabla 6**

*Reglas de Negocio*

  -------- --------------------------------------------------------------------------------------------------------------------------------------------------
  Código   Regla
  RN-01    El cliente se identifica por DNI único de 8 dígitos y puede tener varios equipos, cada uno con número de serie único.
  RN-02    Un equipo no puede tener una nueva orden mientras tenga otra sin entregar.
  RN-03    La orden solo se asigna a un técnico disponible, y el técnico solo accede a sus órdenes asignadas.
  RN-04    El presupuesto reserva todos los repuestos requeridos o ninguno, sobre el stock libre (no reservado por otras órdenes).
  RN-05    La decisión del cliente exige canal, fecha y evidencia textual.
  RN-06    Si el cliente aprueba, se mantienen las reservas; si rechaza, se liberan de inmediato.
  RN-07    La reparación solo se finaliza con prueba de funcionamiento conforme; al finalizar, los repuestos reservados se consumen definitivamente.
  RN-08    El cobro es por el total, en un solo pago, con la orden en estado Listo.
  RN-09    El pago, el comprobante interno y el paso a Entregado se confirman en una sola transacción.
  RN-10    Repetir una solicitud con el mismo identificador de operación no duplica órdenes, reservas, pagos ni comprobantes.
  RN-11    *(Propuesta)* Si el cliente rechaza el presupuesto, se cobra el costo de revisión (S/ 40 en el prototipo). Pendiente de confirmar con el taller.
  -------- --------------------------------------------------------------------------------------------------------------------------------------------------

*Nota.* Elaboración propia.

## **Lista de trabajo priorizada**

En AUP los requisitos forman una pila priorizada; los de mayor riesgo y
valor se abordan primero (ver Tabla 7).

**Tabla 7**

*Lista de Trabajo (Casos de Uso)*

  -------- ------------------------- ----------- -------- --------------
  Código   Caso de uso                Prioridad   Riesgo    Iteración

  CU-05    Buscar cliente               Alta       Bajo         C1

  CU-06    Registrar nuevo cliente      Alta       Bajo         C1

  CU-01    Registrar orden de           Alta      Medio         C1
           servicio                                       

  CU-07    Consultar stock de           Alta      Medio         C2
           repuestos                                      

  CU-02    Emitir diagnóstico y         Alta       Alto   E1 (prueba) ·
           presupuesto                                          C2

  CU-03    Registrar decisión de        Alta      Medio         C3
           presupuesto                                    

  CU-08    Finalizar reparación         Media     Medio         C3

  CU-04    Liquidar orden y entregar    Alta       Alto   E2 (prueba) ·
           equipo                                               C4
  -------- ------------------------- ----------- -------- --------------

*Nota.* E1 prueba la reserva atómica de repuestos (RNF-01) con CU-02. E2
prueba la idempotencia del cobro (RNF-04) con CU-04. Elaboración propia.

## **Lista de riesgos**

La Tabla 8 presenta los riesgos iniciales del proyecto, su probabilidad,
su impacto y la mitigación prevista.

**Tabla 8**

*Riesgos Iniciales*

  ----- ------------------------------------------------------------------------- ------- --------- ------------------------------------------------------------------------ --------------
   N.°  Riesgo                                                                     Prob.   Impacto  Mitigación                                                               Fase
   R1   Dos técnicos reservan la última unidad de un repuesto                      Alta     Alto    Bloqueo de fila y reserva todo o nada; prueba de concepto (RNF-01)       Elaboración
   R2   Reintentos o doble clic duplican cobros, reservas o comprobantes           Media    Alto    Identificador de operación e idempotencia; prueba de concepto (RNF-04)   Elaboración
   R3   Las reglas se saltan llamando a la API o un técnico ve órdenes ajenas      Media    Alto    OAuth2 con JWT y reglas en el dominio (RNF-02)                           Elaboración
   R4   El personal no adopta el sistema y sigue con el talonario                  Media    Medio   Prototipos validados con usuarios; capacitación                          Inicio
   R5   No se cumple el rendimiento esperado (p95 ≤ 1 s con 5 sesiones, RNF-03)    Media    Medio   Prueba de carga antes de cerrar la Elaboración                           Elaboración
   R6   Regla RN-11 (cobro de revisión) sin aprobar                                Media    Bajo    Decisión del dueño del taller antes de C4                                Construcción
   R7   Costos de nube mayores a lo previsto                                       Baja     Medio   Presupuesto y alarmas de facturación                                     Transición
  ----- ------------------------------------------------------------------------- ------- --------- ------------------------------------------------------------------------ --------------

*Nota.* Prob. = probabilidad. Elaboración propia.

## **Modelo de dominio inicial y casos de uso**

El modelo de dominio inicial identifica las ocho clases conceptuales del
negocio: Cliente, Equipo, Tecnico, OrdenServicio, Diagnostico,
DetalleRepuesto, Repuesto y ComprobantePago (ver Figura 1). Se refina en
la fase de Elaboración (sección 3.4).

**Figura 1**

*Modelo de Dominio Inicial de ByteTrack*

![Título: Modelo de dominio inicial - Descripción: Diagrama de clases
del dominio de
ByteTrack](docs/aup/img/media/image2.gif){width="3.9583333333333335in"
height="4.652777777777778in"}

*Nota.* Elaboración propia.

Los casos de uso del sistema tienen dos actores: el Recepcionista
(CU-01, CU-03, CU-04, CU-05 y CU-06) y el Técnico de laboratorio (CU-02
y CU-07), como se muestra en la Figura 2. CU-01 incluye a CU-05 y se
extiende con CU-06 cuando el cliente no existe; CU-02 incluye a CU-07.

**Figura 2**

*Diagrama de Casos de Uso de ByteTrack*

![Título: Diagrama de casos de uso - Descripción: Casos de uso de
ByteTrack con Recepcionista y
Técnico](docs/aup/img/media/image3.jpg){width="6.25in"
height="2.1527777777777777in"}

*Nota.* El caso de uso CU-08 (Finalizar reparación, a cargo del Técnico)
pertenece a la ampliación y se incorporará al diagrama en la fase de
Elaboración. Elaboración propia.

## **Arquitectura candidata**

La arquitectura candidata es una aplicación web de tres capas en la
nube: frontend estático (S3 con CloudFront y WAF), API REST (FastAPI en
ECS Fargate tras un balanceador de carga) y base de datos relacional
(PostgreSQL en RDS Multi-AZ), con SES para avisos por correo. La
seguridad se basa en OAuth2 con JWT. Esta arquitectura se prueba en la
fase de Elaboración.

**Hito LCO: Objetivos del Ciclo de Vida**

El hito se considera cumplido cuando se verifica lo siguiente:

> • Visión e interesados acordados.
>
> • Lista de trabajo priorizada y estimada.
>
> • Riesgos identificados con mitigación.
>
> • Plan de fases e iteraciones aprobado.

- Arquitectura candidata definida

# **Fase de elaboración**

Se detallarán los requisitos críticos del negocio y probar la
arquitectura candidata mediante los casos de uso de mayor riesgo
arquitectónico (CU-02 para la reserva atómica de repuestos sobre stock
libre y CU-04 para la liquidación transaccional e idempotencia de
confirmaciones).

1.  Modelo de requisitos: narrativas

    **CU-01 Registrar orden de servicio**

    **Actor:** Recepcionista. **Precondición:** sesión iniciada y al
    menos un Técnico disponible.

    **Curso básico**

<!-- -->

1.  El Recepcionista abre la pantalla de recepción (GUI-01), ingresa el
    DNI del cliente (8 dígitos) y presiona "Buscar cliente" (CU-05).

2.  El sistema recupera los datos del cliente (nombres, apellidos y
    teléfono) y carga en el selector sus equipos previamente
    registrados.

3.  El Recepcionista selecciona un equipo existente o ingresa los datos
    de uno nuevo (tipo, marca, modelo y número de serie), marca los
    accesorios dejados y describe el estado físico al ingreso.

4.  El Recepcionista registra la falla reportada, selecciona un Técnico
    disponible de la lista, verifica el costo de revisión inicial y
    presiona "Generar orden de servicio".

5.  El sistema valida los campos obligatorios y verifica que el número
    de serie no tenga otra orden activa en el taller.

6.  El sistema registra la Orden de servicio en estado RECEPCIONADO,
    incrementa en 1 la cola del Técnico asignado y muestra el código de
    orden generado listo para imprimir

> **Cursos alternos**

- **2a. El DNI no existe en el sistema (CU-06):** el sistema habilita
  "Registrar nuevo cliente". El Recepcionista abre el modal (GUI-02),
  ingresa DNI, nombres, apellidos, teléfono y correo opcional, y
  presiona "Guardar cliente". El sistema registra al cliente y retorna
  al paso 3 con los datos cargados en GUI-01.

- **2b. DNI ya registrado en modal (CU-06):** si en GUI-02 se intenta
  guardar un DNI existente, el sistema avisa "El DNI ya está registrado"
  y carga el cliente existente sin duplicarlo.

- **5a. El equipo ya tiene una orden activa:** si el número de serie
  posee una orden con estado distinto de ENTREGADO, el sistema bloquea
  el registro y muestra la alerta E01 en GUI-01: "Este número de serie
  ya posee la Orden activa N.° \[X\] en laboratorio".

- **6a. Reintento de confirmación:** si la solicitud se repite con el
  mismo identificador de operación (ID OP), el sistema devuelve la orden
  ya creada sin duplicar el registro ni incrementar nuevamente la cola
  del técnico.

> **CU-02 Emitir diagnóstico y presupuesto**
>
> **Actor**: Técnico de laboratorio. **Precondición**: sesión iniciada y
> Orden de servicio asignada al técnico en estado RECEPCIONADO
>
> Curso básico

1.  El Técnico selecciona una orden pendiente de su bandeja de
    laboratorio y abre la consola de diagnóstico (GUI-03).

2.  El sistema muestra la cabecera de la orden (número, fecha de
    ingreso, equipo, serie y falla reportada).

3.  El Técnico redacta la evaluación técnica en el informe de
    laboratorio e ingresa el costo de mano de obra.

4.  El Técnico ingresa el código SKU o nombre del componente en el
    buscador, indica la cantidad y presiona "Buscar" (CU-07).

5.  El sistema lista los repuestos cuyo stock libre (descontando
    reservas de otras órdenes) es mayor a cero, mostrando SKU, nombre,
    unidades libres y precio unitario.

6.  El Técnico presiona "Añadir al presupuesto" sobre los repuestos
    requeridos.

7.  El sistema agrega cada ítem al detalle, calcula el subtotal de
    repuestos y actualiza el monto total del presupuesto (mano de obra +
    repuestos).

8.  El Técnico presiona "Emitir diagnóstico y presupuesto".

9.  El sistema ejecuta una transacción atómica (todo o nada): bloquea y
    reserva las unidades requeridas sobre el stock libre, guarda el
    Diagnóstico con su detalle de repuestos, cambia el estado de la
    orden a PRESUPUESTADO y muestra la confirmación.

> **Cursos alternos**

- **6a. Cantidad superior al stock libre:** el sistema impide añadir el
  repuesto y alerta la cantidad máxima disponible en almacén.

- **6b. Reparación de software o mantenimiento sin repuestos:** el
  Técnico omite los pasos 4 a 7; el sistema calcula el presupuesto
  únicamente con el costo de mano de obra y guarda el diagnóstico con
  cero repuestos reservados.

- **9a. Conflicto de concurrencia por stock agotado:** si otro técnico
  reservó la última unidad libre de algún ítem mientras se armaba el
  presupuesto, el sistema aborta la transacción completa (no reserva
  ningún repuesto), mantiene la orden en RECEPCIONADO y muestra la
  alerta E02 en GUI-03 para revisar el presupuesto.

- **9b. Reintento de confirmación:** un envío repetido con el mismo ID
  OP no vuelve a descontar el stock libre ni duplica el diagnóstico.

> **CU-03 Registrar decisión de presupuesto**
>
> **Actor**: Recepcionista. **Precondición**: Orden de servicio en
> estado PRESUPUESTADO
>
> **Curso básico**

1.  El Recepcionista abre la pantalla de decisión de presupuesto
    (GUI-04), ingresa el número de orden y presiona "Buscar".

2.  El sistema verifica que la orden esté en estado PRESUPUESTADO y
    muestra el resumen de repuestos reservados, mano de obra y monto
    total.

3.  El Recepcionista selecciona la decisión del cliente ("Aprobado"),
    elige el canal de comunicación (llamada telefónica, WhatsApp o
    presencial), verifica la fecha y hora, redacta la evidencia textual
    de la confirmación y presiona "Registrar decisión".

4.  El sistema valida los campos obligatorios, registra la aprobación
    manteniendo las reservas de repuestos activas y cambia el estado de
    la orden a APROBADO, habilitándola en la bandeja del Técnico.

> **Cursos alternos**

- **2a. Orden no está en estado Presupuestado:** el sistema no permite
  cargar la orden para decisión e informa su estado actual.

- **3a. El cliente rechaza el presupuesto:** el Recepcionista marca
  "Rechazado", registra el canal y la evidencia textual, y confirma. El
  sistema libera inmediatamente todas las reservas de repuestos hacia el
  stock libre y cambia el estado de la orden a RECHAZADO para devolución
  del equipo (aplicando la regla de cobro de revisión según RN-11).

- **4a. Reintento de confirmación:** repetir el envío con el mismo ID OP
  no duplica el registro de decisión ni libera dos veces el stock.

> **CU-08 Finalizar reparación**
>
> **Actor:** Técnico de laboratorio. **Precondición:** Orden de servicio
> asignada al técnico en estado
>
> **Curso básico**

1.  El Técnico selecciona la orden aprobada en su bandeja y abre la
    pantalla de finalización (GUI-05).

2.  El sistema muestra los datos de la orden, la fecha de aprobación y
    la lista de repuestos reservados que se consumirán.

3.  El Técnico redacta el detalle del trabajo realizado en el
    laboratorio.

4.  El Técnico marca la casilla "Prueba conforme" y describe el
    resultado de la prueba de funcionamiento.

5.  El Técnico presiona "Finalizar reparación".

6.  El sistema consume definitivamente del inventario los repuestos
    reservados, registra el cierre técnico y cambia el estado de la
    orden a LISTO para su cobro y entrega en recepción.

> **Cursos alternos**

- **4a. Prueba de funcionamiento no conforme o sin marcar:** el sistema
  mantiene deshabilitado el botón "Finalizar reparación" hasta que se
  verifique y documente la conformidad de la prueba (RN-07).

- **6a. Reintento de confirmación:** repetir la confirmación con el
  mismo ID OP no vuelve a descontar los repuestos consumidos.

> **CU-04 Liquidar orden y entregar equipo**
>
> **Actor:** Recepcionista. **Precondición:** Orden de servicio en
> estado LISTO
>
> **Curso básico**

1.  El Recepcionista abre la pantalla de cobro y entrega (GUI-06),
    ingresa el número de orden y presiona "Buscar".

2.  El sistema muestra los datos del cliente, el equipo con los
    accesorios registrados al ingreso y el cuadro de liquidación
    (subtotal de repuestos, mano de obra y total a cobrar).

3.  El Recepcionista selecciona el método de pago (efectivo, tarjeta o
    transferencia), verifica el monto recibido (igual al total), marca
    la casilla de conformidad de entrega del equipo con sus accesorios y
    presiona "Cobrar y entregar".

4.  El sistema ejecuta en una sola transacción: registra el pago único,
    emite el comprobante de pago interno (CP-AAAA-NNNN) y cambia el
    estado de la orden a ENTREGADO, liberando al equipo para futuras
    órdenes.

> **Cursos alternos**

- **1a. La orden no está en estado Listo:** el sistema impide iniciar la
  liquidación porque la reparación aún no ha sido finalizada con prueba
  conforme.

- **3a. Monto incompleto o sin conformidad de entrega:** el sistema
  rechaza pagos parciales (RN-08) y exige marcar la casilla de
  conformidad antes de confirmar.

- **4a. Reintento de confirmación (idempotencia):** si ocurre un doble
  clic o reintento de red con el mismo ID OP, el sistema retorna el
  comprobante interno ya generado sin duplicar el cobro ni el
  comprobante.

  1.  Prototipos de interfaz

  -------------------------------------------- ------------------------ ----------------------------
  Pantalla                                     Actor                    Caso de uso
  GUI-01 Recepción y orden de servicio         Recepcionista            CU-01, CU-05
  GUI-02 Modal de registro de cliente          Recepcionista            CU-06 (extensión de CU-01)
  Alerta en GUI-01: Serie con orden activa     Recepcionista            CU-01 (5a)
  GUI-03 Consola de diagnóstico y cotización   Técnico de laboratorio   CU-02, CU-07
  Alerta en GUI-03: Conflicto de stock libre   Técnico de laboratorio   CU-02 (9a)
  GUI-04 Decisión de presupuesto               Recepcionista            CU-03
  GUI-05 Finalizar reparación                  Técnico de laboratorio   CU-08
  GUI-06 Cobro y entrega                       Recepcionista            CU-04
  -------------------------------------------- ------------------------ ----------------------------

> *Nota.* Las pantallas GUI-01 a GUI-06 corresponden a los prototipos
> refinados de ByteTrack v2.0, que incorporan el indicador de flujo de
> estados y el token de idempotencia (ID OP) en el pie de cada operación
> transaccional. Elaboración propia (2026).

2.  Modelo de análisis: robustez

3.  Modelo de dominio refinado

4.  Arquitectura del sistema

5.  Diseño de los casos de uso arquitectónicos

El diseño de los casos de uso arquitectónicos de ByteTrack se concentra
en CU-02, Emitir diagnóstico y presupuesto, y CU-04, Liquidar orden y
entregar equipo. Estos casos permiten evaluar los riesgos principales
del sistema: la reserva concurrente de repuestos y la duplicación de
operaciones por reintentos.

El diseño sigue la arquitectura candidata de tres capas: interfaz web,
API REST desarrollada con FastAPI y persistencia en PostgreSQL. Dentro
de la API se proponen servicios de aplicación que coordinan las reglas
del negocio, los repositorios y las transacciones.

Las interfaces presentan información y recogen datos; los servicios
coordinan las operaciones; las entidades representan el negocio; y los
repositorios permiten consultar y persistir los datos. La confirmación o
reversión de los cambios se administra mediante una unidad de trabajo
que utiliza una misma transacción.

3.6.1. CU-02 Emitir diagnóstico y presupuesto

  ----------------------- -----------------------------------------------------------------------------------
  **Elemento**            **Diseño**
  Actor                   Técnico de laboratorio.
  Interfaz                GUI-03 Consola de diagnóstico y cotización.
  Precondición            Sesión válida, orden asignada al técnico y estado RECEPCIONADO.
  Servicio responsable    ServicioDiagnostico.
  Entidades principales   OrdenServicio, Diagnostico, DetalleRepuesto y Repuesto.
  Persistencia            RepositorioOrden, RepositorioDiagnostico y RepositorioRepuesto.
  Resultado               Diagnóstico y detalle registrados, repuestos reservados y orden en PRESUPUESTADO.
  Reglas principales      RN-03, RN-04 y RN-10.
  ----------------------- -----------------------------------------------------------------------------------

> **Desarrollo de la operación**

1.  El técnico abre una orden asignada en GUI-03 y registra el informe
    técnico y el costo de mano de obra.

2.  Mediante CU-07 consulta los repuestos y su stock libre. Esta
    consulta es informativa: la disponibilidad se vuelve a verificar al
    confirmar.

3.  Selecciona los repuestos y las cantidades necesarias. El servidor
    calcula los importes utilizando los precios registrados, sin confiar
    únicamente en los totales enviados desde la interfaz.

4.  Al confirmar, la solicitud incluye un identificador de operación, ID
    OP.

5.  El sistema valida la identidad y autorización del técnico. Si el ID
    OP corresponde a una operación ya confirmada con los mismos datos,
    devuelve el resultado anterior.

6.  Para una operación nueva, inicia una transacción, bloquea la orden y
    comprueba nuevamente que continúe en RECEPCIONADO.

7.  Bloquea los repuestos involucrados en un orden consistente por SKU y
    verifica que todos cuenten con stock libre suficiente.

8.  Si existe disponibilidad, incrementa las cantidades reservadas,
    registra el diagnóstico y sus detalles y cambia la orden a
    PRESUPUESTADO.

9.  Guarda el resultado asociado al ID OP y confirma la transacción.

> Cuando no se requieren repuestos, el diagnóstico se registra con una
> lista de detalles vacía y el presupuesto corresponde únicamente a la
> mano de obra.
>
> **Tratamiento de errores**
>
> Si algún repuesto no tiene disponibilidad suficiente, se revierte toda
> la operación. La orden permanece en RECEPCIONADO y GUI-03 muestra la
> alerta E02. No se conservan reservas parciales ni un diagnóstico
> incompleto.
>
> El stock libre se determina mediante:
>
> **Stock libre = stock disponible físico − stock reservado**
>
> En esta propuesta, stockDisponible conserva el nombre del modelo
> inicial y representa las unidades físicas todavía no consumidas.
> stockReservado representa la parte comprometida con órdenes.
>
> **3.6.2. CU-04 Liquidar orden y entregar equipo**
>
> El Recepcionista utiliza **GUI-06** para registrar el método de pago,
> el importe y la conformidad de entrega. ServicioLiquidacion verifica
> que la orden esté en **LISTO**, que el pago corresponda al total y que
> no exista un comprobante previo.
>
> En una sola transacción, el sistema registra el pago mediante
> ComprobantePago, genera el comprobante interno **CP-AAAA-NNNN** y
> cambia la orden a **ENTREGADO**. Si ocurre un error, todos los cambios
> se revierten.
>
> **Reglas relacionadas:** RN-08, RN-09 y RN-10.
>
> **Controles compartidos**
>
> Ambas operaciones validan los permisos en el servidor y utilizan un
> **ID OP** para evitar duplicaciones. Si una solicitud confirmada se
> repite con el mismo identificador y datos, se devuelve el resultado
> anterior; si sus datos cambian, se rechaza. Los repositorios
> involucrados comparten una misma transacción.

1.  Pruebas de concepto, hito LCA

    Las pruebas de concepto verifican los mecanismos de mayor riesgo
    antes de la Construcción. E1 se concentra en la reserva atómica de
    repuestos; E2, en la liquidación transaccional y la idempotencia.

    Para su ejecución se requiere una API de prueba, PostgreSQL,
    usuarios con los roles correspondientes y datos controlados de
    órdenes y repuestos. Las solicitudes concurrentes deben utilizar
    conexiones independientes para reproducir operaciones simultáneas
    reales.

    3.7.1. Prueba de concepto de reserva atómica --- E1

    **Objetivo:** verificar que las reservas no excedan las existencias
    y que el presupuesto se confirme completamente o no produzca
    cambios.

    **Datos de prueba:** dos órdenes en RECEPCIONADO, asignadas a
    técnicos distintos, y un repuesto con una unidad física disponible y
    ninguna reservada.

  --------------------------------------------------------------------------- -------------------------------------------------------------------------
  **Escenario**                                                               **Resultado esperado**
  Dos técnicos reservan simultáneamente la última unidad.                     Solo una reserva se confirma; la otra orden permanece en RECEPCIONADO.
  Un presupuesto requiere varios repuestos y uno no tiene stock suficiente.   No se reserva ninguno ni se guarda el diagnóstico.
  Ocurre un fallo antes de confirmar.                                         Se revierten todas las modificaciones.
  Se repite una solicitud con el mismo ID OP.                                 No se duplican el diagnóstico ni las reservas.
  Se emite un diagnóstico sin repuestos.                                      El total corresponde a la mano de obra y la orden pasa a PRESUPUESTADO.
  --------------------------------------------------------------------------- -------------------------------------------------------------------------

> **3.7.2. Liquidación e idempotencia --- E2**
>
> **Objetivo:** comprobar que el pago, el comprobante y la entrega se
> confirmen conjuntamente, sin duplicaciones.

  ------------------------------------------------------------------------------------ -------------------------------------------------------
  **Escenario**                                                                        **Resultado esperado**
  Se registra el pago total con conformidad de entrega.                                Se genera un comprobante y la orden pasa a ENTREGADO.
  Se repite la solicitud, incluso después de perder la respuesta.                      Se recupera el comprobante existente.
  Se intenta liquidar simultáneamente la misma orden con identificadores diferentes.   Solo una liquidación se confirma.
  Ocurre un fallo durante la transacción.                                              Ocurre un fallo durante la transacción.
  El importe es incorrecto o falta conformidad.                                        Se rechaza la operación sin modificar los datos.
  Se reutiliza un ID OP con datos distintos.                                           Se rechaza la solicitud.
  ------------------------------------------------------------------------------------ -------------------------------------------------------

> También se verificará que un técnico no acceda a órdenes ajenas, que
> las reglas se apliquen directamente en la API y que se cumpla **p95 ≤
> 1 segundo con cinco sesiones concurrentes**, documentando las
> condiciones de la prueba.
>
> Las evidencias incluirán solicitudes, respuestas y consultas a la base
> de datos antes y después de cada escenario. **Las pruebas están
> diseñadas, pero su ejecución y resultados permanecen pendientes.**
>
> **3.7.3. Hito LCA --- Arquitectura del Ciclo de Vida**
>
> El hito LCA permitirá iniciar Construcción cuando se verifique lo
> siguiente:

- Diseño de CU-02 y CU-04 consistente con las narrativas.

- Modelo de dominio y arquitectura completos y compatibles.

- Pruebas satisfactorias de reserva atómica y liquidación idempotente.

- Validaciones de seguridad y rendimiento documentadas.

- Plan de iteraciones C1--C4 y riesgos pendientes actualizados.

4.  Fase de construcción

    Durante la fase de Construcción se implementarán progresivamente los
    casos de uso de ByteTrack. Cada iteración incluirá ajuste del
    modelo, desarrollo, pruebas, control de versiones y revisión de una
    versión funcional.

    La construcción incorporará los mecanismos validados durante
    Elaboración y conservará la trazabilidad entre reglas de negocio,
    clases, operaciones y pruebas.

4.1. Plan de iteraciones

Se mantienen las cuatro iteraciones de dos semanas establecidas en
Inicio.

  ----------- --------- ------------------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  Iteración   Semanas   Alcance                                                                                    Entregable y aceptación
  C1          7--8      CU-05 Buscar cliente, CU-06 Registrar nuevo cliente y CU-01 Registrar orden de servicio.   Recepción funcional mediante GUI-01 y GUI-02. Valida DNI, serie, orden activa y técnico disponible. Los reintentos no duplican órdenes ni incrementan nuevamente la cola.
  C2          9--10     CU-07 Consultar stock y CU-02 Emitir diagnóstico y presupuesto.                            GUI-03 con búsqueda, cálculo y reserva atómica. Admite diagnósticos sin repuestos y controla conflictos de stock e idempotencia.
  C3          11--12    CU-03 Registrar decisión y CU-08 Finalizar reparación.                                     GUI-04 y GUI-05. Registra canal, fecha y evidencia; mantiene o libera reservas según la decisión; consume repuestos solo al finalizar con prueba conforme.
  C4          13--14    CU-04 Liquidar orden y entregar equipo e integración completa.                             GUI-06 y flujo integrado. Solo permite pago total de órdenes LISTO, exige conformidad y evita duplicar comprobantes. Preparación para evaluar IOC.
  ----------- --------- ------------------------------------------------------------------------------------------ ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

> **Dependencias entre iteraciones**

C2 utiliza las órdenes registradas en C1 e incorpora el mecanismo de
reserva probado en E1. C3 utiliza los presupuestos de C2. C4 utiliza las
órdenes finalizadas en C3 y el mecanismo de liquidación probado en E2.

Al cierre de cada iteración se revisarán los criterios de aceptación,
los defectos pendientes y las pruebas de regresión de las funciones ya
implementadas.

> **Decisiones pendientes que afectan la construcción**

La narrativa de CU-08 deja incompleto el estado de su precondición. Para
este diseño se utiliza **APROBADO**, porque coincide con su primer paso
y con el resultado de CU-03.

La ruta de rechazo requiere una definición adicional: CU-03 deja la
orden en RECHAZADO, mientras que CU-04 exige LISTO. Debe acordarse cómo
se autoriza la devolución de un equipo no reparado y cómo se aplica
RN-11. **No se incorpora una transición automática de RECHAZADO a LISTO
ni se fija el cobro de S/ 40 como regla aprobada.** Esta decisión debe
resolverse antes de implementar esa ruta en C3 y su liquidación en C4.

4.2. Diagramas de clases

Se presentan dos vistas complementarias:

- **Diagrama de entidades:** conserva las ocho clases de negocio
  iniciales y añade los atributos y operaciones necesarios para las
  narrativas actualizadas.

- **Diagrama de diseño técnico:** muestra cómo las interfaces,
  servicios, repositorios y controles transaccionales colaboran para
  ejecutar los casos de uso.

Las clases técnicas son elementos de diseño propuestos y deberán
incorporarse de forma consistente a la arquitectura del apartado 3.5.

**4.2.1. Diagrama de clases de las entidades del negocio**

Los accesorios y el estado físico se registran en OrdenServicio, porque
pueden variar en cada ingreso del mismo equipo. El precio cotizado se
conserva en DetalleRepuesto para que un cambio posterior de precio no
modifique un presupuesto emitido.

aprobadoPorCliente admite un valor nulo mientras no exista decisión. Los
campos de decisión y cierre técnico permanecen sin valor hasta ejecutar
sus respectivos casos de uso.

***Figura 3: Diagrama de clases de las entidades del negocio***

![](docs/aup/img/media/image4.png){width="7.703125546806649in"
height="6.010416666666667in"}

> **4.2.2. Diagrama de clases del diseño técnico**

Esta vista organiza las responsabilidades de los ocho casos de uso. Las
pantallas representan la interfaz web; los controladores representan los
puntos de entrada de la API.

OperacionIdempotente es un registro técnico adicional. UnidadTrabajo
delimita las transacciones y permite que todos los repositorios
involucrados compartan una misma conexión transaccional.

![](docs/aup/img/media/image6.png){width="7.192708880139983in"
height="1.9073009623797026in"}![](docs/aup/img/media/image1.png){width="7.838542213473316in"
height="4.40625in"}

![](docs/aup/img/media/image5.png){width="7.661458880139983in"
height="3.6770833333333335in"}
