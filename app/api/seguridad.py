"""Dependencias de acceso por rol (RNF-02).

``get_session_seguridad`` entrega una sesión de base de datos **propia e independiente** de la de la
operación (research D7): si se consultara el usuario con la sesión de la solicitud, la transacción ya
estaría abierta con un BEGIN diferido y ``iniciar_escritura`` (BEGIN IMMEDIATE, base de RN-02 y RN-10)
no tendría efecto.
"""

from typing import Iterator

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import obtener_fabrica_sesiones
from app.models.entities import Usuario
from app.services import auth_service

# auto_error=False: el error lo devuelve ErrorDominio en el formato uniforme {codigo, mensaje, detalle}.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def get_session_seguridad() -> Iterator[Session]:
    """Dependencia de FastAPI: sesión breve e independiente para verificar la sesión (RNF-02)."""
    with obtener_fabrica_sesiones()() as sesion:
        yield sesion


def usuario_actual(
    token: str | None = Depends(esquema_oauth2),
    sesion: Session = Depends(get_session_seguridad),
) -> Usuario:
    """RNF-02: exige sesión activa (cualquier rol)."""
    return auth_service.verificar_sesion(sesion, token)


def exigir_recepcionista(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """RNF-02: exige sesión activa con rol Recepcionista (CU-01, CU-03, CU-04, CU-05, CU-06)."""
    return auth_service.exigir_recepcionista(usuario)


def exigir_tecnico(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """RNF-02: exige sesión activa con rol Técnico de laboratorio (CU-02, CU-07, CU-08)."""
    return auth_service.exigir_tecnico(usuario)
