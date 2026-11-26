"""RNF-02: acceso por rol y sesiones activas sobre las operaciones de recepción.

Precondición de CU-01 («sesión iniciada»); riesgo R3 de AUP (las reglas no deben saltarse llamando a
la API). Las contraseñas y la clave de firma se generan en tiempo de ejecución (conftest).
"""

import secrets
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from app import config, security
from app.models.entities import (
    Cliente,
    Equipo,
    OperacionIdempotente,
    OrdenServicio,
    Tecnico,
    TokenRevocado,
    Usuario,
)

DNI_EXISTENTE = "12345678"
DNI_NUEVO = "87654321"
ENCABEZADO_401 = "Bearer"


def _orden(tecnico_id, id_op="op-rnf02-0001"):
    return {
        "id_op": id_op,
        "dni": DNI_EXISTENTE,
        "equipo_id": None,
        "equipo": {"tipo": "Laptop", "marca": "Dell", "modelo": "XPS", "numero_serie": "SN-RNF02"},
        "accesorios": "Cargador",
        "estado_fisico": "Bisagra floja",
        "falla_reportada": "No carga",
        "tecnico_id": tecnico_id,
    }


def _cliente_nuevo():
    return {"dni": DNI_NUEVO, "nombres": "Lucía", "apellidos": "Paredes", "telefono": "987123456"}


def _operaciones(tecnico_id):
    """Las cinco operaciones de recepción: (nombre, método, ruta, argumentos)."""
    return [
        ("buscar_cliente", "get", f"/clientes/{DNI_EXISTENTE}", {}),
        ("registrar_cliente", "post", "/clientes", {"json": _cliente_nuevo()}),
        ("tecnicos_disponibles", "get", "/tecnicos/disponibles", {}),
        ("costo_revision", "get", "/ordenes/costo-revision-inicial", {}),
        ("registrar_orden", "post", "/ordenes", {"json": _orden(tecnico_id)}),
    ]


NOMBRES = ["buscar_cliente", "registrar_cliente", "tecnicos_disponibles", "costo_revision", "registrar_orden"]


@pytest.fixture
def datos_base(crear_cliente, crear_tecnico):
    """Un cliente existente y un técnico disponible (id del técnico)."""
    crear_cliente(DNI_EXISTENTE)
    return crear_tecnico(cola=0)


def _llamar(cliente, operacion, headers=None):
    _nombre, metodo, ruta, kwargs = operacion
    return getattr(cliente, metodo)(ruta, headers=headers, **kwargs)


def _por_nombre(tecnico_id, nombre):
    return next(op for op in _operaciones(tecnico_id) if op[0] == nombre)


def _foto(leer):
    """Estado observable de la base, para comprobar que un rechazo no cambia nada."""
    return leer(
        lambda s: (
            s.query(Cliente).count(),
            s.query(Equipo).count(),
            s.query(OrdenServicio).count(),
            s.query(OperacionIdempotente).count(),
            [t.cola for t in s.query(Tecnico).order_by(Tecnico.id)],
        )
    )


# ---- Inicio de sesión ----------------------------------------------------------------


