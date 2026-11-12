"""Configuración de ByteTrack leída de variables de entorno.

No contiene secretos ni credenciales (constitución, principio VI).
Los valores se leen en cada llamada para que las pruebas puedan modificarlos.
"""

import os
from decimal import Decimal

# Origen: GUI-01 («Costo de revisión S/ 40.00») y RN-11. RN-11 es una propuesta pendiente de
# confirmar con el taller y está fuera de alcance en C1.
COSTO_REVISION_POR_DEFECTO = "40.00"


def ruta_base_datos() -> str:
    """Ruta del archivo SQLite local (BYTETRACK_DB_PATH)."""
    return os.environ.get("BYTETRACK_DB_PATH", "./bytetrack.db")


def costo_revision_inicial() -> Decimal:
    """Costo de revisión inicial que se muestra y se guarda en cada orden (BYTETRACK_COSTO_REVISION)."""
    valor = os.environ.get("BYTETRACK_COSTO_REVISION", COSTO_REVISION_POR_DEFECTO)
    return Decimal(valor).quantize(Decimal("0.01"))
