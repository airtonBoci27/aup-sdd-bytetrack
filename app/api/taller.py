"""Endpoints del flujo completo de taller: seguimiento paginado, CU-07, CU-02, CU-03, CU-08 y CU-04."""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.etiquetas import (
    CU01_GUI01,
    CU02_GUI03,
    CU03_GUI04,
    CU04_GUI06,
    CU05_GUI01,
    CU07_GUI03,
    CU08_GUI05,
)
from app.api.seguridad import exigir_recepcionista, exigir_tecnico, usuario_actual
from app.database import get_session
from app.models.entities import Usuario
from app.models.schemas import (
    DecisionIn,
    DiagnosticoIn,
    EmitirDiagnosticoOut,
    ErrorOut,
    FinalizarReparacionIn,
    FinalizarReparacionOut,
    LiquidarOrdenIn,
    LiquidarOrdenOut,
    OrdenDetalleOut,
    PaginaClientesOut,
    PaginaOrdenesOut,
    PaginaRepuestosOut,
    RegistrarDecisionOut,
    ResumenTallerOut,
    TecnicoCargaOut,
)
from app.services import flujo_taller_service

RESPUESTAS_SEGURIDAD = {
    401: {"model": ErrorOut, "description": "Sin sesión activa (RNF-02)"},
    403: {"model": ErrorOut, "description": "Rol sin acceso a esta operación (RNF-02)"},
}

router = APIRouter()


@router.get(
    "/ordenes",
    response_model=PaginaOrdenesOut,
    tags=[CU01_GUI01],
    summary="CU-01 Listar órdenes de servicio (paginado)",
    description=(
        "Trazabilidad de equipos por estado con paginación y filtros. "
        "**RN-03**: un Técnico solo visualiza sus órdenes asignadas. "
        "**RNF-02**: exige sesión activa."
    ),
    responses=RESPUESTAS_SEGURIDAD,
)
def listar_ordenes(
    estado: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=6, ge=1, le=50),
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(get_session),
):
    return flujo_taller_service.listar_ordenes(
        sesion, usuario, estado=estado, q=q, page=page, limit=limit
    )


@router.get(
    "/ordenes/resumen",
    response_model=ResumenTallerOut,
    tags=[CU01_GUI01],
    summary="CU-01 Resumen operativo del taller",
    description="Indicadores de órdenes por estado, técnicos disponibles y alertas de stock. **RNF-02**: exige sesión activa.",
    responses=RESPUESTAS_SEGURIDAD,
)
def resumen_taller(
    _usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(get_session),
):
    return flujo_taller_service.resumen_taller(sesion)


@router.get(
    "/tecnicos/resumen",
    response_model=list[TecnicoCargaOut],
    tags=[CU01_GUI01],
    summary="CU-01 Carga de trabajo de técnicos",
    description="Lista los técnicos del taller con disponibilidad y cola actual (**RN-03**, **RNF-02**).",
    responses=RESPUESTAS_SEGURIDAD,
)
def listar_tecnicos_carga(
    _usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(get_session),
):
    return flujo_taller_service.listar_tecnicos_carga(sesion)


@router.get(
    "/clientes",
    response_model=PaginaClientesOut,
    tags=[CU05_GUI01],
    summary="CU-05 Directorio paginado de clientes y equipos",
    description="Lista clientes registrados con sus equipos asociados (**RN-01**, **RNF-02**: solo Recepcionista).",
    responses=RESPUESTAS_SEGURIDAD,
)
def listar_clientes(
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=6, ge=1, le=50),
    _usuario: Usuario = Depends(exigir_recepcionista),
    sesion: Session = Depends(get_session),
):
    return flujo_taller_service.listar_clientes(sesion, q=q, page=page, limit=limit)


@router.get(
    "/ordenes/{codigo}",
    response_model=OrdenDetalleOut,
    tags=[CU01_GUI01],
    summary="CU-01 Consultar orden de servicio por código",
    description=(
        "Devuelve el detalle completo de una orden (cliente, equipo, diagnóstico, decisión y comprobante). "
        "**RN-03**: el Técnico solo accede a sus órdenes asignadas. **RNF-02**: exige sesión activa."
    ),
    responses={**RESPUESTAS_SEGURIDAD, 404: {"model": ErrorOut}},
)
def obtener_orden(
    codigo: str,
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(get_session),
):
    return flujo_taller_service.obtener_orden(sesion, usuario, codigo)


@router.get(
    "/repuestos",
    response_model=PaginaRepuestosOut,
    tags=[CU07_GUI03],
    summary="CU-07 Consultar stock de repuestos (paginado)",
    description=(
        "CU-07 (GUI-03): lista repuestos con stock libre (`stock_disponible - stock_reservado`) "
        "y búsqueda paginada por SKU o nombre. **RN-04** y **RNF-02**: exige sesión activa."
    ),
    responses=RESPUESTAS_SEGURIDAD,
)
def consultar_repuestos(
    q: str | None = Query(default=None),
    solo_con_stock: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=6, ge=1, le=50),
    _usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(get_session),
):
    return flujo_taller_service.consultar_repuestos(
        sesion, q=q, solo_con_stock=solo_con_stock, page=page, limit=limit
    )


