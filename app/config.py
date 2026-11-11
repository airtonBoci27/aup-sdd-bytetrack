"""Configuración de ByteTrack leída de variables de entorno.

No contiene secretos ni credenciales (constitución, principio VI).
Los valores se leen en cada llamada para que las pruebas puedan modificarlos.
"""

import os
from decimal import Decimal

# Valor de prototipo, pendiente de confirmar con el taller. La documentación AUP solo
# menciona S/ 40 como propuesta de RN-11 (fuera de alcance en C1).
COSTO_REVISION_POR_DEFECTO = "40.00"


def ruta_base_datos() -> str:
    """Ruta del archivo SQLite local (BYTETRACK_DB_PATH)."""
    return os.environ.get("BYTETRACK_DB_PATH", "./bytetrack.db")


def costo_revision_inicial() -> Decimal:
    """Costo de revisión inicial que se muestra y se guarda en cada orden (BYTETRACK_COSTO_REVISION)."""
    valor = os.environ.get("BYTETRACK_COSTO_REVISION", COSTO_REVISION_POR_DEFECTO)
    return Decimal(valor).quantize(Decimal("0.01"))
