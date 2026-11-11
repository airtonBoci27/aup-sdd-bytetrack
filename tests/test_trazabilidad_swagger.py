"""Principio I de la constitución: cada operación declara su CU/pantalla y cita sus RN en Swagger."""

import re

from app.main import app

ETIQUETA = re.compile(r"^CU-\d{2} · GUI-\d{2}$")
METODOS = {"get", "post", "put", "patch", "delete"}

# Reglas que debe citar la descripción de cada operación (método, ruta).
REGLAS_ESPERADAS = {
    ("get", "/clientes/{dni}"): {"RN-01"},
    ("post", "/clientes"): {"RN-01"},
    ("get", "/tecnicos/disponibles"): {"RN-03"},
    ("post", "/ordenes"): {"RN-01", "RN-02", "RN-03", "RN-10"},
}


def _operaciones():
    for ruta, metodos in app.openapi()["paths"].items():
        for metodo, operacion in metodos.items():
            if metodo in METODOS:
                yield metodo, ruta, operacion


def test_cada_operacion_declara_su_cu_y_pantalla():
    operaciones = list(_operaciones())
    assert len(operaciones) == 5
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
    assert etiquetas == {"CU-05 · GUI-01", "CU-06 · GUI-02", "CU-01 · GUI-01"}
