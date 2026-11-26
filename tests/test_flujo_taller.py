"""Pruebas integradas del ciclo completo del taller: seguimiento paginado, CU-07, CU-02, CU-03, CU-08 y CU-04."""

from decimal import Decimal
import re

from app.models.entities import Repuesto, Usuario


def _crear_repuesto(fabrica_sesiones, sku, nombre, stock_disponible, stock_reservado=0, precio="100.00"):
    with fabrica_sesiones() as s:
        rep = Repuesto(
            sku=sku,
            nombre=nombre,
            stock_disponible=stock_disponible,
            stock_reservado=stock_reservado,
            precio_unitario=Decimal(precio),
        )
        s.add(rep)
        s.commit()
        return rep.id


def test_flujo_completo_cu01_cu02_cu03_cu08_cu04(
    client, client_tecnico, crear_cliente, crear_equipo, crear_tecnico, fabrica_sesiones, leer
):
    """Recorre todo el ciclo AUP: RECEPCIONADO → PRESUPUESTADO → APROBADO → LISTO → ENTREGADO."""
    cliente_id = crear_cliente(dni="45678912")
    equipo_id = crear_equipo(cliente_id, numero_serie="SN-FLUJO-01")
    tecnico_id = crear_tecnico(nombres="Luis", apellidos="Rojas")
    with fabrica_sesiones() as s:
        s.query(Usuario).filter_by(nombre_usuario="tecnico").update({Usuario.tecnico_id: tecnico_id})
        s.commit()

    rep_id = _crear_repuesto(fabrica_sesiones, "SKU-SSD-1", "SSD 512GB", 3, 0, "200.00")

    # 1. CU-01 Recepcionista crea orden
    r1 = client.post(
        "/ordenes",
        json={
            "id_op": "op-flujo-1",
            "dni": "45678912",
            "equipo_id": equipo_id,
            "accesorios": "Cargador",
            "estado_fisico": "Sin golpes",
            "falla_reportada": "No arranca",
            "tecnico_id": tecnico_id,
        },
    )
    assert r1.status_code == 201
    codigo = r1.json()["orden"]["codigo"]

    # 2. CU-07 Consulta de repuestos paginados; Recepcionista puede consultar almacén pero NO emitir diagnóstico (RNF-02)
    assert client.get("/repuestos").status_code == 200
    assert (
        client.post(
            f"/ordenes/{codigo}/diagnostico",
            json={"id_op": "op-no-rol", "informe_tecnico": "x", "costo_mano_obra": "10.00"},
        ).status_code
        == 403
    )
    r_rep = client_tecnico.get("/repuestos?q=SSD&page=1&limit=5")
    assert r_rep.status_code == 200
    assert r_rep.json()["total"] == 1
    assert r_rep.json()["items"][0]["stock_libre"] == 3

    # 3. CU-02 Técnico emite diagnóstico y reserva atómica (RN-04)
    r2 = client_tecnico.post(
        f"/ordenes/{codigo}/diagnostico",
        json={
            "id_op": "op-diag-1",
            "informe_tecnico": "Disco dañado",
            "costo_mano_obra": "100.00",
            "repuestos": [{"repuesto_id": rep_id, "cantidad": 2}],
        },
    )
    assert r2.status_code == 201
    assert r2.json()["orden"]["estado"] == "PRESUPUESTADO"
    assert r2.json()["orden"]["diagnostico"]["total_presupuesto"] == "500.00"
    assert leer(lambda s: s.get(Repuesto, rep_id).stock_reservado) == 2

    # Idempotencia CU-02 (RN-10)
    r2_dup = client_tecnico.post(
        f"/ordenes/{codigo}/diagnostico",
        json={
            "id_op": "op-diag-1",
            "informe_tecnico": "Disco dañado",
            "costo_mano_obra": "100.00",
            "repuestos": [{"repuesto_id": rep_id, "cantidad": 2}],
        },
    )
    assert r2_dup.status_code == 200
    assert r2_dup.json()["reintento"] is True
    assert leer(lambda s: s.get(Repuesto, rep_id).stock_reservado) == 2

    # 4. CU-03 Recepcionista registra aprobación (RN-05, RN-06)
    r3 = client.post(
        f"/ordenes/{codigo}/decision",
        json={
            "id_op": "op-dec-1",
            "decision": "APROBADO",
            "canal": "WHATSAPP",
            "evidencia": "Cliente confirmó presupuesto por WhatsApp.",
        },
    )
    assert r3.status_code == 200
    assert r3.json()["orden"]["estado"] == "APROBADO"
    assert leer(lambda s: s.get(Repuesto, rep_id).stock_reservado) == 2

    # 5. CU-08 Técnico finaliza reparación (RN-07: exige prueba_conforme=True)
    r4_fail = client_tecnico.post(
        f"/ordenes/{codigo}/finalizar",
        json={
            "id_op": "op-fin-fail",
            "trabajo_realizado": "Cambio de SSD",
            "prueba_conforme": False,
            "resultado_prueba": "Pendiente",
        },
    )
    assert r4_fail.status_code == 422
    assert r4_fail.json()["codigo"] == "PRUEBA_NO_CONFORME"

    r4 = client_tecnico.post(
        f"/ordenes/{codigo}/finalizar",
        json={
            "id_op": "op-fin-1",
            "trabajo_realizado": "Cambio de SSD e instalación de SO",
            "prueba_conforme": True,
            "resultado_prueba": "Arranque correcto en 12 segundos",
        },
    )
    assert r4.status_code == 200
    assert r4.json()["orden"]["estado"] == "LISTO"
    # Repuestos consumidos definitivamente (3 - 2 = 1 disponible, 0 reservado)
    assert leer(lambda s: (s.get(Repuesto, rep_id).stock_disponible, s.get(Repuesto, rep_id).stock_reservado)) == (1, 0)

    # 6. CU-04 Recepcionista liquida y entrega (RN-08, RN-09, RN-10)
    r5_parcial = client.post(
        f"/ordenes/{codigo}/liquidar",
        json={
            "id_op": "op-cob-parcial",
            "metodo_pago": "EFECTIVO",
            "monto_recibido": "200.00",
            "conformidad_entrega": True,
        },
    )
    assert r5_parcial.status_code == 422
    assert r5_parcial.json()["codigo"] == "MONTO_INCOMPLETO"

    r5 = client.post(
        f"/ordenes/{codigo}/liquidar",
        json={
            "id_op": "op-cob-1",
            "metodo_pago": "TARJETA",
            "monto_recibido": "500.00",
            "conformidad_entrega": True,
        },
    )
    assert r5.status_code == 201
    assert r5.json()["orden"]["estado"] == "ENTREGADO"
    assert re.fullmatch(r"CP-\d{4}-\d{4}", r5.json()["comprobante"]["numero"])


