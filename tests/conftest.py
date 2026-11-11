"""Fixtures compartidas: base SQLite temporal en archivo y cliente de pruebas.

La base es un archivo (no memoria) para poder abrir conexiones independientes en las
pruebas de concurrencia (RN-02, RN-10).
"""

import pytest
from fastapi.testclient import TestClient

from app.database import (
    Base,
    crear_fabrica_sesiones,
    crear_motor,
    get_session,
)
from app.main import app
from app.models.entities import Cliente, Equipo, OrdenServicio, Tecnico


@pytest.fixture
def motor(tmp_path):
    motor = crear_motor(str(tmp_path / "prueba.db"))
    Base.metadata.create_all(motor)
    yield motor
    motor.dispose()


@pytest.fixture
def fabrica_sesiones(motor):
    """Fábrica de sesiones independientes (una conexión por sesión)."""
    return crear_fabrica_sesiones(motor)


@pytest.fixture
def db(fabrica_sesiones):
    with fabrica_sesiones() as sesion:
        yield sesion


@pytest.fixture
def client(fabrica_sesiones):
    def _sesion():
        with fabrica_sesiones() as sesion:
            yield sesion

    app.dependency_overrides[get_session] = _sesion
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---- Fábricas de datos (insertan directamente en la base) ------------------------------


@pytest.fixture
def crear_cliente(fabrica_sesiones):
    def _crear(dni="12345678", nombres="Ana", apellidos="Quispe", telefono="999111222", correo=None):
        with fabrica_sesiones() as s:
            cliente = Cliente(
                dni=dni, nombres=nombres, apellidos=apellidos, telefono=telefono, correo=correo
            )
            s.add(cliente)
            s.commit()
            return cliente.id

    return _crear


@pytest.fixture
def crear_equipo(fabrica_sesiones):
    def _crear(cliente_id, numero_serie="SN-0001", tipo="Laptop", marca="Lenovo", modelo="T14"):
        with fabrica_sesiones() as s:
            equipo = Equipo(
                cliente_id=cliente_id,
                tipo=tipo,
                marca=marca,
                modelo=modelo,
                numero_serie=numero_serie,
            )
            s.add(equipo)
            s.commit()
            return equipo.id

    return _crear


@pytest.fixture
def crear_tecnico(fabrica_sesiones):
    def _crear(nombres="Luis", apellidos="Rojas", disponible=True, cola=0):
        with fabrica_sesiones() as s:
            tecnico = Tecnico(nombres=nombres, apellidos=apellidos, disponible=disponible, cola=cola)
            s.add(tecnico)
            s.commit()
            return tecnico.id

    return _crear


@pytest.fixture
def crear_orden(fabrica_sesiones):
    """Inserta una orden directamente (para preparar estados como ENTREGADO)."""

    def _crear(equipo_id, tecnico_id, estado="RECEPCIONADO", id_op="OP-PREVIA-0001"):
        from decimal import Decimal

        with fabrica_sesiones() as s:
            n = s.query(OrdenServicio).count() + 1
            orden = OrdenServicio(
                codigo=f"OS-{n:06d}",
                equipo_id=equipo_id,
                tecnico_id=tecnico_id,
                estado=estado,
                estado_fisico="Sin daños",
                falla_reportada="No enciende",
                costo_revision=Decimal("40.00"),
                id_op=id_op,
            )
            s.add(orden)
            s.commit()
            return orden.codigo

    return _crear


@pytest.fixture
def leer(fabrica_sesiones):
    """Ejecuta una función con una sesión nueva para consultar el estado real de la base."""

    def _leer(funcion):
        with fabrica_sesiones() as s:
            return funcion(s)

    return _leer
