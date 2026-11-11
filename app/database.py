"""Acceso a SQLite con SQLAlchemy: motor, sesión y control de transacciones.

Decisión de diseño (research D4): SQLite no bloquea filas, así que las operaciones de
escritura abren la transacción con ``BEGIN IMMEDIATE`` (escritores serializados). Para que
el driver ``pysqlite`` respete el ``BEGIN`` explícito se desactiva su control automático de
transacciones y se emite el ``BEGIN`` desde el evento ``begin`` del motor.
"""

from functools import lru_cache
from typing import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app import config

OPCION_ESCRITURA = "escritura_inmediata"
BUSY_TIMEOUT_MS = 30_000


class Base(DeclarativeBase):
    """Base declarativa de todos los modelos."""


def crear_motor(ruta_db: str) -> Engine:
    """Crea un motor SQLite con claves foráneas, WAL y transacciones controladas."""
    motor = create_engine(
        f"sqlite:///{ruta_db}",
        connect_args={"check_same_thread": False, "timeout": BUSY_TIMEOUT_MS / 1000},
    )

    @event.listens_for(motor, "connect")
    def _al_conectar(conexion_dbapi, _registro):
        conexion_dbapi.isolation_level = None  # sin BEGIN automático del driver
        cursor = conexion_dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute(f"PRAGMA busy_timeout={BUSY_TIMEOUT_MS}")
        cursor.close()

    @event.listens_for(motor, "begin")
    def _al_comenzar(conexion):
        if conexion.get_execution_options().get(OPCION_ESCRITURA):
            conexion.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            conexion.exec_driver_sql("BEGIN")

    return motor


def crear_fabrica_sesiones(motor: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=motor, expire_on_commit=False)


def iniciar_escritura(sesion: Session) -> None:
    """Abre la transacción de la sesión con ``BEGIN IMMEDIATE``.

    Debe llamarse antes de cualquier consulta de la unidad de trabajo.
    """
    sesion.connection(execution_options={OPCION_ESCRITURA: True})


@lru_cache(maxsize=1)
def obtener_motor() -> Engine:
    return crear_motor(config.ruta_base_datos())


@lru_cache(maxsize=1)
def _fabrica_por_defecto() -> sessionmaker[Session]:
    return crear_fabrica_sesiones(obtener_motor())


def crear_tablas(motor: Engine | None = None) -> None:
    """Crea las tablas si no existen (importa los modelos para registrarlos)."""
    from app.models import entities  # noqa: F401

    Base.metadata.create_all(motor or obtener_motor())


def get_session() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por solicitud; revierte lo no confirmado al cerrar."""
    with _fabrica_por_defecto()() as sesion:
        yield sesion
