"""CU-05 Buscar cliente (GUI-01): pasos 1-2 de CU-01, curso 2a y RN-01."""


def test_cu01_B_busca_cliente_con_equipos(client, crear_cliente, crear_equipo):
    """CU-01-B (CU-05): muestra los datos del cliente y carga sus equipos en el selector."""
    cliente_id = crear_cliente(dni="12345678", nombres="Ana", apellidos="Quispe", telefono="999111222")
    crear_equipo(cliente_id, numero_serie="SN-A")
    crear_equipo(cliente_id, numero_serie="SN-B", tipo="Celular", marca="Samsung", modelo="S21")

    respuesta = client.get("/clientes/12345678")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["cliente"] == {
        "dni": "12345678",
        "nombres": "Ana",
        "apellidos": "Quispe",
        "telefono": "999111222",
        "correo": None,
    }
    assert sorted(e["numero_serie"] for e in cuerpo["equipos"]) == ["SN-A", "SN-B"]


def test_cu01_B_cliente_sin_equipos_lista_vacia(client, crear_cliente):
    """CU-01-B (CU-05): un cliente sin equipos devuelve el selector vacío."""
    crear_cliente(dni="87654321")

    respuesta = client.get("/clientes/87654321")

    assert respuesta.status_code == 200
    assert respuesta.json()["equipos"] == []


def test_cu01_2a_dni_inexistente_habilita_registro(client):
    """CU-01-2a (CU-05): un DNI inexistente habilita «Registrar nuevo cliente»."""
    respuesta = client.get("/clientes/11112222")

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "CLIENTE_NO_ENCONTRADO"
    assert cuerpo["detalle"]["habilitar_registro"] is True


def test_rn01_dni_debe_tener_8_digitos(client):
    """RN-01: el DNI debe ser numérico de exactamente 8 dígitos."""
    for dni in ("1234567", "123456789", "1234567a", "abcdefgh"):
        respuesta = client.get(f"/clientes/{dni}")
        assert respuesta.status_code == 422, dni
