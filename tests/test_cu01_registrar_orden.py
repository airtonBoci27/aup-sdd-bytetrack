"""CU-01 Registrar orden de servicio (GUI-01): curso básico, RN-01 y RN-03 (asignación)."""

import re
from datetime import date

ID_OP = "op-0000-0001"


def _solicitud(**cambios):
    cuerpo = {
        "id_op": ID_OP,
        "dni": "12345678",
        "equipo_id": None,
        "equipo": None,
        "accesorios": "Cargador",
        "estado_fisico": "Carcasa rayada",
        "falla_reportada": "No enciende",
        "tecnico_id": None,
    }
    cuerpo.update(cambios)
    return cuerpo


def _equipo_nuevo(numero_serie="SN-NUEVO-1"):
    return {"tipo": "Laptop", "marca": "HP", "modelo": "Pavilion", "numero_serie": numero_serie}


def test_cu01_B_crea_orden_equipo_existente(client, crear_cliente, crear_equipo, crear_tecnico, leer):
    """CU-01-B: orden RECEPCIONADO con código OS-AAAA-NNNN (GUI-01), costo de revisión y cola del técnico +1."""
    cliente_id = crear_cliente()
    equipo_id = crear_equipo(cliente_id)
    tecnico_id = crear_tecnico(cola=2)

    respuesta = client.post("/ordenes", json=_solicitud(equipo_id=equipo_id, tecnico_id=tecnico_id))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["reintento"] is False
    orden = cuerpo["orden"]
    assert orden["estado"] == "RECEPCIONADO"
    assert re.fullmatch(rf"OS-{date.today().year}-\d{{4}}", orden["codigo"])
    assert orden["costo_revision"] == "40.00"
    assert orden["tecnico"]["id"] == tecnico_id
    assert orden["equipo"]["id"] == equipo_id
    assert orden["dni"] == "12345678"

    from app.models.entities import Tecnico

    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 3


def test_cu01_B_crea_orden_con_equipo_nuevo(client, crear_cliente, crear_tecnico, leer):
    """CU-01-B: se ingresa un equipo nuevo (tipo, marca, modelo, serie) y queda asociado al cliente."""
    cliente_id = crear_cliente()
    tecnico_id = crear_tecnico()

    respuesta = client.post("/ordenes", json=_solicitud(equipo=_equipo_nuevo(), tecnico_id=tecnico_id))

    assert respuesta.status_code == 201
    from app.models.entities import Equipo

    equipos = leer(lambda s: [(e.numero_serie, e.cliente_id) for e in s.query(Equipo).all()])
    assert equipos == [("SN-NUEVO-1", cliente_id)]


def test_rn01_cliente_con_varios_equipos(client, crear_cliente, crear_equipo, crear_tecnico):
    """RN-01: un cliente puede tener varios equipos, cada uno con serie única."""
    cliente_id = crear_cliente()
    crear_equipo(cliente_id, numero_serie="SN-A")
    tecnico_id = crear_tecnico()

    respuesta = client.post(
        "/ordenes", json=_solicitud(equipo=_equipo_nuevo("SN-B"), tecnico_id=tecnico_id)
    )
    assert respuesta.status_code == 201

    busqueda = client.get("/clientes/12345678").json()
    assert sorted(e["numero_serie"] for e in busqueda["equipos"]) == ["SN-A", "SN-B"]


