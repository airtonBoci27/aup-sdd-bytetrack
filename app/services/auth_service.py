"""Servicio de acceso por rol (RNF-02; precondición «sesión iniciada» de CU-01).

Las reglas de acceso viven aquí; los endpoints y las dependencias solo delegan (principio IV).
"""

import time

from sqlalchemy.orm import Session

from app import config, security
from app.config import ROL_RECEPCIONISTA
from app.database import iniciar_escritura
from app.errors import CredencialesInvalidas, NoAutenticado, RolNoPermitido
from app.models.entities import Usuario
from app.models.schemas import TokenOut
from app.repositories.usuario_repository import UsuarioRepository


def iniciar_sesion(sesion: Session, nombre_usuario: str, clave: str) -> TokenOut:
    """RNF-02: valida las credenciales y emite el token. Un Técnico válido también obtiene token;
    su rechazo ocurre en las operaciones de recepción."""
    usuario = UsuarioRepository(sesion).obtener_por_nombre(nombre_usuario)
    if usuario is None or not security.verificar_clave(clave, usuario.clave_hash):
        raise CredencialesInvalidas()
    token, _jti, _exp = security.crear_token(
        usuario.nombre_usuario, config.minutos_sesion(), config.clave_jwt()
    )
    return TokenOut(access_token=token, rol=usuario.rol)


def verificar_sesion(sesion: Session, token: str | None) -> Usuario:
    """RNF-02: exige una sesión activa y devuelve el usuario (con su rol leído de la base).

    Token ausente, vencido, con firma inválida, cerrado (``jti`` revocado) o de un usuario que ya no
    existe → ``NoAutenticado``. Termina la transacción de lectura y desvincula el usuario para no
    retener la conexión durante la operación.
    """
    if not token:
        raise NoAutenticado()
    try:
        reclamos = security.decodificar_token(token, config.clave_jwt())
    except security.TokenInvalido:
        raise NoAutenticado() from None
    repositorio = UsuarioRepository(sesion)
    if repositorio.esta_revocado(reclamos["jti"]):
        raise NoAutenticado()
    usuario = repositorio.obtener_por_nombre(reclamos["sub"])
    if usuario is None:
        raise NoAutenticado()
    sesion.expunge(usuario)
    sesion.rollback()
    return usuario


def exigir_recepcionista(usuario: Usuario) -> Usuario:
    """RNF-02: las operaciones de recepción están restringidas al rol Recepcionista."""
    if usuario.rol != ROL_RECEPCIONISTA:
        raise RolNoPermitido()
    return usuario


def cerrar_sesion(sesion: Session, token: str) -> None:
    """RNF-02: invalida la sesión revocando el ``jti`` y purga las ya vencidas."""
    try:
        reclamos = security.decodificar_token(token, config.clave_jwt())
    except security.TokenInvalido:
        raise NoAutenticado() from None
    iniciar_escritura(sesion)  # BEGIN IMMEDIATE, como el resto de las escrituras (research D4 de 001)
    repositorio = UsuarioRepository(sesion)
    repositorio.revocar(reclamos["jti"], int(reclamos["exp"]))
    repositorio.purgar_vencidos(int(time.time()))
    sesion.commit()
