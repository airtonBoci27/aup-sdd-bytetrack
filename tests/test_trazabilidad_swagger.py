"""Principio I de la constitución: cada operación declara su CU/pantalla y cita sus RN en Swagger."""

import re

from app.main import app

ETIQUETA = re.compile(r"^CU-\d{2} · (GUI-\d{2}|Acceso \(RNF-02\))$")
ETIQUETA_ACCESO = "CU-01 · Acceso (RNF-02)"
METODOS = {"get", "post", "put", "patch", "delete"}

# Reglas que debe citar la descripción de cada operación (método, ruta).
REGLAS_ESPERADAS = {
    ("get", "/clientes/{dni}"): {"RN-01", "RNF-02"},
    ("get", "/clientes"): {"RN-01", "RNF-02"},
    ("post", "/clientes"): {"RN-01", "RNF-02"},
    ("get", "/tecnicos/disponibles"): {"RN-03", "RNF-02"},
    ("get", "/tecnicos/resumen"): {"RN-03", "RNF-02"},
    ("get", "/ordenes/costo-revision-inicial"): {"RNF-02"},
    ("post", "/ordenes"): {"RN-01", "RN-02", "RN-03", "RN-10", "RNF-02"},
    ("get", "/ordenes"): {"RN-03", "RNF-02"},
    ("get", "/ordenes/resumen"): {"RNF-02"},
    ("get", "/ordenes/{codigo}"): {"RN-03", "RNF-02"},
    ("get", "/repuestos"): {"RN-04", "RNF-02"},
    ("post", "/ordenes/{codigo}/diagnostico"): {"RN-03", "RN-04", "RN-10", "RNF-01", "RNF-02"},
    ("post", "/ordenes/{codigo}/decision"): {"RN-05", "RN-06", "RN-10", "RNF-02"},
    ("post", "/ordenes/{codigo}/finalizar"): {"RN-03", "RN-07", "RN-10", "RNF-02"},
    ("post", "/ordenes/{codigo}/liquidar"): {"RN-08", "RN-09", "RN-10", "RN-11", "RNF-01", "RNF-02"},
    ("post", "/auth/token"): {"CU-01", "RNF-02"},
    ("post", "/auth/logout"): {"CU-01", "RNF-02"},
}

OPERACIONES_PROTEGIDAS = [
    ("get", "/clientes/{dni}"),
    ("post", "/clientes"),
    ("get", "/tecnicos/disponibles"),
    ("get", "/ordenes/costo-revision-inicial"),
    ("post", "/ordenes"),
    ("get", "/ordenes"),
    ("get", "/repuestos"),
    ("post", "/ordenes/{codigo}/diagnostico"),
    ("post", "/ordenes/{codigo}/decision"),
    ("post", "/ordenes/{codigo}/finalizar"),
    ("post", "/ordenes/{codigo}/liquidar"),
]


def _operaciones():
    for ruta, metodos in app.openapi()["paths"].items():
        for metodo, operacion in metodos.items():
            if metodo in METODOS:
                yield metodo, ruta, operacion


def test_cada_operacion_declara_su_cu_y_pantalla():
    operaciones = list(_operaciones())
    assert len(operaciones) == 17
    for metodo, ruta, operacion in operaciones:
        etiquetas = operacion.get("tags", [])
        assert etiquetas, f"{metodo} {ruta} sin etiqueta"
        assert all(ETIQUETA.match(e) for e in etiquetas), (metodo, ruta, etiquetas)


def test_cada_operacion_cita_las_reglas_que_valida():
    for (metodo, ruta), reglas in REGLAS_ESPERADAS.items():
        operacion = app.openapi()["paths"][ruta][metodo]
        descripcion = operacion["description"]
        for regla in reglas:
            assert regla in descripcion, f"{metodo} {ruta} no cita {regla}"


def test_las_etiquetas_corresponden_a_los_codigos_del_proyecto():
    etiquetas = {t["name"] for t in app.openapi()["tags"]}
    assert etiquetas == {
        "CU-05 · GUI-01",
        "CU-06 · GUI-02",
        "CU-01 · GUI-01",
        ETIQUETA_ACCESO,
        "CU-07 · GUI-03",
        "CU-02 · GUI-03",
        "CU-03 · GUI-04",
        "CU-08 · GUI-05",
        "CU-04 · GUI-06",
    }


def test_las_operaciones_de_acceso_llevan_la_etiqueta_de_acceso():
    paths = app.openapi()["paths"]
    for ruta in ("/auth/token", "/auth/logout"):
        assert paths[ruta]["post"]["tags"] == [ETIQUETA_ACCESO]


def test_las_operaciones_protegidas_declaran_401_y_403():
    """RNF-02: el esquema OpenAPI documenta los rechazos por sesión y por rol."""
    paths = app.openapi()["paths"]
    for metodo, ruta in OPERACIONES_PROTEGIDAS:
        respuestas = paths[ruta][metodo]["responses"]
        assert "401" in respuestas and "403" in respuestas, (metodo, ruta)
