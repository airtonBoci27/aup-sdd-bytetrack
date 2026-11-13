"""Endpoints de acceso: inicio y cierre de sesión (precondición de CU-01; RNF-02)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.etiquetas import CU01_ACCESO
from app.api.seguridad import esquema_oauth2, get_session_seguridad, usuario_actual
from app.models.entities import Usuario
from app.models.schemas import ErrorOut, TokenOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=[CU01_ACCESO])


@router.post(
    "/token",
    response_model=TokenOut,
    summary="CU-01 Iniciar sesión",
    description=(
        "Precondición de CU-01 («sesión iniciada»). **RNF-02**: flujo OAuth2 de contraseña "
        "(`username` y `password` como formulario) que devuelve un JWT. Un usuario con rol "
        "Técnico también obtiene token; su rechazo ocurre en las operaciones de recepción "
        "(403 `ROL_NO_PERMITIDO`). El campo `rol` es informativo para la interfaz."
    ),
    responses={401: {"model": ErrorOut, "description": "Credenciales inválidas (RNF-02)"}},
)
def iniciar_sesion(
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()],
    sesion: Session = Depends(get_session_seguridad),
):
    return auth_service.iniciar_sesion(sesion, formulario.username, formulario.password)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="CU-01 Cerrar sesión",
    description=(
        "Precondición de CU-01. **RNF-02** («sesiones activas»): invalida la sesión actual; con ese "
        "token, las operaciones posteriores responden 401 `NO_AUTENTICADO`. Disponible para "
        "cualquier rol con sesión activa."
    ),
    responses={401: {"model": ErrorOut, "description": "Sin sesión activa (RNF-02)"}},
)
def cerrar_sesion(
    token: str | None = Depends(esquema_oauth2),
    _usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(get_session_seguridad),
):
    auth_service.cerrar_sesion(sesion, token or "")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
