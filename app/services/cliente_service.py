"""Reglas de negocio de clientes (CU-05, CU-06)."""

import re

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import iniciar_escritura
from app.errors import ClienteNoEncontrado, DniInvalido
from app.models.schemas import (
    BusquedaClienteOut,
    ClienteIn,
    ClienteOut,
    EquipoOut,
    RegistroClienteOut,
)
from app.repositories.cliente_repository import ClienteRepository

_PATRON_DNI = re.compile(r"^[0-9]{8}$")


def validar_dni(dni: str) -> None:
    """RN-01: el cliente se identifica por un DNI de 8 dígitos."""
    if not _PATRON_DNI.fullmatch(dni):
        raise DniInvalido()


def buscar_cliente(sesion: Session, dni: str) -> BusquedaClienteOut:
    """CU-05: busca al cliente por DNI y devuelve sus equipos (RN-01)."""
    validar_dni(dni)  # RN-01
    repositorio = ClienteRepository(sesion)
    cliente = repositorio.obtener_por_dni(dni)
    if cliente is None:
        raise ClienteNoEncontrado(dni)  # CU-01 curso 2a: se habilita CU-06
    equipos = repositorio.equipos_del_cliente(cliente.id)
    return BusquedaClienteOut(
        cliente=ClienteOut.model_validate(cliente),
        equipos=[EquipoOut.model_validate(e) for e in equipos],
    )


AVISO_DNI_REGISTRADO = "El DNI ya está registrado"


def _como_registro(sesion: Session, cliente, ya_registrado: bool) -> RegistroClienteOut:
    equipos = ClienteRepository(sesion).equipos_del_cliente(cliente.id)
    return RegistroClienteOut(
        cliente=ClienteOut.model_validate(cliente),
        equipos=[EquipoOut.model_validate(e) for e in equipos],
        ya_registrado=ya_registrado,
        aviso=AVISO_DNI_REGISTRADO if ya_registrado else None,
    )


def registrar_cliente(sesion: Session, datos: ClienteIn) -> tuple[RegistroClienteOut, bool]:
    """CU-06: registra un cliente nuevo (CU-01 curso 2a).

    Si el DNI ya existe devuelve al cliente existente con el aviso «El DNI ya está
    registrado» sin duplicarlo ni modificarlo (CU-01 curso 2b, RN-01).
    Devuelve ``(respuesta, creado)``.
    """
    validar_dni(datos.dni)  # RN-01
    iniciar_escritura(sesion)  # escritores serializados: el DNI no se duplica
    repositorio = ClienteRepository(sesion)
    try:
        existente = repositorio.obtener_por_dni(datos.dni)
        if existente is not None:  # RN-01: DNI único
            respuesta = _como_registro(sesion, existente, ya_registrado=True)
            sesion.rollback()
            return respuesta, False
        cliente = repositorio.crear(
            dni=datos.dni,
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            telefono=datos.telefono,
            correo=datos.correo,
        )
        sesion.commit()
        return _como_registro(sesion, cliente, ya_registrado=False), True
    except IntegrityError:
        # Respaldo ante una carrera: otra transacción registró el mismo DNI (RN-01).
        sesion.rollback()
        existente = repositorio.obtener_por_dni(datos.dni)
        if existente is None:
            raise
        return _como_registro(sesion, existente, ya_registrado=True), False
    except Exception:
        sesion.rollback()
        raise
