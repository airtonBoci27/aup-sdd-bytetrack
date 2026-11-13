"""Principio I de la constitución: cada operación declara su CU/pantalla y cita sus RN en Swagger."""

import re

from app.main import app

ETIQUETA = re.compile(r"^CU-\d{2} · (GUI-\d{2}|Acceso \(RNF-02\))$")
ETIQUETA_ACCESO = "CU-01 · Acceso (RNF-02)"
METODOS = {"get", "post", "put", "patch", "delete"}

# Reglas que debe citar la descripción de cada operación (método, ruta).
REGLAS_ESPERADAS = {
    ("get", "/clientes/{dni}"): {"RN-01", "RNF-02"},
    ("post", "/clientes"): {"RN-01", "RNF-02"},
    ("get", "/tecnicos/disponibles"): {"RN-03", "RNF-02"},
    ("get", "/ordenes/costo-revision-inicial"): {"RNF-02"},
    ("post", "/ordenes"): {"RN-01", "RN-02", "RN-03", "RN-10", "RNF-02"},
    # RNF-02: las operaciones de acceso citan la precondición de CU-01 y el requisito.
    ("post", "/auth/token"): {"CU-01", "RNF-02"},
    ("post", "/auth/logout"): {"CU-01", "RNF-02"},
}

OPERACIONES_DE_RECEPCION = [
    ("get", "/clientes/{dni}"),
    ("post", "/clientes"),
    ("get", "/tecnicos/disponibles"),
    ("get", "/ordenes/costo-revision-inicial"),
    ("post", "/ordenes"),
]


def _operaciones():
    for ruta, metodos in app.openapi()["paths"].items():
        for metodo, operacion in metodos.items():
            if metodo in METODOS:
                yield metodo, ruta, operacion


def test_cada_operacion_declara_su_cu_y_pantalla():
    operaciones = list(_operaciones())
    assert len(operaciones) == 7
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


def test_las_etiquetas_corresponden_a_los_codigos_de_c1():
    etiquetas = {t["name"] for t in app.openapi()["tags"]}
    assert etiquetas == {"CU-05 · GUI-01", "CU-06 · GUI-02", "CU-01 · GUI-01", ETIQUETA_ACCESO}


def test_las_operaciones_de_acceso_llevan_la_etiqueta_de_acceso():
    paths = app.openapi()["paths"]
    for ruta in ("/auth/token", "/auth/logout"):
        assert paths[ruta]["post"]["tags"] == [ETIQUETA_ACCESO]


def test_las_operaciones_de_recepcion_declaran_401_y_403():
    """RNF-02: el esquema OpenAPI documenta los rechazos por sesión y por rol."""
    paths = app.openapi()["paths"]
    for metodo, ruta in OPERACIONES_DE_RECEPCION:
        respuestas = paths[ruta][metodo]["responses"]
        assert "401" in respuestas and "403" in respuestas, (metodo, ruta)
