"""Datos iniciales (fase de Transición) para uso local: técnicos y usuarios.

Uso: ``uv run python -m app.seed`` (idempotente: no duplica técnicos ni usuarios si ya existen).
Los nombres de técnicos son ficticios. Las contraseñas de los usuarios iniciales NO están en el
código: se leen de variables de entorno o del ``.env`` (RNF-02, principio VI); si falta alguna, la
carga termina con un error que nombra la variable.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app import config, security
from app.database import _fabrica_por_defecto, crear_tablas
from app.models.entities import Tecnico
from app.repositories.usuario_repository import UsuarioRepository

TECNICOS_DEMO = [
    ("Luis", "Rojas", True),
    ("Carla", "Mendoza", True),
    ("Jorge", "Paredes", False),
]


def cargar_tecnicos() -> int:
    """Crea los técnicos de demostración si la tabla está vacía; devuelve cuántos creó."""
    crear_tablas()
    with _fabrica_por_defecto()() as sesion:
        if sesion.scalar(select(Tecnico.id).limit(1)) is not None:
            return 0
        for nombres, apellidos, disponible in TECNICOS_DEMO:
            sesion.add(Tecnico(nombres=nombres, apellidos=apellidos, disponible=disponible, cola=0))
        sesion.commit()
        return len(TECNICOS_DEMO)


def cargar_usuarios(fabrica: sessionmaker[Session] | None = None) -> int:
    """RNF-02: crea o actualiza los usuarios iniciales desde el entorno; devuelve cuántos procesó.

    Lanza ``ConfiguracionError`` (sin crear ninguno) si falta una contraseña. Guarda solo el hash.
    """
    credenciales = config.credenciales_iniciales()  # falla antes de tocar la base
    if fabrica is None:
        crear_tablas()
        fabrica = _fabrica_por_defecto()
    with fabrica() as sesion:
        repositorio = UsuarioRepository(sesion)
        for nombre_usuario, clave, rol in credenciales:
            repositorio.crear_o_actualizar(nombre_usuario, security.hashear_clave(clave), rol)
        sesion.commit()
    return len(credenciales)


def main() -> int:
    config.cargar_entorno()
    try:
        usuarios = cargar_usuarios()
    except config.ConfiguracionError as error:
        print(f"Error de configuración: {error}", file=sys.stderr)
        return 1
    tecnicos = cargar_tecnicos()
    print(f"Usuarios cargados o actualizados: {usuarios}")
    print(f"Técnicos de demostración creados: {tecnicos}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
