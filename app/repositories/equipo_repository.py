"""Acceso a datos de equipos."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Equipo


class EquipoRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener(self, equipo_id: int) -> Equipo | None:
        return self.sesion.get(Equipo, equipo_id)

    def obtener_por_serie(self, numero_serie: str) -> Equipo | None:
        return self.sesion.scalar(select(Equipo).where(Equipo.numero_serie == numero_serie))

    def crear(
        self, cliente_id: int, tipo: str, marca: str, modelo: str, numero_serie: str
    ) -> Equipo:
        equipo = Equipo(
            cliente_id=cliente_id,
            tipo=tipo,
            marca=marca,
            modelo=modelo,
            numero_serie=numero_serie,
        )
        self.sesion.add(equipo)
        self.sesion.flush()
        return equipo
