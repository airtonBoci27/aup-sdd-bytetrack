"""CU-01 curso alterno 5a: el equipo ya tiene una orden activa (alerta E01, RN-02)."""

from concurrent.futures import ThreadPoolExecutor


def _solicitud(id_op, tecnico_id, **cambios):
    cuerpo = {
        "id_op": id_op,
        "dni": "12345678",
        "equipo_id": None,
        "equipo": {"tipo": "Laptop", "marca": "HP", "modelo": "Pavilion", "numero_serie": "SN-5A"},
        "accesorios": None,
        "estado_fisico": "Sin daños visibles",
        "falla_reportada": "Pantalla negra",
        "tecnico_id": tecnico_id,
    }
    cuerpo.update(cambios)
    return cuerpo


def test_cu01_5a_serie_con_orden_activa_muestra_e01(client, crear_cliente, crear_tecnico):
    """CU-01-5a: se bloquea el registro y se muestra E01 con el número de la orden activa."""
    crear_cliente()
    tecnico_id = crear_tecnico()
    primera = client.post("/ordenes", json=_solicitud("op-5a-0001", tecnico_id))
    assert primera.status_code == 201
    codigo_activo = primera.json()["orden"]["codigo"]

    segunda = client.post("/ordenes", json=_solicitud("op-5a-0002", tecnico_id))

    assert segunda.status_code == 409
    cuerpo = segunda.json()
    assert cuerpo["codigo"] == "E01"
    assert cuerpo["mensaje"] == (
        f"Este número de serie ya posee la Orden activa N.° {codigo_activo} en laboratorio"
    )
    assert cuerpo["detalle"]["orden_activa"] == codigo_activo


def test_cu01_5a_equipo_existente_con_orden_activa_bloqueado(
    client, crear_cliente, crear_equipo, crear_tecnico, crear_orden
):
    """CU-01-5a: seleccionar un equipo ya registrado con orden activa también se bloquea."""
    cliente_id = crear_cliente()
    equipo_id = crear_equipo(cliente_id, numero_serie="SN-EXISTENTE")
    tecnico_id = crear_tecnico()
    codigo = crear_orden(equipo_id, tecnico_id, estado="RECEPCIONADO")

    respuesta = client.post(
        "/ordenes", json=_solicitud("op-5a-0003", tecnico_id, equipo=None, equipo_id=equipo_id)
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "E01"
    assert respuesta.json()["detalle"]["orden_activa"] == codigo


def test_rn02_orden_activa_en_cualquier_estado_distinto_de_entregado(
    client, crear_cliente, crear_equipo, crear_tecnico, crear_orden
):
    """RN-02: cualquier estado distinto de ENTREGADO cuenta como orden activa."""
    cliente_id = crear_cliente()
    tecnico_id = crear_tecnico()
    for n, estado in enumerate(("PRESUPUESTADO", "APROBADO", "RECHAZADO", "LISTO")):
        equipo_id = crear_equipo(cliente_id, numero_serie=f"SN-EST-{n}")
        crear_orden(equipo_id, tecnico_id, estado=estado, id_op=f"op-previa-{n}")

        respuesta = client.post(
            "/ordenes",
            json=_solicitud(f"op-est-000{n}", tecnico_id, equipo=None, equipo_id=equipo_id),
        )

        assert respuesta.status_code == 409, estado
        assert respuesta.json()["codigo"] == "E01", estado


def test_rn02_permite_nueva_orden_tras_entregado(
    client, crear_cliente, crear_equipo, crear_tecnico, crear_orden
):
    """RN-02: si la única orden anterior está ENTREGADO, se puede registrar una nueva."""
    cliente_id = crear_cliente()
    equipo_id = crear_equipo(cliente_id, numero_serie="SN-REINGRESO")
    tecnico_id = crear_tecnico()
    crear_orden(equipo_id, tecnico_id, estado="ENTREGADO")

    respuesta = client.post(
        "/ordenes", json=_solicitud("op-reingreso-1", tecnico_id, equipo=None, equipo_id=equipo_id)
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["orden"]["estado"] == "RECEPCIONADO"


def test_cu01_5a_bloqueo_no_incrementa_cola(client, crear_cliente, crear_tecnico, leer):
    """CU-01-5a: el bloqueo por E01 no modifica la cola del técnico ni crea otra orden."""
    from app.models.entities import OrdenServicio, Tecnico

    crear_cliente()
    tecnico_id = crear_tecnico(cola=0)
    assert client.post("/ordenes", json=_solicitud("op-5a-0010", tecnico_id)).status_code == 201
    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 1

    bloqueada = client.post("/ordenes", json=_solicitud("op-5a-0011", tecnico_id))

    assert bloqueada.status_code == 409
    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 1
    assert leer(lambda s: s.query(OrdenServicio).count()) == 1


def test_rn02_concurrencia_misma_serie(client, crear_cliente, crear_tecnico, leer):
    """RN-02: dos solicitudes simultáneas para la misma serie (ID OP distintos) dejan una sola orden."""
    from app.models.entities import OrdenServicio, Tecnico

    crear_cliente()
    tecnico_id = crear_tecnico()

    def _enviar(n):
        return client.post("/ordenes", json=_solicitud(f"op-conc-000{n}", tecnico_id))

    with ThreadPoolExecutor(max_workers=2) as pool:
        respuestas = list(pool.map(_enviar, range(2)))

    estados = sorted(r.status_code for r in respuestas)
    assert estados == [201, 409]
    bloqueada = next(r for r in respuestas if r.status_code == 409)
    assert bloqueada.json()["codigo"] == "E01"
    assert leer(lambda s: s.query(OrdenServicio).count()) == 1
    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 1
