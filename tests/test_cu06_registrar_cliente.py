"""CU-06 Registrar nuevo cliente (GUI-02): cursos 2a y 2b de CU-01, RN-01."""

from concurrent.futures import ThreadPoolExecutor

from app.models.entities import Cliente

CLIENTE = {
    "dni": "45678912",
    "nombres": "María",
    "apellidos": "Torres",
    "telefono": "987654321",
    "correo": "maria@example.com",
}


def test_cu01_2a_registra_cliente_nuevo_201(client, leer):
    """CU-01-2a: el cliente nuevo se registra y GUI-01 recibe sus datos para continuar."""
    respuesta = client.post("/clientes", json=CLIENTE)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["ya_registrado"] is False
    assert cuerpo["aviso"] is None
    assert cuerpo["cliente"]["dni"] == "45678912"
    assert cuerpo["equipos"] == []
    assert leer(lambda s: s.query(Cliente).count()) == 1
    # Luego de guardarlo, la búsqueda (CU-05) lo encuentra.
    assert client.get("/clientes/45678912").status_code == 200


def test_cu01_2a_correo_opcional(client):
    """CU-01-2a: el correo es opcional."""
    sin_correo = {k: v for k, v in CLIENTE.items() if k != "correo"}

    respuesta = client.post("/clientes", json=sin_correo)

    assert respuesta.status_code == 201
    assert respuesta.json()["cliente"]["correo"] is None


def test_cu01_2a_correo_vacio_se_normaliza_y_correo_invalido_422(client, leer):
    """CU-01-2a: correo en blanco se guarda como None y un formato inválido devuelve 422."""
    assert client.post("/clientes", json={**CLIENTE, "correo": "correo-invalido"}).status_code == 422
    assert leer(lambda s: s.query(Cliente).count()) == 0

    respuesta = client.post("/clientes", json={**CLIENTE, "correo": "   "})
    assert respuesta.status_code == 201
    assert respuesta.json()["cliente"]["correo"] is None


def test_cu01_2a_campos_obligatorios_y_dni_invalido_422(client, leer):
    """CU-01-2a / RN-01: sin campos obligatorios o con DNI inválido no se registra nada."""
    casos = [
        {k: v for k, v in CLIENTE.items() if k != "nombres"},
        {k: v for k, v in CLIENTE.items() if k != "apellidos"},
        {k: v for k, v in CLIENTE.items() if k != "telefono"},
        {**CLIENTE, "nombres": "   "},
        {**CLIENTE, "dni": "1234567"},
        {**CLIENTE, "dni": "123456789"},
        {**CLIENTE, "dni": "1234567a"},
    ]
    for cuerpo in casos:
        assert client.post("/clientes", json=cuerpo).status_code == 422, cuerpo
    assert leer(lambda s: s.query(Cliente).count()) == 0


def test_cu01_2b_dni_existente_avisa_y_carga_cliente(client, crear_cliente, crear_equipo):
    """CU-01-2b: «El DNI ya está registrado» y se carga al cliente existente sin duplicarlo."""
    cliente_id = crear_cliente(dni="45678912", nombres="Original", apellidos="Existente", telefono="111")
    crear_equipo(cliente_id, numero_serie="SN-EXIST")

    respuesta = client.post("/clientes", json=CLIENTE)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ya_registrado"] is True
    assert cuerpo["aviso"] == "El DNI ya está registrado"
    assert cuerpo["cliente"]["nombres"] == "Original"  # no se modifica el cliente existente
    assert [e["numero_serie"] for e in cuerpo["equipos"]] == ["SN-EXIST"]


def test_rn01_dni_unico_sin_duplicados(client, leer):
    """RN-01: guardar dos veces el mismo DNI deja un único cliente."""
    assert client.post("/clientes", json=CLIENTE).status_code == 201
    assert client.post("/clientes", json=CLIENTE).status_code == 200

    assert leer(lambda s: s.query(Cliente).count()) == 1


def test_cu01_2b_doble_guardado_concurrente_no_duplica(client, leer):
    """CU-01-2b / RN-01: dos guardados simultáneos con el mismo DNI dejan un solo cliente."""

    def _guardar(_):
        return client.post("/clientes", json=CLIENTE)

    with ThreadPoolExecutor(max_workers=2) as pool:
        respuestas = list(pool.map(_guardar, range(2)))

    assert sorted(r.status_code for r in respuestas) == [200, 201]
    assert leer(lambda s: s.query(Cliente).count()) == 1