def test_cu02_e02_reserva_atomica_todo_o_nada_y_cu03_rechazo_libera_stock(
    client, client_tecnico, crear_cliente, crear_equipo, crear_tecnico, crear_orden, fabrica_sesiones, leer
):
    """RN-04 (E02 todo o nada) y RN-06 (rechazo libera stock reservado inmediatamente)."""
    cliente_id = crear_cliente(dni="72345678")
    eq1 = crear_equipo(cliente_id, numero_serie="SN-E02-1")
    tec_id = crear_tecnico()
    with fabrica_sesiones() as s:
        s.query(Usuario).filter_by(nombre_usuario="tecnico").update({Usuario.tecnico_id: tec_id})
        s.commit()

    codigo = crear_orden(eq1, tec_id, estado="RECEPCIONADO", id_op="op-e02-base")
    rep_ok = _crear_repuesto(fabrica_sesiones, "SKU-OK", "Pasta térmica", 5, 0, "30.00")
    rep_agotado = _crear_repuesto(fabrica_sesiones, "SKU-LOW", "Pantalla", 1, 1, "300.00")

    # E02: rep_ok tiene stock pero rep_agotado tiene 0 libre -> NO reserva ninguno
    r_e02 = client_tecnico.post(
        f"/ordenes/{codigo}/diagnostico",
        json={
            "id_op": "op-diag-e02",
            "informe_tecnico": "Cambio de pantalla",
            "costo_mano_obra": "80.00",
            "repuestos": [
                {"repuesto_id": rep_ok, "cantidad": 2},
                {"repuesto_id": rep_agotado, "cantidad": 1},
            ],
        },
    )
    assert r_e02.status_code == 409
    assert r_e02.json()["codigo"] == "E02"
    assert leer(lambda s: s.get(Repuesto, rep_ok).stock_reservado) == 0

    # Emite solo con rep_ok y luego el cliente rechaza -> libera stock (RN-06)
    r_ok = client_tecnico.post(
        f"/ordenes/{codigo}/diagnostico",
        json={
            "id_op": "op-diag-ok",
            "informe_tecnico": "Mantenimiento",
            "costo_mano_obra": "80.00",
            "repuestos": [{"repuesto_id": rep_ok, "cantidad": 2}],
        },
    )
    assert r_ok.status_code == 201
    assert leer(lambda s: s.get(Repuesto, rep_ok).stock_reservado) == 2

    r_rech = client.post(
        f"/ordenes/{codigo}/decision",
        json={
            "id_op": "op-dec-rech",
            "decision": "RECHAZADO",
            "canal": "PRESENCIAL",
            "evidencia": "Cliente rechaza presupuesto en mostrador.",
        },
    )
    assert r_rech.status_code == 200
    assert r_rech.json()["orden"]["estado"] == "RECHAZADO"
    assert leer(lambda s: s.get(Repuesto, rep_ok).stock_reservado) == 0


