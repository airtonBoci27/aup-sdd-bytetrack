"""Utilidades de seguridad puras (sin acceso a datos): hash de contraseñas y JWT (RNF-02).

Hash: ``hashlib.scrypt`` de la biblioteca estándar (research D4), formato
``scrypt$n$r$p$sal$hash`` con sal y hash en base64. Tokens: JWT HS256 con PyJWT (research D2).
"""

import base64
import binascii
from functools import lru_cache
import hashlib
import hmac
import secrets
import time
import uuid

import jwt

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
LONGITUD_SAL = 16
LONGITUD_HASH = 32
ALGORITMO_JWT = "HS256"
MEMORIA_MAXIMA = 64 * 1024 * 1024


class TokenInvalido(Exception):
    """El token no es un JWT válido: firma, formato, reclamos o vencimiento (RNF-02)."""


def _b64(datos: bytes) -> str:
    return base64.b64encode(datos).decode("ascii")


def _derivar(clave: str, sal: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(
        clave.encode("utf-8"), salt=sal, n=n, r=r, p=p, dklen=LONGITUD_HASH, maxmem=MEMORIA_MAXIMA
    )


def hashear_clave(clave: str) -> str:
    """RNF-02: hash scrypt con sal aleatoria; nunca se guarda la contraseña."""
    sal = secrets.token_bytes(LONGITUD_SAL)
    derivado = _derivar(clave, sal, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(sal)}${_b64(derivado)}"


@lru_cache(maxsize=1)
def hash_ficticio() -> str:
    """Hash scrypt de relleno para igualar el costo cuando el usuario no existe (RNF-02)."""
    return hashear_clave(secrets.token_urlsafe(24))


def verificar_clave(clave: str, almacenado: str) -> bool:
    """RNF-02: compara en tiempo constante; un formato inválido devuelve ``False``, sin excepción."""
    try:
        esquema, n, r, p, sal_b64, hash_b64 = almacenado.split("$")
        if esquema != "scrypt":
            return False
        n, r, p = int(n), int(r), int(p)
        sal = base64.b64decode(sal_b64, validate=True)
        esperado = base64.b64decode(hash_b64, validate=True)
        if not sal or not esperado or n < 2 or r < 1 or p < 1 or n > 2**20:
            return False
        obtenido = hashlib.scrypt(
            clave.encode("utf-8"), salt=sal, n=n, r=r, p=p, dklen=len(esperado), maxmem=MEMORIA_MAXIMA
        )
    except (ValueError, binascii.Error, MemoryError):
        return False
    return hmac.compare_digest(obtenido, esperado)


def crear_token(sub: str, minutos: int, clave_firma: str) -> tuple[str, str, int]:
    """RNF-02: crea un JWT HS256 con ``sub``, ``jti`` (UUID), ``iat`` y ``exp``.

    Devuelve ``(token, jti, exp)``.
    """
    ahora = int(time.time())
    jti = uuid.uuid4().hex
    exp = ahora + minutos * 60
    token = jwt.encode(
        {"sub": sub, "jti": jti, "iat": ahora, "exp": exp}, clave_firma, algorithm=ALGORITMO_JWT
    )
    return token, jti, exp


def decodificar_token(token: str, clave_firma: str) -> dict:
    """RNF-02: valida firma, vencimiento y reclamos obligatorios (``exp``, ``sub``, ``jti``)."""
    try:
        return jwt.decode(
            token,
            clave_firma,
            algorithms=[ALGORITMO_JWT],
            options={"require": ["exp", "sub", "jti"]},
        )
    except jwt.PyJWTError as error:
        raise TokenInvalido(str(error)) from error
