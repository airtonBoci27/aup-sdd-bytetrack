"""Endpoint de técnicos disponibles (CU-01 paso 4, RN-03)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.etiquetas import CU01_GUI01
from app.database import get_session
from app.models.schemas import TecnicoOut
from app.services import orden_service

router = APIRouter()


@router.get(
    "/tecnicos/disponibles",
    response_model=list[TecnicoOut],
    tags=[CU01_GUI01],
    summary="CU-01 Listar técnicos disponibles",
    description=(
        "CU-01 paso 4 (GUI-01): lista los técnicos disponibles para asignar la orden. "
        "**RN-03**: la orden solo se asigna a un técnico disponible."
    ),
)
def listar_tecnicos_disponibles(sesion: Session = Depends(get_session)):
    return orden_service.listar_tecnicos_disponibles(sesion)
