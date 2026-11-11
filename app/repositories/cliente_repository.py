"""Acceso a datos de clientes."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Cliente, Equipo


class ClienteRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_dni(self, dni: str) -> Cliente | None:
        return self.sesion.scalar(select(Cliente).where(Cliente.dni == dni))

    def equipos_del_cliente(self, cliente_id: int) -> list[Equipo]:
        return list(
            self.sesion.scalars(
                select(Equipo).where(Equipo.cliente_id == cliente_id).order_by(Equipo.id)
            )
        )

    def crear(
        self,
        *,
        dni: str,
        nombres: str,
        apellidos: str,
        telefono: str,
        correo: str | None,
    ) -> Cliente:
        cliente = Cliente(
            dni=dni, nombres=nombres, apellidos=apellidos, telefono=telefono, correo=correo
        )
        self.sesion.add(cliente)
        self.sesion.flush()
        return cliente
