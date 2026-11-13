"""Endpoints de clientes: CU-05 Buscar cliente (GUI-01) y CU-06 Registrar nuevo cliente (GUI-02)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Response, status
from sqlalchemy.orm import Session

from app.api.etiquetas import CU05_GUI01, CU06_GUI02
from app.api.seguridad import exigir_recepcionista
from app.database import get_session
from app.models.schemas import (
    PATRON_DNI,
    BusquedaClienteOut,
    ClienteIn,
    ErrorOut,
    RegistroClienteOut,
)
from app.services import cliente_service

router = APIRouter(
    dependencies=[Depends(exigir_recepcionista)],  # RNF-02: sesión activa con rol Recepcionista
    responses={
        401: {"model": ErrorOut, "description": "Sin sesión activa (RNF-02)"},
        403: {"model": ErrorOut, "description": "Rol sin acceso a recepción (RNF-02)"},
    },
)


@router.get(
    "/clientes/{dni}",
    response_model=BusquedaClienteOut,
    tags=[CU05_GUI01],
    summary="CU-05 Buscar cliente por DNI",
    description=(
        "CU-05 (GUI-01): busca un cliente por DNI y devuelve sus datos y los equipos ya "
        "registrados para el selector (CU-01 pasos 1-2). **RN-01**: el DNI son 8 dígitos. "
        "Si el DNI no existe responde 404 con `habilitar_registro` (CU-01 curso 2a). "
        "**RNF-02**: exige sesión activa con rol Recepcionista."
    ),
    responses={404: {"model": ErrorOut}},
)
def buscar_cliente(
    dni: Annotated[str, Path(pattern=PATRON_DNI, description="DNI de 8 dígitos (RN-01)")],
    sesion: Session = Depends(get_session),
):
    return cliente_service.buscar_cliente(sesion, dni)


@router.post(
    "/clientes",
    response_model=RegistroClienteOut,
    status_code=status.HTTP_201_CREATED,
    tags=[CU06_GUI02],
    summary="CU-06 Registrar nuevo cliente",
    description=(
        "CU-06 (GUI-02): registra un cliente con DNI, nombres, apellidos, teléfono y correo "
        "opcional (CU-01 curso 2a). **RN-01**: el DNI es único; si ya está registrado responde "
        "200 con `ya_registrado=true` y el aviso «El DNI ya está registrado», y devuelve al "
        "cliente existente sin duplicarlo (CU-01 curso 2b). "
        "**RNF-02**: exige sesión activa con rol Recepcionista."
    ),
    responses={200: {"model": RegistroClienteOut, "description": "DNI ya registrado (curso 2b)"}},
)
def registrar_cliente(
    datos: ClienteIn, respuesta: Response, sesion: Session = Depends(get_session)
):
    resultado, creado = cliente_service.registrar_cliente(sesion, datos)
    if not creado:
        respuesta.status_code = status.HTTP_200_OK
    return resultado
