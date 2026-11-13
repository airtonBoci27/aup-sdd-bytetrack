"""Configuración de ByteTrack leída de variables de entorno.

No contiene secretos ni credenciales (constitución, principio VI): la clave de firma y las
contraseñas de los usuarios iniciales se leen del entorno o de un archivo ``.env`` ignorado por git.
Los valores se leen en cada llamada para que las pruebas puedan modificarlos.
Una variable vacía se trata como no definida.
"""

import os
from decimal import Decimal

from dotenv import load_dotenv

# Origen: GUI-01 («Costo de revisión S/ 40.00») y RN-11. RN-11 es una propuesta pendiente de
# confirmar con el taller y está fuera de alcance en C1.
COSTO_REVISION_POR_DEFECTO = "40.00"

# RNF-02: la duración de la sesión es configurable (no proviene de AUP; ver spec 002, Assumptions).
MINUTOS_SESION_POR_DEFECTO = 60
LONGITUD_MINIMA_CLAVE_JWT = 32
ARCHIVO_ENTORNO_POR_DEFECTO = "./.env"

USUARIO_RECEPCIONISTA_POR_DEFECTO = "recepcion"
USUARIO_TECNICO_POR_DEFECTO = "tecnico"

# Roles de los dos actores de AUP (Recepcionista y Técnico de laboratorio). RNF-02.
ROL_RECEPCIONISTA = "RECEPCIONISTA"
ROL_TECNICO = "TECNICO"


class ConfiguracionError(Exception):
    """Falta o es inválido un valor obligatorio de configuración (RNF-02, principio VI)."""


def _leer(nombre: str) -> str | None:
    """Valor de una variable de entorno, o ``None`` si no existe o está vacía/en blanco."""
    valor = os.environ.get(nombre)
    if valor is None or not valor.strip():
        return None
    return valor.strip()


def cargar_entorno() -> None:
    """Carga el archivo de entorno (``BYTETRACK_ENV_FILE`` o ``./.env``) sin pisar variables ya definidas.

    Se llama al arrancar la aplicación y en ``app.seed``; nunca al importar módulos, para que un
    ``.env`` local no afecte a las pruebas (RNF-02, research D6).
    """
    ruta = _leer("BYTETRACK_ENV_FILE") or ARCHIVO_ENTORNO_POR_DEFECTO
    load_dotenv(dotenv_path=ruta, override=False)


def ruta_base_datos() -> str:
    """Ruta del archivo SQLite local (BYTETRACK_DB_PATH)."""
    return _leer("BYTETRACK_DB_PATH") or "./bytetrack.db"


def costo_revision_inicial() -> Decimal:
    """Costo de revisión inicial que se muestra y se guarda en cada orden (BYTETRACK_COSTO_REVISION)."""
    valor = _leer("BYTETRACK_COSTO_REVISION") or COSTO_REVISION_POR_DEFECTO
    return Decimal(valor).quantize(Decimal("0.01"))


def clave_jwt() -> str:
    """Clave de firma de los tokens (RNF-02): obligatoria y de al menos 32 caracteres."""
    valor = _leer("BYTETRACK_JWT_SECRET")
    if valor is None:
        raise ConfiguracionError(
            "Falta la variable de entorno BYTETRACK_JWT_SECRET (clave de firma de los tokens)."
        )
    if len(valor) < LONGITUD_MINIMA_CLAVE_JWT:
        raise ConfiguracionError(
            f"BYTETRACK_JWT_SECRET debe tener al menos {LONGITUD_MINIMA_CLAVE_JWT} caracteres."
        )
    return valor


def minutos_sesion() -> int:
    """Duración de la sesión en minutos (BYTETRACK_SESION_MINUTOS, por defecto 60)."""
    valor = _leer("BYTETRACK_SESION_MINUTOS")
    if valor is None:
        return MINUTOS_SESION_POR_DEFECTO
    try:
        minutos = int(valor)
    except ValueError:
        raise ConfiguracionError("BYTETRACK_SESION_MINUTOS debe ser un número entero.") from None
    if minutos <= 0:
        raise ConfiguracionError("BYTETRACK_SESION_MINUTOS debe ser mayor que cero.")
    return minutos


def credenciales_iniciales() -> list[tuple[str, str, str]]:
    """Usuarios iniciales ``(nombre_usuario, clave, rol)`` leídos del entorno (RNF-02, principio VI).

    Las contraseñas no tienen valor por defecto: si falta una se lanza ``ConfiguracionError``.
    """
    resultado = []
    for prefijo, usuario_defecto, rol in (
        ("RECEPCIONISTA", USUARIO_RECEPCIONISTA_POR_DEFECTO, ROL_RECEPCIONISTA),
        ("TECNICO", USUARIO_TECNICO_POR_DEFECTO, ROL_TECNICO),
    ):
        nombre_clave = f"BYTETRACK_{prefijo}_CLAVE"
        clave = _leer(nombre_clave)
        if clave is None:
            raise ConfiguracionError(f"Falta la variable de entorno {nombre_clave}.")
        usuario = _leer(f"BYTETRACK_{prefijo}_USUARIO") or usuario_defecto
        resultado.append((usuario, clave, rol))
    return resultado
