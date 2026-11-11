"""Endpoints de CU-01 Registrar orden de servicio (GUI-01)."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.etiquetas import CU01_GUI01
from app.database import get_session
from app.models.schemas import CostoRevisionOut, CrearOrdenOut, ErrorOut, OrdenIn
from app.services import orden_service

router = APIRouter()


@router.get(
    "/ordenes/costo-revision-inicial",
    response_model=CostoRevisionOut,
    tags=[CU01_GUI01],
    summary="CU-01 Consultar costo de revisión inicial",
    description="CU-01 paso 4 (GUI-01): costo de revisión inicial que el Recepcionista verifica.",
)
def consultar_costo_revision_inicial():
    return CostoRevisionOut(costo_revision=orden_service.costo_revision_inicial())


@router.post(
    "/ordenes",
    response_model=CrearOrdenOut,
    status_code=status.HTTP_201_CREATED,
    tags=[CU01_GUI01],
    summary="CU-01 Registrar orden de servicio",
    description=(
        "CU-01 (GUI-01): registra la orden en estado RECEPCIONADO, la asigna a un técnico "
        "disponible e incrementa en 1 su cola. Reglas: **RN-01** (DNI y número de serie "
        "únicos), **RN-02** (una sola orden activa por equipo; alerta E01), **RN-03** "
        "(solo técnico disponible) y **RN-10** (el mismo `id_op` no duplica órdenes ni "
        "incrementa la cola)."
    ),
    responses={
        200: {"model": CrearOrdenOut, "description": "Reintento con el mismo ID OP (RN-10)"},
        404: {"model": ErrorOut},
        409: {"model": ErrorOut},
    },
)
def registrar_orden(
    datos: OrdenIn, respuesta: Response, sesion: Session = Depends(get_session)
):
    resultado, creada = orden_service.crear_orden(sesion, datos)
    if not creada:
        respuesta.status_code = status.HTTP_200_OK
    return resultado
