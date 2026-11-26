"""Servicios del flujo completo de taller: seguimiento, CU-07, CU-02, CU-03, CU-08 y CU-04.

Todas las operaciones de escritura usan ``BEGIN IMMEDIATE`` para garantizar transacciones
atómicas todo-o-nada (RNF-01) e idempotencia por ``id_op`` (RN-10, RNF-04).
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math

from sqlalchemy.orm import Session

from app.config import ROL_TECNICO
from app.database import iniciar_escritura
from app.errors import (
    ConformidadRequeridaError,
    EstadoOrdenInvalido,
    IdOpConflicto,
    MontoIncompletoError,
    OrdenNoAsignada,
    OrdenNoEncontrada,
    PruebaNoConformeError,
    RepuestoNoEncontrado,
    StockInsuficienteError,
)
from app.models.entities import (
    ESTADO_APROBADO,
    ESTADO_ENTREGADO,
    ESTADO_LISTO,
    ESTADO_PRESUPUESTADO,
    ESTADO_RECEPCIONADO,
    ESTADO_RECHAZADO,
    RESERVA_ACTIVA,
    RESERVA_CONSUMIDA,
    RESERVA_LIBERADA,
    DetalleRepuesto,
    Diagnostico,
    OrdenServicio,
    Usuario,
)
from app.models.schemas import (
    BusquedaClienteOut,
    ClienteOut,
    ComprobantePagoOut,
    DecisionIn,
    DetalleRepuestoOut,
    DiagnosticoIn,
    DiagnosticoOut,
    EmitirDiagnosticoOut,
    EquipoOut,
    FinalizarReparacionIn,
    FinalizarReparacionOut,
    LiquidarOrdenIn,
    LiquidarOrdenOut,
    OrdenDetalleOut,
    PaginaClientesOut,
    PaginaOrdenesOut,
    PaginaRepuestosOut,
    RegistrarDecisionOut,
    RepuestoOut,
    ResumenTallerOut,
    TecnicoCargaOut,
    TecnicoResumenOut,
)
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.operacion_repository import OperacionRepository
from app.repositories.orden_repository import OrdenRepository
from app.repositories.repuesto_repository import RepuestoRepository
from app.repositories.tecnico_repository import TecnicoRepository


def _huella(operacion: str, codigo: str, datos) -> str:
    canonico = json.dumps(
        {"op": operacion, "codigo": codigo, "datos": datos.model_dump(mode="json", exclude={"id_op"})},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def _a_orden_detalle(orden: OrdenServicio) -> OrdenDetalleOut:
    diagnostico_out = None
    if orden.diagnostico is not None:
        diagnostico_out = DiagnosticoOut(
            informe_tecnico=orden.diagnostico.informe_tecnico,
            costo_mano_obra=orden.diagnostico.costo_mano_obra,
            subtotal_repuestos=orden.diagnostico.subtotal_repuestos,
            total_presupuesto=orden.diagnostico.total_presupuesto,
            fecha_emision=orden.diagnostico.fecha_emision,
            detalles=[
                DetalleRepuestoOut(
                    repuesto_id=d.repuesto_id,
                    sku=d.repuesto.sku,
                    nombre=d.repuesto.nombre,
                    cantidad=d.cantidad,
                    precio_cotizado=d.precio_cotizado,
                    subtotal=d.subtotal,
                    estado_reserva=d.estado_reserva,
                )
                for d in orden.diagnostico.detalles
            ],
        )

    comprobante_out = (
        ComprobantePagoOut.model_validate(orden.comprobante)
        if orden.comprobante is not None
        else None
    )

    return OrdenDetalleOut(
        codigo=orden.codigo,
        estado=orden.estado,
        fecha_ingreso=orden.fecha_ingreso,
        cliente=ClienteOut.model_validate(orden.equipo.cliente),
        equipo=EquipoOut.model_validate(orden.equipo),
        tecnico=TecnicoResumenOut.model_validate(orden.tecnico),
        accesorios=orden.accesorios,
        estado_fisico=orden.estado_fisico,
        falla_reportada=orden.falla_reportada,
        costo_revision=orden.costo_revision,
        diagnostico=diagnostico_out,
        decision_canal=orden.decision_canal,
        decision_fecha=orden.decision_fecha,
        decision_evidencia=orden.decision_evidencia,
        trabajo_realizado=orden.trabajo_realizado,
        prueba_conforme=orden.prueba_conforme,
        resultado_prueba=orden.resultado_prueba,
        comprobante=comprobante_out,
    )


def _verificar_acceso_tecnico(usuario: Usuario, orden: OrdenServicio) -> None:
    """RN-03: el técnico solo accede a sus órdenes asignadas."""
    if usuario.rol == ROL_TECNICO and usuario.tecnico_id is not None:
        if orden.tecnico_id != usuario.tecnico_id:
            raise OrdenNoAsignada(orden.codigo)


# ---- Seguimiento y Resumen del Taller ------------------------------------------------


def listar_ordenes(
    sesion: Session,
    usuario: Usuario,
    *,
    estado: str | None = None,
    q: str | None = None,
    page: int = 1,
    limit: int = 6,
) -> PaginaOrdenesOut:
    tecnico_id = usuario.tecnico_id if usuario.rol == ROL_TECNICO else None
    items, total = OrdenRepository(sesion).listar_paginado(
        estado=estado, q=q, tecnico_id=tecnico_id, page=page, limit=limit
    )
    total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1
    return PaginaOrdenesOut(
        items=[_a_orden_detalle(o) for o in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


def obtener_orden(sesion: Session, usuario: Usuario, codigo: str) -> OrdenDetalleOut:
    orden = OrdenRepository(sesion).obtener_por_codigo(codigo)
    if orden is None:
        raise OrdenNoEncontrada(codigo)
    _verificar_acceso_tecnico(usuario, orden)
    return _a_orden_detalle(orden)


def resumen_taller(sesion: Session) -> ResumenTallerOut:
    por_estado = OrdenRepository(sesion).resumen_estados()
    tecnicos_disponibles = len(TecnicoRepository(sesion).listar_disponibles())
    repuestos_stock_bajo = RepuestoRepository(sesion).contar_stock_bajo()
    return ResumenTallerOut(
        total_ordenes=sum(por_estado.values()),
        por_estado=por_estado,
        tecnicos_disponibles=tecnicos_disponibles,
        repuestos_stock_bajo=repuestos_stock_bajo,
    )


def listar_tecnicos_carga(sesion: Session) -> list[TecnicoCargaOut]:
    return [TecnicoCargaOut.model_validate(t) for t in TecnicoRepository(sesion).listar_todos()]


def listar_clientes(
    sesion: Session, *, q: str | None = None, page: int = 1, limit: int = 6
) -> PaginaClientesOut:
    items, total = ClienteRepository(sesion).listar_paginado(q=q, page=page, limit=limit)
    total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1
    return PaginaClientesOut(
        items=[
            BusquedaClienteOut(
                cliente=ClienteOut.model_validate(c),
                equipos=[EquipoOut.model_validate(e) for e in c.equipos],
            )
            for c in items
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


# ---- CU-07 Consultar stock de repuestos ----------------------------------------------


def consultar_repuestos(
    sesion: Session,
    *,
    q: str | None = None,
    solo_con_stock: bool = True,
    page: int = 1,
    limit: int = 8,
) -> PaginaRepuestosOut:
    items, total = RepuestoRepository(sesion).listar_paginado(
        q=q, solo_con_stock=solo_con_stock, page=page, limit=limit
    )
    total_pages = max(1, math.ceil(total / limit)) if limit > 0 else 1
    return PaginaRepuestosOut(
        items=[
            RepuestoOut(
                id=r.id,
                sku=r.sku,
                nombre=r.nombre,
                stock_disponible=r.stock_disponible,
                stock_reservado=r.stock_reservado,
                stock_libre=r.stock_libre,
                precio_unitario=r.precio_unitario,
            )
            for r in items
        ],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


# ---- CU-02 Emitir diagnóstico y presupuesto (RN-03, RN-04, RN-10, RNF-01) ------------


def emitir_diagnostico(
    sesion: Session, usuario: Usuario, codigo: str, datos: DiagnosticoIn
) -> tuple[EmitirDiagnosticoOut, bool]:
    iniciar_escritura(sesion)
    try:
        operaciones = OperacionRepository(sesion)
        huella = _huella("CU-02", codigo, datos)
        previa = operaciones.obtener(datos.id_op)
        if previa is not None:
            if previa.huella != huella:
                raise IdOpConflicto(datos.id_op)
            guardada = EmitirDiagnosticoOut.model_validate_json(previa.resultado)
            sesion.rollback()
            return guardada.model_copy(update={"reintento": True}), False

        ordenes = OrdenRepository(sesion)
        orden = ordenes.obtener_por_codigo(codigo)
        if orden is None:
            raise OrdenNoEncontrada(codigo)
        _verificar_acceso_tecnico(usuario, orden)
        if orden.estado != ESTADO_RECEPCIONADO:
            raise EstadoOrdenInvalido(codigo, orden.estado, ESTADO_RECEPCIONADO)

        # Agrupar cantidades por repuesto_id para evitar duplicados en el mismo presupuesto.
        cantidades: dict[int, int] = {}
        for item in datos.repuestos:
            cantidades[item.repuesto_id] = cantidades.get(item.repuesto_id, 0) + item.cantidad

        repuestos_repo = RepuestoRepository(sesion)
        repuestos_db = {r.id: r for r in repuestos_repo.obtener_por_ids(list(cantidades.keys()))}

        # Validación atómica todo-o-nada antes de mutar (RN-04, RNF-01).
        for rep_id, cant in cantidades.items():
            repuesto = repuestos_db.get(rep_id)
            if repuesto is None:
                raise RepuestoNoEncontrado(rep_id)
            if repuesto.stock_libre < cant:
                raise StockInsuficienteError(
                    repuesto.sku, repuesto.nombre, cant, repuesto.stock_libre
                )

        subtotal_repuestos = Decimal("0.00")
        detalles: list[DetalleRepuesto] = []
        for rep_id, cant in cantidades.items():
            repuesto = repuestos_db[rep_id]
            repuesto.stock_reservado += cant
            subtotal = (repuesto.precio_unitario * cant).quantize(Decimal("0.01"))
            subtotal_repuestos += subtotal
            detalles.append(
                DetalleRepuesto(
                    repuesto_id=repuesto.id,
                    cantidad=cant,
                    precio_cotizado=repuesto.precio_unitario,
                    subtotal=subtotal,
                    estado_reserva=RESERVA_ACTIVA,
                )
            )

        mano_obra = datos.costo_mano_obra.quantize(Decimal("0.01"))
        total_presupuesto = (mano_obra + subtotal_repuestos).quantize(Decimal("0.01"))

        diagnostico = Diagnostico(
            orden_id=orden.id,
            informe_tecnico=datos.informe_tecnico,
            costo_mano_obra=mano_obra,
            subtotal_repuestos=subtotal_repuestos,
            total_presupuesto=total_presupuesto,
            detalles=detalles,
        )
        sesion.add(diagnostico)
        orden.diagnostico = diagnostico
        orden.estado = ESTADO_PRESUPUESTADO
        sesion.flush()
        sesion.expire(orden, ["diagnostico"])

        orden_actualizada = ordenes.obtener_por_codigo(codigo)
        respuesta = EmitirDiagnosticoOut(orden=_a_orden_detalle(orden_actualizada), reintento=False)
        operaciones.registrar(
            id_op=datos.id_op,
            huella=huella,
            orden_id=orden.id,
            resultado=respuesta.model_dump_json(),
        )
        sesion.commit()
        return respuesta, True
    except Exception:
        sesion.rollback()
        raise


# ---- CU-03 Registrar decisión de presupuesto (RN-05, RN-06, RN-10) -------------------


def registrar_decision(
    sesion: Session, codigo: str, datos: DecisionIn
) -> tuple[RegistrarDecisionOut, bool]:
    iniciar_escritura(sesion)
    try:
        operaciones = OperacionRepository(sesion)
        huella = _huella("CU-03", codigo, datos)
        previa = operaciones.obtener(datos.id_op)
        if previa is not None:
            if previa.huella != huella:
                raise IdOpConflicto(datos.id_op)
            guardada = RegistrarDecisionOut.model_validate_json(previa.resultado)
            sesion.rollback()
            return guardada.model_copy(update={"reintento": True}), False

        ordenes = OrdenRepository(sesion)
        orden = ordenes.obtener_por_codigo(codigo)
        if orden is None:
            raise OrdenNoEncontrada(codigo)
        if orden.estado != ESTADO_PRESUPUESTADO:
            raise EstadoOrdenInvalido(codigo, orden.estado, ESTADO_PRESUPUESTADO)

        orden.decision_canal = datos.canal
        orden.decision_fecha = datetime.now(timezone.utc).isoformat(timespec="seconds")
        orden.decision_evidencia = datos.evidencia

        if datos.decision == ESTADO_APROBADO:
            orden.estado = ESTADO_APROBADO
        else:
            # RN-06: si rechaza, libera de inmediato las reservas hacia el stock libre.
            if orden.diagnostico is not None:
                for detalle in orden.diagnostico.detalles:
                    if detalle.estado_reserva == RESERVA_ACTIVA:
                        detalle.repuesto.stock_reservado -= detalle.cantidad
                        detalle.estado_reserva = RESERVA_LIBERADA
            orden.estado = ESTADO_RECHAZADO

        sesion.flush()
        orden_actualizada = ordenes.obtener_por_codigo(codigo)
        respuesta = RegistrarDecisionOut(orden=_a_orden_detalle(orden_actualizada), reintento=False)
        operaciones.registrar(
            id_op=datos.id_op,
            huella=huella,
            orden_id=orden.id,
            resultado=respuesta.model_dump_json(),
        )
        sesion.commit()
        return respuesta, True
    except Exception:
        sesion.rollback()
        raise


# ---- CU-08 Finalizar reparación (RN-03, RN-07, RN-10) --------------------------------


def finalizar_reparacion(
    sesion: Session, usuario: Usuario, codigo: str, datos: FinalizarReparacionIn
) -> tuple[FinalizarReparacionOut, bool]:
    if not datos.prueba_conforme:
        raise PruebaNoConformeError()

    iniciar_escritura(sesion)
    try:
        operaciones = OperacionRepository(sesion)
        huella = _huella("CU-08", codigo, datos)
        previa = operaciones.obtener(datos.id_op)
        if previa is not None:
            if previa.huella != huella:
                raise IdOpConflicto(datos.id_op)
            guardada = FinalizarReparacionOut.model_validate_json(previa.resultado)
            sesion.rollback()
            return guardada.model_copy(update={"reintento": True}), False

        ordenes = OrdenRepository(sesion)
        orden = ordenes.obtener_por_codigo(codigo)
        if orden is None:
            raise OrdenNoEncontrada(codigo)
        _verificar_acceso_tecnico(usuario, orden)
        if orden.estado != ESTADO_APROBADO:
            raise EstadoOrdenInvalido(codigo, orden.estado, ESTADO_APROBADO)

        # RN-07: consumir definitivamente los repuestos reservados.
        if orden.diagnostico is not None:
            for detalle in orden.diagnostico.detalles:
                if detalle.estado_reserva == RESERVA_ACTIVA:
                    detalle.repuesto.stock_reservado -= detalle.cantidad
                    detalle.repuesto.stock_disponible -= detalle.cantidad
                    detalle.estado_reserva = RESERVA_CONSUMIDA

        orden.trabajo_realizado = datos.trabajo_realizado
        orden.prueba_conforme = True
        orden.resultado_prueba = datos.resultado_prueba
        orden.estado = ESTADO_LISTO
        if orden.tecnico.cola > 0:
            orden.tecnico.cola -= 1

        sesion.flush()
        orden_actualizada = ordenes.obtener_por_codigo(codigo)
        respuesta = FinalizarReparacionOut(
            orden=_a_orden_detalle(orden_actualizada), reintento=False
        )
        operaciones.registrar(
            id_op=datos.id_op,
            huella=huella,
            orden_id=orden.id,
            resultado=respuesta.model_dump_json(),
        )
        sesion.commit()
        return respuesta, True
    except Exception:
        sesion.rollback()
        raise


# ---- CU-04 Liquidar orden y entregar equipo (RN-08, RN-09, RN-10) --------------------


def liquidar_orden(
    sesion: Session, codigo: str, datos: LiquidarOrdenIn
) -> tuple[LiquidarOrdenOut, bool]:
    if not datos.conformidad_entrega:
        raise ConformidadRequeridaError()

    iniciar_escritura(sesion)
    try:
        operaciones = OperacionRepository(sesion)
        huella = _huella("CU-04", codigo, datos)
        previa = operaciones.obtener(datos.id_op)
        if previa is not None:
            if previa.huella != huella:
                raise IdOpConflicto(datos.id_op)
            guardada = LiquidarOrdenOut.model_validate_json(previa.resultado)
            sesion.rollback()
            return guardada.model_copy(update={"reintento": True}), False

        ordenes = OrdenRepository(sesion)
        orden = ordenes.obtener_por_codigo(codigo)
        if orden is None:
            raise OrdenNoEncontrada(codigo)
        if orden.estado not in (ESTADO_LISTO, ESTADO_RECHAZADO):
            raise EstadoOrdenInvalido(codigo, orden.estado, f"{ESTADO_LISTO} o {ESTADO_RECHAZADO}")

        # RN-08 (LISTO: presupuesto total) / RN-11 (RECHAZADO: costo de revisión inicial).
        if orden.estado == ESTADO_RECHAZADO:
            total_esperado = orden.costo_revision.quantize(Decimal("0.01"))
        else:
            total_esperado = (
                orden.diagnostico.total_presupuesto
                if orden.diagnostico is not None
                else orden.costo_revision
            ).quantize(Decimal("0.01"))
        recibido = datos.monto_recibido.quantize(Decimal("0.01"))
        if recibido != total_esperado:
            raise MontoIncompletoError(str(total_esperado), str(recibido))

        comprobante = ordenes.crear_comprobante(
            orden_id=orden.id,
            metodo_pago=datos.metodo_pago,
            monto_total=total_esperado,
            conformidad_entrega=True,
        )
        orden.comprobante = comprobante
        orden.estado = ESTADO_ENTREGADO
        sesion.flush()
        sesion.expire(orden, ["comprobante"])

        orden_actualizada = ordenes.obtener_por_codigo(codigo)
        respuesta = LiquidarOrdenOut(
            orden=_a_orden_detalle(orden_actualizada),
            comprobante=ComprobantePagoOut.model_validate(comprobante),
            reintento=False,
        )
        operaciones.registrar(
            id_op=datos.id_op,
            huella=huella,
            orden_id=orden.id,
            resultado=respuesta.model_dump_json(),
        )
        sesion.commit()
        return respuesta, True
    except Exception:
        sesion.rollback()
        raise
