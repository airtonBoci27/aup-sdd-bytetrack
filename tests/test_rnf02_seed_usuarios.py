"""RNF-02 / principio VI: carga de los usuarios iniciales desde variables de entorno (app.seed).

Las contraseñas se generan en la prueba; ninguna vive en el repositorio.
"""

import secrets

import pytest

from app import config, security, seed
from app.models.entities import Usuario


@pytest.fixture
def claves(monkeypatch, tmp_path):
    """Fija las contraseñas por entorno y aísla la prueba de cualquier .env local."""
    monkeypatch.setenv("BYTETRACK_ENV_FILE", str(tmp_path / "no_existe.env"))
    for nombre in (
        "BYTETRACK_RECEPCIONISTA_USUARIO",
        "BYTETRACK_TECNICO_USUARIO",
        "BYTETRACK_RECEPCIONISTA_CLAVE",
        "BYTETRACK_TECNICO_CLAVE",
    ):
        monkeypatch.delenv(nombre, raising=False)
    datos = {"recepcion": secrets.token_urlsafe(12), "tecnico": secrets.token_urlsafe(12)}
    monkeypatch.setenv("BYTETRACK_RECEPCIONISTA_CLAVE", datos["recepcion"])
    monkeypatch.setenv("BYTETRACK_TECNICO_CLAVE", datos["tecnico"])
    return datos


def _usuarios(leer):
    return leer(lambda s: {u.nombre_usuario: (u.rol, u.clave_hash) for u in s.query(Usuario)})


def test_rnf02_seed_crea_los_dos_usuarios_con_hash_y_rol(claves, fabrica_sesiones, leer):
    seed.cargar_usuarios(fabrica_sesiones)
    usuarios = _usuarios(leer)
    assert set(usuarios) == {"recepcion", "tecnico"}
    assert usuarios["recepcion"][0] == "RECEPCIONISTA" and usuarios["tecnico"][0] == "TECNICO"
    for nombre, clave in claves.items():
        assert usuarios[nombre][1].startswith("scrypt$")
        assert security.verificar_clave(clave, usuarios[nombre][1])


def test_rnf02_seed_usa_los_nombres_de_usuario_configurados(
    claves, monkeypatch, fabrica_sesiones, leer
):
    monkeypatch.setenv("BYTETRACK_RECEPCIONISTA_USUARIO", "ana")
    seed.cargar_usuarios(fabrica_sesiones)
    assert set(_usuarios(leer)) == {"ana", "tecnico"}


def test_rnf02_seed_es_idempotente_no_duplica(claves, fabrica_sesiones, leer):
    seed.cargar_usuarios(fabrica_sesiones)
    seed.cargar_usuarios(fabrica_sesiones)
    assert leer(lambda s: s.query(Usuario).count()) == 2


def test_rnf02_seed_actualiza_el_hash_si_cambia_la_contraseña(
    claves, monkeypatch, fabrica_sesiones, leer
):
    seed.cargar_usuarios(fabrica_sesiones)
    nueva = secrets.token_urlsafe(12)
    monkeypatch.setenv("BYTETRACK_RECEPCIONISTA_CLAVE", nueva)
    seed.cargar_usuarios(fabrica_sesiones)
    _rol, hash_actual = _usuarios(leer)["recepcion"]
    assert security.verificar_clave(nueva, hash_actual)
    assert not security.verificar_clave(claves["recepcion"], hash_actual)
    assert leer(lambda s: s.query(Usuario).count()) == 2


def test_rnf02_seed_falla_con_mensaje_claro_si_falta_una_contraseña(
    claves, monkeypatch, fabrica_sesiones, leer, capsys
):
    monkeypatch.delenv("BYTETRACK_TECNICO_CLAVE")
    with pytest.raises(config.ConfiguracionError, match="BYTETRACK_TECNICO_CLAVE"):
        seed.cargar_usuarios(fabrica_sesiones)
    assert leer(lambda s: s.query(Usuario).count()) == 0  # no se crea ninguno a medias
    assert seed.main() == 1  # `python -m app.seed` termina con código distinto de cero
    assert "BYTETRACK_TECNICO_CLAVE" in capsys.readouterr().err


def test_rnf02_seed_no_guarda_la_contraseña_en_claro(claves, fabrica_sesiones, leer):
    seed.cargar_usuarios(fabrica_sesiones)
    for _rol, clave_hash in _usuarios(leer).values():
        assert all(clave not in clave_hash for clave in claves.values())
