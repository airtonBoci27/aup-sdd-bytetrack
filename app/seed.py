"""Datos de demostración para uso local: técnicos (su mantenimiento no pertenece a C1).

Uso: ``uv run python -m app.seed`` (idempotente: no duplica técnicos si ya existen).
Solo contiene nombres ficticios; no incluye credenciales ni datos personales reales.
"""

from sqlalchemy import select

from app.database import _fabrica_por_defecto, crear_tablas
from app.models.entities import Tecnico

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


if __name__ == "__main__":
    creados = cargar_tecnicos()
    print(f"Técnicos de demostración creados: {creados}")
