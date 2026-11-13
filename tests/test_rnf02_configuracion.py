"""RNF-02: configuración de seguridad, hash de contraseñas y tokens (principio VI).

Ninguna prueba contiene secretos: las claves y contraseñas se generan en tiempo de ejecución.
"""

import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import jwt
import pytest

from app import config, security

RAIZ = Path(__file__).resolve().parents[1]
VARIABLES = [
    "BYTETRACK_JWT_SECRET",
    "BYTETRACK_SESION_MINUTOS",
    "BYTETRACK_ENV_FILE",
    "BYTETRACK_DB_PATH",
    "BYTETRACK_COSTO_REVISION",
    "BYTETRACK_RECEPCIONISTA_USUARIO",
    "BYTETRACK_RECEPCIONISTA_CLAVE",
    "BYTETRACK_TECNICO_USUARIO",
    "BYTETRACK_TECNICO_CLAVE",
]


@pytest.fixture(autouse=True)
def entorno_limpio(monkeypatch):
    for nombre in VARIABLES:
        monkeypatch.delenv(nombre, raising=False)


# ---- Configuración -------------------------------------------------------------------


def test_rnf02_clave_jwt_ausente_o_vacia_falla(monkeypatch):
    with pytest.raises(config.ConfiguracionError):
        config.clave_jwt()
    monkeypatch.setenv("BYTETRACK_JWT_SECRET", "   ")
    with pytest.raises(config.ConfiguracionError):
        config.clave_jwt()


def test_rnf02_clave_jwt_menor_de_32_caracteres_falla(monkeypatch):
    monkeypatch.setenv("BYTETRACK_JWT_SECRET", secrets.token_hex(15) + "a")  # 31 caracteres
    with pytest.raises(config.ConfiguracionError):
        config.clave_jwt()
    valida = secrets.token_hex(16)  # 32 caracteres
    monkeypatch.setenv("BYTETRACK_JWT_SECRET", valida)
    assert config.clave_jwt() == valida


def test_rnf02_sesion_minutos_por_defecto_60_y_configurable(monkeypatch):
    assert config.minutos_sesion() == 60
    monkeypatch.setenv("BYTETRACK_SESION_MINUTOS", "5")
    assert config.minutos_sesion() == 5
    monkeypatch.setenv("BYTETRACK_SESION_MINUTOS", "0")
    with pytest.raises(config.ConfiguracionError):
        config.minutos_sesion()
    monkeypatch.setenv("BYTETRACK_SESION_MINUTOS", "abc")
    with pytest.raises(config.ConfiguracionError):
        config.minutos_sesion()


def test_rnf02_cargar_entorno_no_sobrescribe_variables_ya_definidas(monkeypatch, tmp_path):
    archivo = tmp_path / "entorno"
    archivo.write_text("BYTETRACK_SESION_MINUTOS=5\nBYTETRACK_COSTO_REVISION=55.00\n")
    monkeypatch.setenv("BYTETRACK_ENV_FILE", str(archivo))
    monkeypatch.setenv("BYTETRACK_SESION_MINUTOS", "10")
    config.cargar_entorno()
    assert os.environ["BYTETRACK_SESION_MINUTOS"] == "10"  # el entorno prevalece
    assert os.environ["BYTETRACK_COSTO_REVISION"] == "55.00"  # lo no definido se toma del archivo
    monkeypatch.delenv("BYTETRACK_COSTO_REVISION")


def test_rnf02_cargar_entorno_usa_BYTETRACK_ENV_FILE(monkeypatch, tmp_path):
    carpeta_externa = tmp_path / "fuera_del_proyecto"
    carpeta_externa.mkdir()
    archivo = carpeta_externa / "bytetrack.env"
    clave = secrets.token_urlsafe(48)
    archivo.write_text(f"BYTETRACK_JWT_SECRET={clave}\n")
    monkeypatch.setenv("BYTETRACK_ENV_FILE", str(archivo))
    config.cargar_entorno()
    try:
        assert config.clave_jwt() == clave
    finally:
        os.environ.pop("BYTETRACK_JWT_SECRET", None)


def test_rnf02_variable_vacia_se_trata_como_no_definida(monkeypatch):
    monkeypatch.setenv("BYTETRACK_DB_PATH", "")
    monkeypatch.setenv("BYTETRACK_COSTO_REVISION", "  ")
    monkeypatch.setenv("BYTETRACK_JWT_SECRET", "")
    assert config.ruta_base_datos() == "./bytetrack.db"
    assert str(config.costo_revision_inicial()) == "40.00"
    with pytest.raises(config.ConfiguracionError):
        config.clave_jwt()


