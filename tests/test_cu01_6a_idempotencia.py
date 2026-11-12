"""CU-01 curso alterno 6a: reintento de confirmación con el mismo ID OP (RN-10, RNF-04)."""

from concurrent.futures import ThreadPoolExecutor

from app.models.entities import OperacionIdempotente, OrdenServicio, Tecnico


def _solicitud(id_op="op-idem-0001", **cambios):
    cuerpo = {
        "id_op": id_op,
        "dni": "12345678",
        "equipo_id": None,
        "equipo": {"tipo": "Laptop", "marca": "Dell", "modelo": "XPS", "numero_serie": "SN-6A"},
        "accesorios": "Cargador",
        "estado_fisico": "Bisagra floja",
        "falla_reportada": "No carga",
        "tecnico_id": None,
    }
    cuerpo.update(cambios)
    return cuerpo


def test_cu01_6a_reintento_devuelve_misma_orden(client, crear_cliente, crear_tecnico, leer):
    """CU-01-6a: el mismo ID OP devuelve la orden ya creada sin duplicar el registro."""
    crear_cliente()
    tecnico_id = crear_tecnico()
    cuerpo = _solicitud(tecnico_id=tecnico_id)

    primera = client.post("/ordenes", json=cuerpo)
    segunda = client.post("/ordenes", json=cuerpo)

    assert primera.status_code == 201
    assert segunda.status_code == 200
    assert primera.json()["reintento"] is False
    assert segunda.json()["reintento"] is True
    assert segunda.json()["orden"] == primera.json()["orden"]
    assert leer(lambda s: s.query(OrdenServicio).count()) == 1


def test_rn10_reintento_no_incrementa_cola(client, crear_cliente, crear_tecnico, leer):
    """RN-10: un reintento no vuelve a incrementar la cola del técnico."""
    crear_cliente()
    tecnico_id = crear_tecnico(cola=3)
    cuerpo = _solicitud(tecnico_id=tecnico_id)

    for _ in range(3):
        client.post("/ordenes", json=cuerpo)

    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 4


def test_rn10_solicitudes_simultaneas_mismo_id_op(client, crear_cliente, crear_tecnico, leer):
    """RN-10: solicitudes simultáneas con el mismo ID OP producen una sola orden y cola +1."""
    crear_cliente()
    tecnico_id = crear_tecnico(cola=0)
    cuerpo = _solicitud(tecnico_id=tecnico_id)

    with ThreadPoolExecutor(max_workers=4) as pool:
        respuestas = list(pool.map(lambda _: client.post("/ordenes", json=cuerpo), range(4)))

    estados = sorted(r.status_code for r in respuestas)
    assert estados == [200, 200, 200, 201]
    assert len({r.json()["orden"]["codigo"] for r in respuestas}) == 1
    assert leer(lambda s: s.query(OrdenServicio).count()) == 1
    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 1


def test_rn10_id_op_con_datos_distintos_rechazado(client, crear_cliente, crear_tecnico, leer):
    """RN-10: reutilizar un ID OP con datos distintos se rechaza sin modificar nada."""
    crear_cliente()
    tecnico_id = crear_tecnico()
    assert client.post("/ordenes", json=_solicitud(tecnico_id=tecnico_id)).status_code == 201

    distinta = _solicitud(tecnico_id=tecnico_id, falla_reportada="Otra falla distinta")
    respuesta = client.post("/ordenes", json=distinta)

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "ID_OP_CONFLICTO"
    assert leer(lambda s: s.query(OrdenServicio).count()) == 1
    assert leer(lambda s: s.get(Tecnico, tecnico_id).cola) == 1


def test_rn10_fallo_no_registra_id_op(client, crear_cliente, crear_tecnico, leer):
    """RN-10: solo se guardan operaciones confirmadas; tras un fallo se puede corregir y reintentar."""
    crear_cliente()
    tecnico_ocupado = crear_tecnico(nombres="Ocupado", disponible=False)
    tecnico_libre = crear_tecnico(nombres="Libre", disponible=True)

    fallida = client.post("/ordenes", json=_solicitud(tecnico_id=tecnico_ocupado))

    assert fallida.status_code == 409
    assert leer(lambda s: s.query(OperacionIdempotente).count()) == 0

    corregida = client.post("/ordenes", json=_solicitud(tecnico_id=tecnico_libre))

    assert corregida.status_code == 201  # mismo id_op, ahora con datos válidos
    assert leer(lambda s: s.query(OperacionIdempotente).count()) == 1


def test_rn10_resultado_guardado_se_devuelve_integro(client, crear_cliente, crear_tecnico, leer):
    """RN-10: el resultado se guarda junto al ID OP y se devuelve tal cual en el reintento."""
    crear_cliente()
    tecnico_id = crear_tecnico()
    cuerpo = _solicitud(tecnico_id=tecnico_id)
    original = client.post("/ordenes", json=cuerpo).json()

    operacion = leer(lambda s: s.get(OperacionIdempotente, cuerpo["id_op"]))
    assert operacion is not None
    assert len(operacion.huella) == 64  # SHA-256 en hexadecimal

    # Aunque cambie la configuración, el reintento devuelve el resultado original guardado.
    import os

    os.environ["BYTETRACK_COSTO_REVISION"] = "99.00"
    try:
        reintento = client.post("/ordenes", json=cuerpo).json()
    finally:
        del os.environ["BYTETRACK_COSTO_REVISION"]
    assert reintento["orden"] == original["orden"]
    assert reintento["orden"]["costo_revision"] == "40.00"
