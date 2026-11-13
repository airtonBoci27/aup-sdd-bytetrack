"""Fixtures compartidas: base SQLite temporal en archivo y cliente de pruebas.

La base es un archivo (no memoria) para poder abrir conexiones independientes en las
pruebas de concurrencia (RN-02, RN-10).
"""

import secrets
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app import security
from app.api.seguridad import get_session_seguridad
from app.database import (
    Base,
    crear_fabrica_sesiones,
    crear_motor,
    get_session,
)
from app.main import app
from app.models.entities import Cliente, Equipo, OrdenServicio, Tecnico, Usuario

# RNF-02 / principio VI: ninguna contraseña ni clave de firma vive en el repositorio; se generan al
# ejecutar las pruebas. El hash se calcula una sola vez por ejecución (scrypt es deliberadamente lento).
_CLAVES = {
    "RECEPCIONISTA": secrets.token_urlsafe(12),
    "TECNICO": secrets.token_urlsafe(12),
}
_HASHES: dict[str, str] = {}


def _hash_de(rol: str) -> str:
    if rol not in _HASHES:
        _HASHES[rol] = security.hashear_clave(_CLAVES[rol])
    return _HASHES[rol]


@pytest.fixture(autouse=True)
def _entorno_de_seguridad(monkeypatch):
    """Clave de firma generada en tiempo de ejecución; sin variables heredadas del entorno."""
    monkeypatch.setenv("BYTETRACK_JWT_SECRET", secrets.token_urlsafe(48))
    monkeypatch.delenv("BYTETRACK_SESION_MINUTOS", raising=False)


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
def _bd_de_prueba(fabrica_sesiones):
    """Sobrescribe las dos dependencias de sesión con la misma base temporal (research D7)."""

    def _sesion():
        with fabrica_sesiones() as sesion:
            yield sesion

    app.dependency_overrides[get_session] = _sesion
    app.dependency_overrides[get_session_seguridad] = _sesion
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def crear_usuario(fabrica_sesiones):
    """Inserta un usuario con el hash de la contraseña de prueba de su rol (RNF-02)."""

    def _crear(nombre_usuario="recepcion", rol="RECEPCIONISTA", clave_hash=None):
        with fabrica_sesiones() as s:
            usuario = Usuario(
                nombre_usuario=nombre_usuario, clave_hash=clave_hash or _hash_de(rol), rol=rol
            )
            s.add(usuario)
            s.commit()
            return usuario.id

    return _crear


@pytest.fixture
def clave_de():
    """Contraseña de prueba (generada al ejecutar) de cada rol."""
    return lambda rol: _CLAVES[rol]


@pytest.fixture
def iniciar_sesion(clave_de):
    """Inicia sesión por la API y devuelve el token (RNF-02)."""

    def _iniciar(cliente, nombre_usuario="recepcion", rol="RECEPCIONISTA", clave=None):
        respuesta = cliente.post(
            "/auth/token",
            data={"username": nombre_usuario, "password": clave or clave_de(rol)},
        )
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()["access_token"]

    return _iniciar


@pytest.fixture
def client_sin_sesion(_bd_de_prueba):
    """Cliente sin cabecera Authorization (RNF-02: debe ser rechazado)."""
    return TestClient(app)


def _cliente_con_sesion(token: str) -> TestClient:
    """TestClient que siempre envía la sesión, también los clientes derivados de él.

    Algunas pruebas de C1 crean otro cliente con ``type(client)(client.app, ...)``; la subclase
    mantiene la cabecera ``Authorization`` en esos casos sin modificar esas pruebas.
    """

    class ClienteConSesion(TestClient):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("headers", {"Authorization": f"Bearer {token}"})
            super().__init__(*args, **kwargs)

    return ClienteConSesion(app)


@pytest.fixture
def client(_bd_de_prueba, crear_usuario, iniciar_sesion):
    """Cliente con sesión de Recepcionista, para que las pruebas de C1 no cambien (RNF-02)."""
    crear_usuario("recepcion", "RECEPCIONISTA")
    token = iniciar_sesion(TestClient(app), "recepcion", "RECEPCIONISTA")
    return _cliente_con_sesion(token)


@pytest.fixture
def client_tecnico(_bd_de_prueba, crear_usuario, iniciar_sesion):
    """Cliente con sesión de Técnico (RNF-02: rol sin acceso a recepción)."""
    crear_usuario("tecnico", "TECNICO")
    token = iniciar_sesion(TestClient(app), "tecnico", "TECNICO")
    return _cliente_con_sesion(token)


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
                codigo=f"OS-{date.today().year}-{n:04d}",
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
