"""Acceso a datos de clientes."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

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

    def listar_paginado(
        self, *, q: str | None = None, page: int = 1, limit: int = 6
    ) -> tuple[list[Cliente], int]:
        """Lista clientes con sus equipos precargados y búsqueda por DNI, nombre o teléfono."""
        filtros = []
        if q and q.strip():
            patron = f"%{q.strip()}%"
            filtros.append(
                or_(
                    Cliente.dni.ilike(patron),
                    Cliente.nombres.ilike(patron),
                    Cliente.apellidos.ilike(patron),
                    Cliente.telefono.ilike(patron),
                )
            )
        total = (
            self.sesion.scalar(select(func.count()).select_from(Cliente).where(*filtros)) or 0
        )
        offset = (page - 1) * limit
        items = list(
            self.sesion.scalars(
                select(Cliente)
                .options(selectinload(Cliente.equipos))
                .where(*filtros)
                .order_by(Cliente.apellidos, Cliente.nombres)
                .offset(offset)
                .limit(limit)
            )
        )
        return items, total

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
