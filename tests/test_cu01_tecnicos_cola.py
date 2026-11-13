"""CU-01 paso 6 / RN-03: la lista de técnicos disponibles incluye la cola de cada técnico (solo lectura).

La interfaz (GUI-01) muestra «[nombres] [apellidos] ([N] en cola)». La cola ya existe en el técnico;
este cambio no altera qué técnicos se devuelven ni ninguna regla.
"""


def _orden(tecnico_id, serie="SN-COLA-1", id_op="op-cola-0001"):
    return {
        "id_op": id_op,
        "dni": "12345678",
        "equipo_id": None,
        "equipo": {"tipo": "Laptop", "marca": "Dell", "modelo": "XPS", "numero_serie": serie},
        "accesorios": None,
        "estado_fisico": "Sin daños",
        "falla_reportada": "No enciende",
        "tecnico_id": tecnico_id,
    }


def test_rn03_tecnicos_disponibles_incluye_cola(client, crear_tecnico):
    """RN-03 / CU-01 paso 6: cada elemento trae id, nombres, apellidos y cola."""
    primero = crear_tecnico("Luis", "Rojas", cola=2)
    segundo = crear_tecnico("Carla", "Mendoza", cola=0)

    respuesta = client.get("/tecnicos/disponibles")

    assert respuesta.status_code == 200
    assert respuesta.json() == [
        {"id": primero, "nombres": "Luis", "apellidos": "Rojas", "cola": 2},
        {"id": segundo, "nombres": "Carla", "apellidos": "Mendoza", "cola": 0},
    ]
    assert all(isinstance(t["cola"], int) for t in respuesta.json())


def test_rn03_cola_refleja_la_orden_recien_generada(client, crear_cliente, crear_tecnico):
    """CU-01 paso 6: tras generar la orden, la cola del técnico sube en 1."""
    crear_cliente()
    tecnico_id = crear_tecnico(cola=3)

    assert client.post("/ordenes", json=_orden(tecnico_id)).status_code == 201

    [tecnico] = client.get("/tecnicos/disponibles").json()
    assert tecnico["cola"] == 4


def test_rn03_el_conjunto_de_tecnicos_devueltos_no_cambia(client, crear_tecnico):
    """RN-03: solo se ofrecen técnicos con disponible = true; lista vacía si no hay ninguno."""
    assert client.get("/tecnicos/disponibles").json() == []
    crear_tecnico("Jorge", "Paredes", disponible=False, cola=5)
    assert client.get("/tecnicos/disponibles").json() == []
    disponible = crear_tecnico("Luis", "Rojas", disponible=True, cola=1)
    ids = [t["id"] for t in client.get("/tecnicos/disponibles").json()]
    assert ids == [disponible]
