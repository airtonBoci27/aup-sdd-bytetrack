"""Acceso a datos de órdenes de servicio."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import ESTADO_ENTREGADO, ESTADO_RECEPCIONADO, OrdenServicio


class OrdenRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_activa_por_equipo(self, equipo_id: int) -> OrdenServicio | None:
        """RN-02: orden del equipo con estado distinto de ENTREGADO (a lo sumo una)."""
        return self.sesion.scalar(
            select(OrdenServicio).where(
                OrdenServicio.equipo_id == equipo_id,
                OrdenServicio.estado != ESTADO_ENTREGADO,
            )
        )

    def crear(
        self,
        *,
        equipo_id: int,
        tecnico_id: int,
        accesorios: str | None,
        estado_fisico: str,
        falla_reportada: str,
        costo_revision: Decimal,
        id_op: str,
    ) -> OrdenServicio:
        """Crea la orden RECEPCIONADO y fija su código ``OS-AAAA-NNNN`` en la misma transacción.

        Formato del prototipo GUI-01 (ejemplo ``OS-2026-0146``): año de la recepción y
        correlativo de órdenes de ese año. Se ejecuta con el bloqueo de escritura tomado
        (BEGIN IMMEDIATE), por lo que el siguiente correlativo no puede usarlo otra transacción.
        """
        prefijo = f"OS-{date.today().year}-"
        correlativo = (
            self.sesion.scalar(
                select(func.count()).select_from(OrdenServicio).where(
                    OrdenServicio.codigo.like(f"{prefijo}%")
                )
            )
            + 1
        )
        orden = OrdenServicio(
            codigo=f"{prefijo}{correlativo:04d}",
            equipo_id=equipo_id,
            tecnico_id=tecnico_id,
            estado=ESTADO_RECEPCIONADO,
            accesorios=accesorios,
            estado_fisico=estado_fisico,
            falla_reportada=falla_reportada,
            costo_revision=costo_revision,
            id_op=id_op,
        )
        self.sesion.add(orden)
        self.sesion.flush()
        return orden
