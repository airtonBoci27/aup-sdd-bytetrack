"""Acceso a datos de órdenes de servicio."""

from datetime import date
from decimal import Decimal

from sqlalchemy import Integer, cast, desc, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.entities import (
    ESTADO_ENTREGADO,
    ESTADO_RECEPCIONADO,
    ESTADOS_ORDEN,
    Cliente,
    ComprobantePago,
    DetalleRepuesto,
    Diagnostico,
    Equipo,
    OrdenServicio,
)


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
        ultimo_correlativo = self.sesion.scalar(
            select(
                func.max(cast(func.substr(OrdenServicio.codigo, len(prefijo) + 1), Integer))
            ).where(OrdenServicio.codigo.like(f"{prefijo}%"))
        )
        correlativo = (ultimo_correlativo or 0) + 1
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

    def obtener_por_codigo(self, codigo: str) -> OrdenServicio | None:
        return self.sesion.scalar(
            select(OrdenServicio)
            .options(
                selectinload(OrdenServicio.equipo).selectinload(Equipo.cliente),
                selectinload(OrdenServicio.tecnico),
                selectinload(OrdenServicio.diagnostico)
                .selectinload(Diagnostico.detalles)
                .selectinload(DetalleRepuesto.repuesto),
                selectinload(OrdenServicio.comprobante),
            )
            .where(OrdenServicio.codigo == codigo)
        )

    def listar_paginado(
        self,
        *,
        estado: str | None = None,
        q: str | None = None,
        tecnico_id: int | None = None,
        page: int = 1,
        limit: int = 6,
    ) -> tuple[list[OrdenServicio], int]:
        """Lista órdenes paginadas con filtro por estado, texto (código/DNI/serie/cliente) y técnico."""
        consulta_base = (
            select(OrdenServicio)
            .join(OrdenServicio.equipo)
            .join(Equipo.cliente)
        )
        filtros = []
        if estado:
            filtros.append(OrdenServicio.estado == estado)
        if tecnico_id is not None:
            filtros.append(OrdenServicio.tecnico_id == tecnico_id)
        if q and q.strip():
            patron = f"%{q.strip()}%"
            filtros.append(
                or_(
                    OrdenServicio.codigo.ilike(patron),
                    Equipo.numero_serie.ilike(patron),
                    Equipo.marca.ilike(patron),
                    Equipo.modelo.ilike(patron),
                    Cliente.dni.ilike(patron),
                    Cliente.nombres.ilike(patron),
                    Cliente.apellidos.ilike(patron),
                )
            )
        total = (
            self.sesion.scalar(
                select(func.count()).select_from(consulta_base.where(*filtros).subquery())
            )
            or 0
        )
        offset = (page - 1) * limit
        items = list(
            self.sesion.scalars(
                consulta_base.where(*filtros)
                .options(
                    selectinload(OrdenServicio.equipo).selectinload(Equipo.cliente),
                    selectinload(OrdenServicio.tecnico),
                    selectinload(OrdenServicio.diagnostico)
                    .selectinload(Diagnostico.detalles)
                    .selectinload(DetalleRepuesto.repuesto),
                    selectinload(OrdenServicio.comprobante),
                )
                .order_by(desc(OrdenServicio.id))
                .offset(offset)
                .limit(limit)
            )
        )
        return items, total

    def resumen_estados(self) -> dict[str, int]:
        conteos = {estado: 0 for estado in ESTADOS_ORDEN}
        filas = self.sesion.execute(
            select(OrdenServicio.estado, func.count()).group_by(OrdenServicio.estado)
        ).all()
        for estado, cantidad in filas:
            conteos[estado] = int(cantidad)
        return conteos

    def crear_comprobante(
        self,
        *,
        orden_id: int,
        metodo_pago: str,
        monto_total: Decimal,
        conformidad_entrega: bool,
    ) -> ComprobantePago:
        """CU-04 (RN-09): genera el comprobante interno CP-AAAA-NNNN en la misma transacción."""
        prefijo = f"CP-{date.today().year}-"
        ultimo = self.sesion.scalar(
            select(
                func.max(cast(func.substr(ComprobantePago.numero, len(prefijo) + 1), Integer))
            ).where(ComprobantePago.numero.like(f"{prefijo}%"))
        )
        correlativo = (ultimo or 0) + 1
        comprobante = ComprobantePago(
            numero=f"{prefijo}{correlativo:04d}",
            orden_id=orden_id,
            metodo_pago=metodo_pago,
            monto_total=monto_total,
            conformidad_entrega=conformidad_entrega,
        )
        self.sesion.add(comprobante)
        self.sesion.flush()
        return comprobante