def test_rnf02_importar_la_app_no_lee_el_env(tmp_path):
    (tmp_path / ".env").write_text("BYTETRACK_SESION_MINUTOS=7\n")
    entorno = {k: v for k, v in os.environ.items() if k not in VARIABLES}
    entorno["PYTHONPATH"] = str(RAIZ)
    salida = subprocess.run(
        [sys.executable, "-c",
         "import os, app.main; print(os.environ.get('BYTETRACK_SESION_MINUTOS'))"],
        cwd=tmp_path, env=entorno, capture_output=True, text=True, check=True,
    )
    assert salida.stdout.strip() == "None"


def test_rnf02_credenciales_iniciales_exigen_las_dos_claves_y_usan_usuarios_por_defecto(monkeypatch):
    with pytest.raises(config.ConfiguracionError, match="BYTETRACK_RECEPCIONISTA_CLAVE"):
        config.credenciales_iniciales()
    clave_r, clave_t = secrets.token_urlsafe(12), secrets.token_urlsafe(12)
    monkeypatch.setenv("BYTETRACK_RECEPCIONISTA_CLAVE", clave_r)
    with pytest.raises(config.ConfiguracionError, match="BYTETRACK_TECNICO_CLAVE"):
        config.credenciales_iniciales()
    monkeypatch.setenv("BYTETRACK_TECNICO_CLAVE", clave_t)
    assert config.credenciales_iniciales() == [
        ("recepcion", clave_r, "RECEPCIONISTA"),
        ("tecnico", clave_t, "TECNICO"),
    ]
    monkeypatch.setenv("BYTETRACK_RECEPCIONISTA_USUARIO", "ana")
    assert config.credenciales_iniciales()[0][0] == "ana"


# ---- Hash de contraseñas -------------------------------------------------------------


def test_rnf02_hash_scrypt_formato_y_verificacion():
    clave = secrets.token_urlsafe(12)
    almacenado = security.hashear_clave(clave)
    partes = almacenado.split("$")
    assert partes[0] == "scrypt" and len(partes) == 6
    assert all(p for p in partes)
    assert security.verificar_clave(clave, almacenado) is True
    assert security.verificar_clave(clave + "x", almacenado) is False


def test_rnf02_hash_con_sal_distinta_por_llamada():
    clave = secrets.token_urlsafe(12)
    assert security.hashear_clave(clave) != security.hashear_clave(clave)


def test_rnf02_hash_no_contiene_la_contraseña():
    clave = secrets.token_urlsafe(16)
    assert clave not in security.hashear_clave(clave)


@pytest.mark.parametrize("basura", ["", "texto", "scrypt$1$2", "bcrypt$a$b$c$d$e", "scrypt$x$y$z$@@$@@"])
def test_rnf02_verificar_hash_con_formato_invalido_devuelve_falso(basura):
    assert security.verificar_clave("cualquiera", basura) is False


# ---- JWT -----------------------------------------------------------------------------


def test_rnf02_jwt_crear_y_decodificar_sub_jti_exp():
    firma = secrets.token_urlsafe(48)
    token, jti, exp = security.crear_token("recepcion", 60, firma)
    reclamos = security.decodificar_token(token, firma)
    assert reclamos["sub"] == "recepcion" and reclamos["jti"] == jti and reclamos["exp"] == exp
    assert reclamos["iat"] <= time.time() + 1
    assert abs(exp - (time.time() + 3600)) < 5
    assert jwt.get_unverified_header(token)["alg"] == "HS256"


def test_rnf02_jwt_vencido_se_rechaza():
    firma = secrets.token_urlsafe(48)
    token, _, _ = security.crear_token("recepcion", -1, firma)
    with pytest.raises(security.TokenInvalido):
        security.decodificar_token(token, firma)


def test_rnf02_jwt_con_firma_de_otra_clave_se_rechaza():
    token, _, _ = security.crear_token("recepcion", 60, secrets.token_urlsafe(48))
    with pytest.raises(security.TokenInvalido):
        security.decodificar_token(token, secrets.token_urlsafe(48))


def test_rnf02_jwt_alg_none_se_rechaza():
    firma = secrets.token_urlsafe(48)
    sin_firma = jwt.encode(
        {"sub": "recepcion", "jti": "x", "exp": int(time.time()) + 600}, None, algorithm="none"
    )
    with pytest.raises(security.TokenInvalido):
        security.decodificar_token(sin_firma, firma)


@pytest.mark.parametrize("faltante", ["sub", "jti"])
def test_rnf02_jwt_sin_jti_o_sin_sub_se_rechaza(faltante):
    firma = secrets.token_urlsafe(48)
    reclamos = {"sub": "recepcion", "jti": "x", "exp": int(time.time()) + 600}
    del reclamos[faltante]
    token = jwt.encode(reclamos, firma, algorithm="HS256")
    with pytest.raises(security.TokenInvalido):
        security.decodificar_token(token, firma)


def test_rnf02_jwt_basura_se_rechaza():
    with pytest.raises(security.TokenInvalido):
        security.decodificar_token("no-es-un-jwt", secrets.token_urlsafe(48))
