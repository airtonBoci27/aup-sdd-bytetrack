"""Modelos SQLAlchemy de la iteración C1 (ver specs/001-recepcion-orden-servicio/data-model.md)."""

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.config import ROL_RECEPCIONISTA, ROL_TECNICO  # noqa: F401  (RNF-02)
from app.database import Base

ESTADO_RECEPCIONADO = "RECEPCIONADO"
ESTADO_ENTREGADO = "ENTREGADO"
ESTADOS_ORDEN = (
    "RECEPCIONADO",
    "PRESUPUESTADO",
    "APROBADO",
    "RECHAZADO",
    "LISTO",
    "ENTREGADO",
)


class Dinero(TypeDecorator):
    """Decimal con 2 decimales guardado como texto (SQLite no tiene decimales nativos)."""

    impl = String
    cache_ok = True

    def process_bind_param(self, valor, dialecto):
        if valor is None:
            return None
        return str(Decimal(valor).quantize(Decimal("0.01")))

    def process_result_value(self, valor, dialecto):
        return None if valor is None else Decimal(valor)


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = (
        # RN-01: DNI de 8 dígitos numéricos (equivale a ^[0-9]{8}$; SQLite no tiene regex).
        CheckConstraint(
            "length(dni) = 8 AND dni NOT GLOB '*[^0-9]*'", name="ck_cliente_dni_formato"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    dni: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)  # RN-01
    nombres: Mapped[str] = mapped_column(String, nullable=False)
    apellidos: Mapped[str] = mapped_column(String, nullable=False)
    telefono: Mapped[str] = mapped_column(String, nullable=False)
    correo: Mapped[str | None] = mapped_column(String, nullable=True)

    equipos: Mapped[list["Equipo"]] = relationship(back_populates="cliente")


class Equipo(Base):
    __tablename__ = "equipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), nullable=False)
    tipo: Mapped[str] = mapped_column(String, nullable=False)
    marca: Mapped[str] = mapped_column(String, nullable=False)
    modelo: Mapped[str] = mapped_column(String, nullable=False)
    # RN-01: número de serie único en todo el sistema.
    numero_serie: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    cliente: Mapped[Cliente] = relationship(back_populates="equipos")


class Tecnico(Base):
    __tablename__ = "tecnico"
    __table_args__ = (CheckConstraint("cola >= 0", name="ck_tecnico_cola_no_negativa"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombres: Mapped[str] = mapped_column(String, nullable=False)
    apellidos: Mapped[str] = mapped_column(String, nullable=False)
    disponible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)  # RN-03
    cola: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class OrdenServicio(Base):
    __tablename__ = "orden_servicio"
    __table_args__ = (
        CheckConstraint(
            "estado IN ({})".format(", ".join(f"'{e}'" for e in ESTADOS_ORDEN)),
            name="ck_orden_estado",
        ),
        # RN-02: una sola orden con estado distinto de ENTREGADO por equipo (incluso con concurrencia).
        Index(
            "uq_orden_activa_por_equipo",
            "equipo_id",
            unique=True,
            sqlite_where=text("estado <> 'ENTREGADO'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # OS-AAAA-NNNN (GUI-01)
    equipo_id: Mapped[int] = mapped_column(ForeignKey("equipo.id"), nullable=False)
    tecnico_id: Mapped[int] = mapped_column(ForeignKey("tecnico.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String, nullable=False, default=ESTADO_RECEPCIONADO)
    accesorios: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_fisico: Mapped[str] = mapped_column(Text, nullable=False)
    falla_reportada: Mapped[str] = mapped_column(Text, nullable=False)
    costo_revision: Mapped[Decimal] = mapped_column(Dinero, nullable=False)
    id_op: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # RN-10

    equipo: Mapped[Equipo] = relationship()
    tecnico: Mapped[Tecnico] = relationship()


class OperacionIdempotente(Base):
    """Operación confirmada: ID OP con su huella y su resultado (RN-10, RNF-04)."""

    __tablename__ = "operacion_idempotente"

    id_op: Mapped[str] = mapped_column(String, primary_key=True)
    huella: Mapped[str] = mapped_column(String, nullable=False)  # SHA-256 de la solicitud
    orden_id: Mapped[int] = mapped_column(ForeignKey("orden_servicio.id"), nullable=False)
    resultado: Mapped[str] = mapped_column(Text, nullable=False)  # JSON de la respuesta original


class Usuario(Base):
    """Usuario del sistema con su rol (RNF-02). Solo se carga con ``app.seed``; no se gestiona."""

    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint(
            f"rol IN ('{ROL_RECEPCIONISTA}','{ROL_TECNICO}')", name="ck_usuario_rol"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_usuario: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # Formato scrypt$n$r$p$sal$hash; nunca la contraseña (principio VI).
    clave_hash: Mapped[str] = mapped_column(String, nullable=False)
    rol: Mapped[str] = mapped_column(String, nullable=False)


class TokenRevocado(Base):
    """Sesión cerrada: ``jti`` del token con su expiración (RNF-02, «sesiones activas»)."""

    __tablename__ = "token_revocado"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    # Segundos desde la época, UTC.
    expira_en: Mapped[int] = mapped_column(Integer, nullable=False)
