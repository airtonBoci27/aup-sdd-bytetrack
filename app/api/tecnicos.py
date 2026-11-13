"""Endpoint de técnicos disponibles (CU-01 paso 4, RN-03)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.etiquetas import CU01_GUI01
from app.api.seguridad import exigir_recepcionista
from app.database import get_session
from app.models.schemas import ErrorOut, TecnicoOut
from app.services import orden_service

router = APIRouter(
    dependencies=[Depends(exigir_recepcionista)],  # RNF-02: sesión activa con rol Recepcionista
    responses={
        401: {"model": ErrorOut, "description": "Sin sesión activa (RNF-02)"},
        403: {"model": ErrorOut, "description": "Rol sin acceso a recepción (RNF-02)"},
    },
)


@router.get(
    "/tecnicos/disponibles",
    response_model=list[TecnicoOut],
    tags=[CU01_GUI01],
    summary="CU-01 Listar técnicos disponibles",
    description=(
        "CU-01 paso 4 (GUI-01): lista los técnicos disponibles para asignar la orden. "
        "**RN-03**: la orden solo se asigna a un técnico disponible. "
        "Cada técnico incluye su `cola` (solo lectura, CU-01 paso 6). "
        "**RNF-02**: exige sesión activa con rol Recepcionista."
    ),
)
def listar_tecnicos_disponibles(sesion: Session = Depends(get_session)):
    return orden_service.listar_tecnicos_disponibles(sesion)
