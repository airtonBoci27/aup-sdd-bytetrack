"""Acceso a datos de repuestos de almacén (CU-02, CU-07; RN-04)."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.entities import Repuesto


class RepuestoRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener(self, repuesto_id: int) -> Repuesto | None:
        return self.sesion.get(Repuesto, repuesto_id)

    def obtener_por_ids(self, ids: list[int]) -> list[Repuesto]:
        if not ids:
            return []
        return list(
            self.sesion.scalars(
                select(Repuesto).where(Repuesto.id.in_(ids)).order_by(Repuesto.sku)
            )
        )

    def listar_paginado(
        self,
        *,
        q: str | None = None,
        solo_con_stock: bool = True,
        page: int = 1,
        limit: int = 8,
    ) -> tuple[list[Repuesto], int]:
        """CU-07: búsqueda paginada por SKU o nombre sobre stock libre."""
        filtros = []
        if solo_con_stock:
            filtros.append((Repuesto.stock_disponible - Repuesto.stock_reservado) > 0)
        if q and q.strip():
            patron = f"%{q.strip()}%"
            filtros.append(or_(Repuesto.sku.ilike(patron), Repuesto.nombre.ilike(patron)))

        total = (
            self.sesion.scalar(select(func.count()).select_from(Repuesto).where(*filtros)) or 0
        )
        offset = (page - 1) * limit
        items = list(
            self.sesion.scalars(
                select(Repuesto)
                .where(*filtros)
                .order_by(Repuesto.sku)
                .offset(offset)
                .limit(limit)
            )
        )
        return items, total

    def contar_stock_bajo(self, umbral: int = 2) -> int:
        return (
            self.sesion.scalar(
                select(func.count())
                .select_from(Repuesto)
                .where((Repuesto.stock_disponible - Repuesto.stock_reservado) <= umbral)
            )
            or 0
        )