def test_listado_paginado_y_resumen_del_taller(
    client, crear_cliente, crear_equipo, crear_tecnico, crear_orden
):
    """Verifica paginación y resumen de estados del panel del taller."""
    c_id = crear_cliente(dni="10293847")
    t_id = crear_tecnico()
    for i in range(4):
        eq_id = crear_equipo(c_id, numero_serie=f"SN-PAG-{i}")
        crear_orden(eq_id, t_id, estado="RECEPCIONADO", id_op=f"op-pag-{i}")

    p1 = client.get("/ordenes?page=1&limit=2")
    assert p1.status_code == 200
    assert p1.json()["total"] == 4
    assert p1.json()["total_pages"] == 2
    assert len(p1.json()["items"]) == 2

    resumen = client.get("/ordenes/resumen")
    assert resumen.status_code == 200
    assert resumen.json()["total_ordenes"] == 4
    assert resumen.json()["por_estado"]["RECEPCIONADO"] == 4


def test_devolucion_rechazado_rn11_directorio_clientes_y_carga_tecnicos(
    client, client_tecnico, crear_cliente, crear_equipo, crear_tecnico, crear_orden
):
    """RN-11 (devolución de equipo RECHAZADO cobrando revisión), GET /clientes y GET /tecnicos/resumen."""
    c_id = crear_cliente(dni="87654321", nombres="Pedro", apellidos="Gómez")
    eq_id = crear_equipo(c_id, numero_serie="SN-RECH-01")
    t_id = crear_tecnico(nombres="Luis", apellidos="Rojas", disponible=True, cola=2)
    codigo = crear_orden(eq_id, t_id, estado="RECHAZADO", id_op="op-rech-base")

    # Directorio paginado de clientes (solo Recepcionista)
    assert client_tecnico.get("/clientes").status_code == 403
    r_cli = client.get("/clientes?q=Pedro&page=1&limit=6")
    assert r_cli.status_code == 200
    assert r_cli.json()["total"] == 1
    assert r_cli.json()["items"][0]["equipos"][0]["numero_serie"] == "SN-RECH-01"

    # Carga de técnicos
    r_tec = client.get("/tecnicos/resumen")
    assert r_tec.status_code == 200
    assert r_tec.json()[0]["cola"] == 2

    # RN-11: liquidar orden RECHAZADO con el costo de revisión (S/ 40.00) pasa a ENTREGADO y libera serie
    r_dev = client.post(
        f"/ordenes/{codigo}/liquidar",
        json={
            "id_op": "op-dev-rn11",
            "metodo_pago": "EFECTIVO",
            "monto_recibido": "40.00",
            "conformidad_entrega": True,
        },
    )
    assert r_dev.status_code == 201
    assert r_dev.json()["orden"]["estado"] == "ENTREGADO"
    assert r_dev.json()["comprobante"]["monto_total"] == "40.00"

    # Ahora la serie queda liberada para una nueva orden (RN-02)
    r_nueva = client.post(
        "/ordenes",
        json={
            "id_op": "op-reingreso-1",
            "dni": "87654321",
            "equipo_id": eq_id,
            "estado_fisico": "Buen estado",
            "falla_reportada": "Reingreso tras devolución",
            "tecnico_id": t_id,
        },
    )
    assert r_nueva.status_code == 201