@router.post(
    "/ordenes/{codigo}/diagnostico",
    response_model=EmitirDiagnosticoOut,
    status_code=status.HTTP_201_CREATED,
    tags=[CU02_GUI03],
    summary="CU-02 Emitir diagnóstico y presupuesto",
    description=(
        "CU-02 (GUI-03): reserva de forma atómica (todo o nada) los repuestos requeridos sobre "
        "el stock libre y cambia la orden a PRESUPUESTADO. Reglas: **RN-03**, **RN-04** (alerta E02), "
        "**RN-10** (idempotencia), **RNF-01** y **RNF-02** (solo Técnico)."
    ),
    responses={
        **RESPUESTAS_SEGURIDAD,
        200: {"model": EmitirDiagnosticoOut, "description": "Reintento con mismo ID OP (RN-10)"},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut, "description": "Alerta E02 de stock libre o estado inválido"},
    },
)
def emitir_diagnostico(
    codigo: str,
    datos: DiagnosticoIn,
    respuesta: Response,
    usuario: Usuario = Depends(exigir_tecnico),
    sesion: Session = Depends(get_session),
):
    resultado, creada = flujo_taller_service.emitir_diagnostico(sesion, usuario, codigo, datos)
    if not creada:
        respuesta.status_code = status.HTTP_200_OK
    return resultado


@router.post(
    "/ordenes/{codigo}/decision",
    response_model=RegistrarDecisionOut,
    tags=[CU03_GUI04],
    summary="CU-03 Registrar decisión de presupuesto",
    description=(
        "CU-03 (GUI-04): registra la aprobación (mantiene reservas → APROBADO) o rechazo "
        "(libera reservas inmediatamente → RECHAZADO) con canal, fecha y evidencia textual. "
        "Reglas: **RN-05**, **RN-06**, **RN-10** y **RNF-02** (solo Recepcionista)."
    ),
    responses={**RESPUESTAS_SEGURIDAD, 404: {"model": ErrorOut}, 409: {"model": ErrorOut}},
)
def registrar_decision(
    codigo: str,
    datos: DecisionIn,
    _usuario: Usuario = Depends(exigir_recepcionista),
    sesion: Session = Depends(get_session),
):
    resultado, _creada = flujo_taller_service.registrar_decision(sesion, codigo, datos)
    return resultado


@router.post(
    "/ordenes/{codigo}/finalizar",
    response_model=FinalizarReparacionOut,
    tags=[CU08_GUI05],
    summary="CU-08 Finalizar reparación",
    description=(
        "CU-08 (GUI-05): registra el trabajo realizado y la prueba de funcionamiento conforme, "
        "consume definitivamente los repuestos reservados y pasa la orden a LISTO. "
        "Reglas: **RN-03**, **RN-07**, **RN-10** y **RNF-02** (solo Técnico)."
    ),
    responses={**RESPUESTAS_SEGURIDAD, 404: {"model": ErrorOut}, 409: {"model": ErrorOut}},
)
def finalizar_reparacion(
    codigo: str,
    datos: FinalizarReparacionIn,
    usuario: Usuario = Depends(exigir_tecnico),
    sesion: Session = Depends(get_session),
):
    resultado, _creada = flujo_taller_service.finalizar_reparacion(sesion, usuario, codigo, datos)
    return resultado


@router.post(
    "/ordenes/{codigo}/liquidar",
    response_model=LiquidarOrdenOut,
    status_code=status.HTTP_201_CREATED,
    tags=[CU04_GUI06],
    summary="CU-04 Liquidar orden y entregar equipo",
    description=(
        "CU-04 (GUI-06): registra el pago único total (orden LISTO) o el cobro de revisión por "
        "devolución (orden RECHAZADO, **RN-11**), emite el comprobante interno CP-AAAA-NNNN "
        "y cambia la orden a ENTREGADO en una sola transacción. "
        "Reglas: **RN-08**, **RN-09**, **RN-10**, **RN-11**, **RNF-01** y **RNF-02** (solo Recepcionista)."
    ),
    responses={
        **RESPUESTAS_SEGURIDAD,
        200: {"model": LiquidarOrdenOut, "description": "Reintento con mismo ID OP (RN-10)"},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
    },
)
def liquidar_orden(
    codigo: str,
    datos: LiquidarOrdenIn,
    respuesta: Response,
    _usuario: Usuario = Depends(exigir_recepcionista),
    sesion: Session = Depends(get_session),
):
    resultado, creada = flujo_taller_service.liquidar_orden(sesion, codigo, datos)
    if not creada:
        respuesta.status_code = status.HTTP_200_OK
    return resultado