def test_rn01_serie_en_otro_cliente_rechazada(client, crear_cliente, crear_equipo, crear_tecnico, leer):
    """RN-01: el número de serie es único; no se crea el equipo ni la orden para otro cliente."""
    otro_cliente = crear_cliente(dni="99999999")
    crear_equipo(otro_cliente, numero_serie="SN-COMPARTIDO")
    crear_cliente(dni="12345678")
    tecnico_id = crear_tecnico()

    respuesta = client.post(
        "/ordenes", json=_solicitud(equipo=_equipo_nuevo("SN-COMPARTIDO"), tecnico_id=tecnico_id)
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "SERIE_EN_OTRO_CLIENTE"
    from app.models.entities import Equipo, OrdenServicio

    assert leer(lambda s: s.query(Equipo).count()) == 1
    assert leer(lambda s: s.query(OrdenServicio).count()) == 0


def test_cu01_B_cliente_inexistente_404(client, crear_tecnico):
    tecnico_id = crear_tecnico()
    respuesta = client.post(
        "/ordenes", json=_solicitud(dni="00000000", equipo=_equipo_nuevo(), tecnico_id=tecnico_id)
    )
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "CLIENTE_NO_ENCONTRADO"


def test_cu01_B_campos_obligatorios_422(client, crear_cliente, crear_equipo, crear_tecnico):
    """CU-01-B paso 5: valida los campos obligatorios antes de crear la orden."""
    cliente_id = crear_cliente()
    equipo_id = crear_equipo(cliente_id)
    tecnico_id = crear_tecnico()
    base = _solicitud(equipo_id=equipo_id, tecnico_id=tecnico_id)

    sin_estado_fisico = {k: v for k, v in base.items() if k != "estado_fisico"}
    sin_falla = {k: v for k, v in base.items() if k != "falla_reportada"}
    sin_tecnico = {k: v for k, v in base.items() if k != "tecnico_id"}
    sin_equipo = {**base, "equipo_id": None}
    ambos_equipos = {**base, "equipo": _equipo_nuevo()}
    falla_vacia = {**base, "falla_reportada": "   "}
    equipo_incompleto = {**base, "equipo_id": None, "equipo": {"tipo": "Laptop"}}
    dni_invalido = {**base, "dni": "123"}

    for cuerpo in (
        sin_estado_fisico,
        sin_falla,
        sin_tecnico,
        sin_equipo,
        ambos_equipos,
        falla_vacia,
        equipo_incompleto,
        dni_invalido,
    ):
        assert client.post("/ordenes", json=cuerpo).status_code == 422, cuerpo


def test_rn03_solo_tecnicos_disponibles_en_lista(client, crear_tecnico):
    """RN-03: el selector solo ofrece técnicos disponibles."""
    disponible = crear_tecnico(nombres="Disponible", disponible=True, cola=4)
    crear_tecnico(nombres="Ocupado", disponible=False)

    respuesta = client.get("/tecnicos/disponibles")

    assert respuesta.status_code == 200
    assert [t["id"] for t in respuesta.json()] == [disponible]
    assert set(respuesta.json()[0]) == {"id", "nombres", "apellidos"}


def test_rn03_tecnico_no_disponible_rechazado(client, crear_cliente, crear_equipo, crear_tecnico, leer):
    """RN-03: no se asigna a un técnico no disponible; no queda ningún dato parcial."""
    cliente_id = crear_cliente()
    crear_tecnico(disponible=True)  # existe al menos uno disponible
    ocupado = crear_tecnico(nombres="Ocupado", disponible=False, cola=5)

    respuesta = client.post(
        "/ordenes", json=_solicitud(equipo=_equipo_nuevo(), tecnico_id=ocupado)
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TECNICO_NO_DISPONIBLE"
    from app.models.entities import Equipo, OrdenServicio, Tecnico

    assert leer(lambda s: s.query(OrdenServicio).count()) == 0
    assert leer(lambda s: s.query(Equipo).count()) == 0  # el equipo nuevo no se conserva
    assert leer(lambda s: s.get(Tecnico, ocupado).cola) == 5
    assert cliente_id


def test_rn03_tecnico_inexistente_rechazado(client, crear_cliente, crear_tecnico):
    crear_cliente()
    crear_tecnico()
    respuesta = client.post("/ordenes", json=_solicitud(equipo=_equipo_nuevo(), tecnico_id=9999))
    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "TECNICO_NO_DISPONIBLE"


def test_rn03_sin_tecnicos_disponibles(client, crear_cliente, crear_tecnico, leer):
    """Precondición de CU-01: sin técnicos disponibles no se crea la orden."""
    crear_cliente()
    ocupado = crear_tecnico(disponible=False)

    respuesta = client.post("/ordenes", json=_solicitud(equipo=_equipo_nuevo(), tecnico_id=ocupado))

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "SIN_TECNICOS_DISPONIBLES"
    from app.models.entities import Equipo, OrdenServicio

    assert leer(lambda s: s.query(OrdenServicio).count()) == 0
    assert leer(lambda s: s.query(Equipo).count()) == 0


def test_cu01_B_equipo_de_otro_cliente_no_encontrado(client, crear_cliente, crear_equipo, crear_tecnico):
    otro = crear_cliente(dni="99999999")
    equipo_ajeno = crear_equipo(otro, numero_serie="SN-AJENO")
    crear_cliente(dni="12345678")
    tecnico_id = crear_tecnico()

    respuesta = client.post("/ordenes", json=_solicitud(equipo_id=equipo_ajeno, tecnico_id=tecnico_id))

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "EQUIPO_NO_ENCONTRADO"


def test_cu01_B_consulta_costo_revision_inicial(client, monkeypatch):
    """CU-01-B paso 4: el Recepcionista verifica el costo de revisión inicial (configurable)."""
    assert client.get("/ordenes/costo-revision-inicial").json() == {"costo_revision": "40.00"}

    monkeypatch.setenv("BYTETRACK_COSTO_REVISION", "55.5")
    assert client.get("/ordenes/costo-revision-inicial").json() == {"costo_revision": "55.50"}


def test_cu01_B_codigos_de_orden_correlativos(client, crear_cliente, crear_tecnico):
    crear_cliente()
    tecnico_id = crear_tecnico()
    codigos = []
    for n in range(2):
        r = client.post(
            "/ordenes",
            json=_solicitud(
                id_op=f"op-corr-000{n}", equipo=_equipo_nuevo(f"SN-C{n}"), tecnico_id=tecnico_id
            ),
        )
        assert r.status_code == 201
        codigos.append(r.json()["orden"]["codigo"])
    anio = date.today().year
    assert codigos == [f"OS-{anio}-0001", f"OS-{anio}-0002"]


def test_cu01_B_correlativo_se_reinicia_cada_anio(
    client, crear_cliente, crear_equipo, crear_tecnico, crear_orden, fabrica_sesiones
):
    """CU-01-B: el código OS-AAAA-NNNN numera las órdenes de cada año (GUI-01)."""
    from app.models.entities import OrdenServicio

    cliente_id = crear_cliente()
    equipo_previo = crear_equipo(cliente_id, numero_serie="SN-PREVIO")
    tecnico_id = crear_tecnico()
    crear_orden(equipo_previo, tecnico_id, estado="ENTREGADO")
    with fabrica_sesiones() as s:  # una orden de un año anterior
        s.query(OrdenServicio).update({OrdenServicio.codigo: "OS-2020-0099"})
        s.commit()

    r = client.post(
        "/ordenes",
        json=_solicitud(id_op="op-anio-0001", equipo=_equipo_nuevo("SN-ANIO"), tecnico_id=tecnico_id),
    )

    assert r.json()["orden"]["codigo"] == f"OS-{date.today().year}-0001"


def test_cu01_B_fallo_no_deja_datos_parciales(client, crear_cliente, crear_tecnico, leer, monkeypatch):
    """CU-01-B: la operación es atómica; si falla a mitad no queda equipo, orden ni cola."""
    from app.models.entities import Equipo, OrdenServicio, Tecnico
    from app.repositories import tecnico_repository

    crear_cliente()
    tecnico_id = crear_tecnico(cola=1)

    def _falla(self, tecnico_id):
        raise RuntimeError("fallo simulado al incrementar la cola")

    monkeypatch.setattr(tecnico_repository.TecnicoRepository, "incrementar_cola", _falla)
    client_sin_propagar = type(client)(client.app, raise_server_exceptions=False)

    respuesta = client_sin_propagar.post(
        "/ordenes", json=_solicitud(equipo=_equipo_nuevo(), tecnico_id=tecnico_id)
    )

    assert respuesta.status_code == 500
    assert leer(lambda s: s.query(Equipo).count()) == 0
    assert leer(lambda s: s.query(OrdenServicio).count()) == 0
    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 1