def test_rnf02_login_recepcionista_devuelve_token_bearer_y_rol(
    client_sin_sesion, crear_usuario, clave_de
):
    crear_usuario("recepcion", "RECEPCIONISTA")
    r = client_sin_sesion.post(
        "/auth/token", data={"username": "recepcion", "password": clave_de("RECEPCIONISTA")}
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer" and cuerpo["rol"] == "RECEPCIONISTA"
    reclamos = security.decodificar_token(cuerpo["access_token"], config.clave_jwt())
    assert reclamos["sub"] == "recepcion" and reclamos["jti"] and reclamos["exp"] > time.time()


def test_rnf02_login_tecnico_obtiene_token_con_rol_tecnico(client_sin_sesion, crear_usuario, clave_de):
    crear_usuario("tecnico", "TECNICO")
    r = client_sin_sesion.post(
        "/auth/token", data={"username": "tecnico", "password": clave_de("TECNICO")}
    )
    assert r.status_code == 200 and r.json()["rol"] == "TECNICO"


def test_rnf02_login_credenciales_invalidas_devuelve_401(client_sin_sesion, crear_usuario, clave_de):
    crear_usuario("recepcion", "RECEPCIONISTA")
    for usuario, clave in (
        ("recepcion", clave_de("RECEPCIONISTA") + "x"),  # contraseña incorrecta
        ("no_existe", clave_de("RECEPCIONISTA")),  # usuario inexistente
    ):
        r = client_sin_sesion.post("/auth/token", data={"username": usuario, "password": clave})
        assert r.status_code == 401
        assert r.json()["codigo"] == "CREDENCIALES_INVALIDAS"
        assert r.json()["mensaje"] == "Usuario o contraseña incorrectos"
        assert r.headers["WWW-Authenticate"] == ENCABEZADO_401
        assert "access_token" not in r.json()


def test_rnf02_login_sin_campos_devuelve_422(client_sin_sesion):
    assert client_sin_sesion.post("/auth/token", data={"username": "recepcion"}).status_code == 422
    assert client_sin_sesion.post("/auth/token", data={}).status_code == 422


# ---- Sin sesión activa ---------------------------------------------------------------


@pytest.mark.parametrize("nombre", NOMBRES)
def test_rnf02_sin_sesion_devuelve_401_no_autenticado(client_sin_sesion, datos_base, nombre):
    r = _llamar(client_sin_sesion, _por_nombre(datos_base, nombre))
    assert r.status_code == 401
    assert r.json() == {"codigo": "NO_AUTENTICADO", "mensaje": "Debe iniciar sesión", "detalle": {}}
    assert r.headers["WWW-Authenticate"] == ENCABEZADO_401


@pytest.mark.parametrize("nombre", NOMBRES)
def test_rnf02_esquema_distinto_de_bearer_devuelve_401(client_sin_sesion, datos_base, nombre):
    r = _llamar(
        client_sin_sesion, _por_nombre(datos_base, nombre), headers={"Authorization": "Basic abc"}
    )
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


@pytest.mark.parametrize("nombre", NOMBRES)
def test_rnf02_token_vencido_devuelve_401(client_sin_sesion, crear_usuario, datos_base, nombre):
    crear_usuario("recepcion", "RECEPCIONISTA")
    vencido, _, _ = security.crear_token("recepcion", -1, config.clave_jwt())
    r = _llamar(
        client_sin_sesion,
        _por_nombre(datos_base, nombre),
        headers={"Authorization": f"Bearer {vencido}"},
    )
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


@pytest.mark.parametrize("nombre", NOMBRES)
def test_rnf02_token_con_firma_ajena_devuelve_401(client_sin_sesion, crear_usuario, datos_base, nombre):
    crear_usuario("recepcion", "RECEPCIONISTA")
    ajeno, _, _ = security.crear_token("recepcion", 60, secrets.token_urlsafe(48))
    r = _llamar(
        client_sin_sesion,
        _por_nombre(datos_base, nombre),
        headers={"Authorization": f"Bearer {ajeno}"},
    )
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


@pytest.mark.parametrize("nombre", NOMBRES)
def test_rnf02_token_de_usuario_inexistente_devuelve_401(client_sin_sesion, datos_base, nombre):
    huerfano, _, _ = security.crear_token("fantasma", 60, config.clave_jwt())
    r = _llamar(
        client_sin_sesion,
        _por_nombre(datos_base, nombre),
        headers={"Authorization": f"Bearer {huerfano}"},
    )
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


# ---- Rol Técnico ---------------------------------------------------------------------


@pytest.mark.parametrize("nombre", NOMBRES)
def test_rnf02_tecnico_devuelve_403_rol_no_permitido_sin_datos(client_tecnico, datos_base, nombre):
    r = _llamar(client_tecnico, _por_nombre(datos_base, nombre))
    assert r.status_code == 403
    assert r.json() == {
        "codigo": "ROL_NO_PERMITIDO",
        "mensaje": "Su rol no tiene acceso a las operaciones de recepción",
        "detalle": {},
    }
    assert "WWW-Authenticate" not in r.headers


def test_rnf02_recepcionista_accede_a_las_cinco_operaciones(client, datos_base):
    esperado = {
        "buscar_cliente": 200,
        "registrar_cliente": 201,
        "tecnicos_disponibles": 200,
        "costo_revision": 200,
        "registrar_orden": 201,
    }
    for operacion in _operaciones(datos_base):
        r = _llamar(client, operacion)
        assert r.status_code == esperado[operacion[0]], (operacion[0], r.text)


# ---- El control de acceso va antes que la validación del cuerpo ----------------------


@pytest.mark.parametrize("ruta", ["/ordenes", "/clientes"])
def test_rnf02_sin_sesion_cuerpo_invalido_devuelve_401_y_no_422(client_sin_sesion, ruta):
    r = client_sin_sesion.post(ruta, json={"campo": "inválido"})
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


@pytest.mark.parametrize("ruta", ["/ordenes", "/clientes"])
def test_rnf02_tecnico_cuerpo_invalido_devuelve_403_y_no_422(client_tecnico, ruta):
    r = client_tecnico.post(ruta, json={"campo": "inválido"})
    assert r.status_code == 403 and r.json()["codigo"] == "ROL_NO_PERMITIDO"


def test_rnf02_dni_invalido_sin_sesion_devuelve_401_y_no_422(client_sin_sesion):
    assert client_sin_sesion.get("/clientes/123").status_code == 401


# ---- Un rechazo no crea ni modifica nada ---------------------------------------------


@pytest.mark.parametrize("cliente_fixture", ["client_sin_sesion", "client_tecnico"])
def test_rnf02_rechazo_no_crea_ni_modifica_registros(request, cliente_fixture, datos_base, leer):
    cliente = request.getfixturevalue(cliente_fixture)
    antes = _foto(leer)
    for operacion in _operaciones(datos_base):
        assert _llamar(cliente, operacion).status_code in (401, 403)
    assert _foto(leer) == antes  # sin clientes, equipos, órdenes, ID OP ni cola nuevos


def test_rnf02_rechazo_no_registra_el_id_op_y_se_puede_reintentar(
    client_tecnico, client_sin_sesion, datos_base, crear_usuario, iniciar_sesion, leer
):
    cuerpo = _orden(datos_base, id_op="op-rnf02-reintento")
    assert client_tecnico.post("/ordenes", json=cuerpo).status_code == 403
    assert leer(lambda s: s.query(OperacionIdempotente).count()) == 0
    crear_usuario("recepcion", "RECEPCIONISTA")
    token = iniciar_sesion(client_sin_sesion, "recepcion", "RECEPCIONISTA")
    r = client_sin_sesion.post(
        "/ordenes", json=cuerpo, headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 201


def test_rnf02_rol_se_lee_de_la_base_en_cada_solicitud(client, fabrica_sesiones):
    assert client.get("/tecnicos/disponibles").status_code == 200
    with fabrica_sesiones() as s:
        s.query(Usuario).filter_by(nombre_usuario="recepcion").one().rol = "TECNICO"
        s.commit()
    r = client.get("/tecnicos/disponibles")
    assert r.status_code == 403 and r.json()["codigo"] == "ROL_NO_PERMITIDO"
    with fabrica_sesiones() as s:
        s.query(Usuario).filter_by(nombre_usuario="recepcion").delete()
        s.commit()
    assert client.get("/tecnicos/disponibles").status_code == 401


# ---- Cierre de sesión ----------------------------------------------------------------


def test_rnf02_logout_devuelve_204_y_revoca_el_token(client, datos_base, leer):
    assert client.get("/tecnicos/disponibles").status_code == 200
    r = client.post("/auth/logout")
    assert r.status_code == 204 and r.content == b""
    assert leer(lambda s: s.query(TokenRevocado).count()) == 1
    for operacion in _operaciones(datos_base):
        respuesta = _llamar(client, operacion)
        assert respuesta.status_code == 401 and respuesta.json()["codigo"] == "NO_AUTENTICADO"


def test_rnf02_logout_dos_veces_el_segundo_devuelve_401(client):
    assert client.post("/auth/logout").status_code == 204
    r = client.post("/auth/logout")
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


def test_rnf02_logout_sin_sesion_devuelve_401(client_sin_sesion):
    r = client_sin_sesion.post("/auth/logout")
    assert r.status_code == 401 and r.json()["codigo"] == "NO_AUTENTICADO"


def test_rnf02_logout_permitido_a_cualquier_rol(client_tecnico):
    assert client_tecnico.post("/auth/logout").status_code == 204


def test_rnf02_login_usuario_inexistente_ejecuta_verificacion_de_hash(client_sin_sesion, monkeypatch):
    """RNF-02: iguala el flujo criptográfico aunque el usuario no exista (mitiga enumeración por tiempo)."""
    from app import security

    llamadas = []
    original = security.verificar_clave

    def _espia(clave, almacenado):
        llamadas.append(almacenado)
        return original(clave, almacenado)

    monkeypatch.setattr(security, "verificar_clave", _espia)
    r = client_sin_sesion.post("/auth/token", data={"username": "no-existe", "password": "x"})

    assert r.status_code == 401
    assert r.json()["codigo"] == "CREDENCIALES_INVALIDAS"
    assert len(llamadas) == 1


def test_rnf02_logout_permite_iniciar_sesion_con_otro_usuario(
    client, crear_usuario, iniciar_sesion
):
    assert client.post("/auth/logout").status_code == 204
    crear_usuario("tecnico", "TECNICO")
    token = iniciar_sesion(client, "tecnico", "TECNICO")
    r = client.get("/tecnicos/disponibles", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403  # sesión nueva de Técnico, rechazada por rol


def test_rnf02_logout_purga_tokens_revocados_vencidos(client, fabrica_sesiones, leer):
    with fabrica_sesiones() as s:
        s.add(TokenRevocado(jti="viejo-1", expira_en=1))
        s.add(TokenRevocado(jti="viejo-2", expira_en=int(time.time()) - 10))
        s.commit()
    assert client.post("/auth/logout").status_code == 204
    jtis = leer(lambda s: {t.jti for t in s.query(TokenRevocado)})
    assert "viejo-1" not in jtis and "viejo-2" not in jtis and len(jtis) == 1


# ---- Documentación pública -----------------------------------------------------------


def test_rnf02_docs_y_openapi_siguen_publicos(client_sin_sesion):
    assert client_sin_sesion.get("/docs").status_code == 200
    assert client_sin_sesion.get("/openapi.json").status_code == 200


# ---- RN-10 con el control de acceso activo (research D7) -----------------------------


def test_rnf02_rn10_concurrencia_con_sesion_de_recepcionista(client, datos_base, leer):
    """RN-10 / RNF-04: el control de acceso no rompe la serialización de escrituras de C1."""
    cuerpo = _orden(datos_base, id_op="op-rnf02-concurrente")
    with ThreadPoolExecutor(max_workers=4) as pool:
        respuestas = list(pool.map(lambda _: client.post("/ordenes", json=cuerpo), range(4)))
    assert sorted(r.status_code for r in respuestas) == [200, 200, 200, 201]
    assert leer(lambda s: s.query(OrdenServicio).count()) == 1
    assert leer(lambda s: s.get(Tecnico, datos_base).cola) == 1
