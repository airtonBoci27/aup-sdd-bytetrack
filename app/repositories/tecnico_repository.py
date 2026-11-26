"""Acceso a datos de técnicos."""

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.entities import Tecnico


class TecnicoRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener(self, tecnico_id: int) -> Tecnico | None:
        return self.sesion.get(Tecnico, tecnico_id)

    def listar_disponibles(self) -> list[Tecnico]:
        return list(
            self.sesion.scalars(
                select(Tecnico).where(Tecnico.disponible.is_(True)).order_by(Tecnico.id)
            )
        )

    def listar_todos(self) -> list[Tecnico]:
        return list(self.sesion.scalars(select(Tecnico).order_by(Tecnico.id)))

    def hay_disponibles(self) -> bool:
        """Verifica con una consulta liviana si existe al menos un técnico disponible (RN-03)."""
        return (
            self.sesion.scalar(
                select(Tecnico.id).where(Tecnico.disponible.is_(True)).limit(1)
            )
            is not None
        )

    def incrementar_cola(self, tecnico_id: int) -> None:
        """Incrementa en 1 la cola del técnico con una actualización atómica (cola = cola + 1)."""
        self.sesion.execute(
            update(Tecnico).where(Tecnico.id == tecnico_id).values(cola=Tecnico.cola + 1)
        )
        self.sesion.expire_all()
