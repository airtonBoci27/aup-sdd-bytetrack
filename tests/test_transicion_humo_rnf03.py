"""Pruebas automatizadas de la Fase de Transición (specs/004-transicion-despliegue):
1. Prueba de humo e idempotencia de ``app.seed`` de punta a punta.
2. Benchmark de concurrencia y rendimiento ``RNF-03`` (5 sesiones concurrentes, 100 intentos de
   reserva sobre stock libre limitado: p95 <= 1.0 s y atomicidad exacta ``RNF-01``).
"""

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import secrets
import time

from fastapi.testclient import TestClient

from app import database, seed
from app.main import app
from app.models.entities import Repuesto, Usuario


def test_transicion_humo_seed_idempotente_y_salud_integral(tmp_path, monkeypatch):
    """Ejecuta app.seed dos veces sobre una BD limpia y verifica web, API, roles y datos iniciales."""
    ruta_db = tmp_path / "transicion_humo.db"
    clave_rec = secrets.token_urlsafe(16)
    clave_tec = secrets.token_urlsafe(16)

    monkeypatch.setenv("BYTETRACK_DB_PATH", str(ruta_db))
    monkeypatch.setenv("BYTETRACK_RECEPCIONISTA_CLAVE", clave_rec)
    monkeypatch.setenv("BYTETRACK_TECNICO_CLAVE", clave_tec)

    database.obtener_fabrica_sesiones.cache_clear()
    database.obtener_motor.cache_clear()
    try:
        # Primera ejecución de semilla: crea usuarios, 3 técnicos, 8 repuestos y 5 clientes (7 órdenes)
        assert seed.main() == 0
        # Segunda ejecución: idempotente (0 técnicos nuevos, 0 clientes duplicados)
        assert seed.cargar_tecnicos() == 0
        assert seed.cargar_datos_demo() == 0

        with TestClient(app) as cliente_pub:
            assert cliente_pub.get("/").status_code == 200
            assert cliente_pub.get("/docs").status_code == 200

            tok_rec = cliente_pub.post(
                "/auth/token", data={"username": "recepcion", "password": clave_rec}
            )
            assert tok_rec.status_code == 200
            headers_rec = {"Authorization": f"Bearer {tok_rec.json()['access_token']}"}

            tok_tec = cliente_pub.post(
                "/auth/token", data={"username": "tecnico", "password": clave_tec}
            )
            assert tok_tec.status_code == 200
            headers_tec = {"Authorization": f"Bearer {tok_tec.json()['access_token']}"}

            resumen = cliente_pub.get("/ordenes/resumen", headers=headers_rec)
            assert resumen.status_code == 200
            assert resumen.json()["total_ordenes"] == 7

            almacen = cliente_pub.get("/repuestos?solo_con_stock=false&limit=20", headers=headers_rec)
            assert almacen.status_code == 200
            assert almacen.json()["total"] == 8

            # RN-03: el Técnico solo visualiza sus órdenes asignadas (menos que el total de 7)
            ordenes_tec = cliente_pub.get("/ordenes?limit=20", headers=headers_tec)
            assert ordenes_tec.status_code == 200
            assert 0 < ordenes_tec.json()["total"] < 7
    finally:
        database.obtener_motor().dispose()
        database.obtener_fabrica_sesiones.cache_clear()
        database.obtener_motor.cache_clear()


def test_rnf03_rendimiento_y_atomicidad_5_sesiones_100_intentos(
    _bd_de_prueba,
    fabrica_sesiones,
    crear_usuario,
    iniciar_sesion,
    crear_cliente,
    crear_equipo,
    crear_tecnico,
    crear_orden,
    leer,
):
    """RNF-03 + RNF-01: 5 sesiones concurrentes y 100 intentos de reserva con p95 <= 1.0 s."""
    cliente_id = crear_cliente(dni="65432198", nombres="Elena", apellidos="Vargas")

    # 40 unidades físicas disponibles para 100 solicitudes concurrentes -> exactamente 40 éxitos y 60 E02
    with fabrica_sesiones() as s:
        rep = Repuesto(
            sku="SKU-RNF03-RAM",
            nombre="RAM 16GB Prueba RNF-03",
            stock_disponible=40,
            stock_reservado=0,
            precio_unitario=Decimal("150.00"),
        )
        s.add(rep)
        s.commit()
        rep_id = rep.id

    sesiones_tecnicos: list[tuple[str, list[str]]] = []
    contador_serie = 0
    for idx in range(5):
        tec_id = crear_tecnico(nombres=f"Tec{idx}", apellidos="Lab")
        nombre_usr = f"tecnico_rnf03_{idx}"
        crear_usuario(nombre_usr, "TECNICO")
        with fabrica_sesiones() as s:
            s.query(Usuario).filter_by(nombre_usuario=nombre_usr).update({Usuario.tecnico_id: tec_id})
            s.commit()
        token = iniciar_sesion(TestClient(app), nombre_usr, "TECNICO")

        codigos_tec: list[str] = []
        for _ in range(20):
            contador_serie += 1
            eq_id = crear_equipo(cliente_id, numero_serie=f"SN-RNF03-{contador_serie:04d}")
            codigo = crear_orden(
                eq_id, tec_id, estado="RECEPCIONADO", id_op=f"op-base-rnf03-{contador_serie:04d}"
            )
            codigos_tec.append(codigo)
        sesiones_tecnicos.append((token, codigos_tec))

    def _ejecutar_lote(lote: tuple[str, list[str]]) -> list[tuple[int, float]]:
        token, codigos = lote
        resultados_locales: list[tuple[int, float]] = []
        with TestClient(app, headers={"Authorization": f"Bearer {token}"}) as cli:
            for codigo in codigos:
                t0 = time.perf_counter()
                resp = cli.post(
                    f"/ordenes/{codigo}/diagnostico",
                    json={
                        "id_op": f"op-diag-{codigo}",
                        "informe_tecnico": "Prueba concurrente RNF-03",
                        "costo_mano_obra": "60.00",
                        "repuestos": [{"repuesto_id": rep_id, "cantidad": 1}],
                    },
                )
                duracion = time.perf_counter() - t0
                resultados_locales.append((resp.status_code, duracion))
        return resultados_locales

    with ThreadPoolExecutor(max_workers=5) as pool:
        lotes = list(pool.map(_ejecutar_lote, sesiones_tecnicos))

    todos = [item for sub in lotes for item in sub]
    assert len(todos) == 100

    exitos_201 = sum(1 for codigo_http, _ in todos if codigo_http == 201)
    conflictos_409 = sum(1 for codigo_http, _ in todos if codigo_http == 409)
    assert exitos_201 == 40, f"Se esperaban 40 reservas exactas, se obtuvieron {exitos_201}"
    assert conflictos_409 == 60, f"Se esperaban 60 rechazos E02, se obtuvieron {conflictos_409}"

    # RNF-01: integridad exacta de inventario sin stock libre negativo
    disp, resv = leer(lambda s: (s.get(Repuesto, rep_id).stock_disponible, s.get(Repuesto, rep_id).stock_reservado))
    assert (disp, resv) == (40, 40)

    # RNF-03: percentil 95 <= 1.0 segundo en 100 intentos con 5 sesiones concurrentes
    latencias = sorted(dur for _, dur in todos)
    p95 = latencias[94]
    assert p95 <= 1.0, f"RNF-03 incumplido: p95 = {p95:.4f}s (> 1.0s)"
