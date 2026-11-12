
RF-01
Gestionar cliente y equipo
Buscar por DNI único (8 dígitos), registrar datos obligatorios del cliente y asociar múltiples equipos por número de serie único.
CU-01, 05, 06

RF-02
Registrar orden
Guardar falla reportada, estado físico y accesorios. Asignar únicamente a un técnico con disponible = true, fijar costo de revisión e impedir la creación si el equipo ya posee una orden con estadoOrden != "Entregado".
CU-01

RF-03
Emitir diagnóstico
Guardar informe técnico, costo de mano de obra y repuestos cotizados. Validar disponibilidad libre y reservar de forma atómica (todo o nada) todos los repuestos requeridos, cambiando estadoOrden a "Presupuestado".
CU-02, 07

RF-04
Registrar decisión
Guardar aprobación o rechazo con evidencia textual, canal y fecha. Si aprueba, mantiene reservas y cambia estado a "Aprobado"; si rechaza, libera reservas inmediatamente y cambia estado a "Rechazado".
CU-03

RF-05
Cobrar y entregar
Calcular liquidación total en estado "Listo", registrar un pago único, emitir comprobante de pago interno y cambiar estado a "Entregado" en una única transacción.
CU-04

RF-06
Finalizar reparación
Registrar trabajo realizado y prueba de funcionamiento conforme. Consumir definitivamente los repuestos reservados y actualizar el estado a "Listo".
CU-08

RNF-01
Integridad
Las operaciones de reserva, liberación, consumo, registro de decisión y cobro con entrega son estrictamente transaccionales. Ante solicitudes concurrentes sobre la última unidad de stock libre, la reserva es atómica (todo o nada) y previene estados inconsistentes o stock negativo.

RNF-02
Seguridad
Acceso basado en roles y sesiones activas. Las operaciones de recepción, decisión y cobro están restringidas al rol Recepcionista; las de diagnóstico, cotización y finalización al rol Técnico (únicamente sobre sus órdenes asignadas).

RNF-03
Rendimiento propuesto
En una prueba con cinco sesiones concurrentes y 100 intentos de reserva, el percentil 95 de respuesta es como máximo un segundo, medido desde la solicitud hasta la confirmación. Objetivo pendiente de prueba.

RNF-04
Reintentos seguros
Idempotencia en las confirmaciones: la repetición de una solicitud con el mismo identificador de operación no duplica órdenes, reservas, liberaciones, consumos, pagos ni comprobantes.

