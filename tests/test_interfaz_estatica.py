"""Trazabilidad de la interfaz web (principio I y VIII) y plantilla de configuración (principio VI).

Comprueba que la interfaz se sirve, que cada elemento con id declara su código AUP en ``data-trace``,
que no existen controles sin trazabilidad ni recursos externos ni usos de ``innerHTML``.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "app" / "web"

CODIGOS_PERMITIDOS = {
    "RNF-02", "RF-01", "RF-02", "RF-03", "RF-04", "RF-05", "RF-06",
    "RN-01", "RN-02", "RN-03", "RN-04", "RN-05", "RN-06", "RN-07", "RN-08", "RN-09", "RNF-04",
    "GUI-01", "GUI-02", "GUI-03", "GUI-04", "GUI-05", "GUI-06",
}
CONTROLES = {"input", "select", "textarea", "button"}
MODULOS_JS = ["app.js", "api.js", "login.js", "recepcion.js", "modal_cliente.js", "taller.js", "ui_addons.js"]

# IDs mínimos críticos que garantizan presencia de todas las pantallas AUP (GUI-01 a GUI-06).
IDS_BASE_AUP = {
    "vista-login", "vista-rechazo-rol", "vista-panel", "vista-recepcion",
    "modal-cliente", "vista-diagnostico", "vista-decision", "vista-finalizar", "vista-cobro",
    "dni", "buscar-cliente", "alerta-e01", "generar-orden", "id-operacion",
    "diag-emitir", "alerta-e02", "dec-registrar", "fin-confirmar", "cob-liquidar",
}


class _Elementos(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elementos = []  # (etiqueta, atributos)

    def handle_starttag(self, etiqueta, atributos):
        self.elementos.append((etiqueta, dict(atributos)))


def _analizar_index():
    analizador = _Elementos()
    analizador.feed((WEB / "index.html").read_text(encoding="utf-8"))
    return analizador.elementos


def test_interfaz_se_sirve_en_la_raiz_y_sus_modulos_js(client_sin_sesion):
    raiz = client_sin_sesion.get("/")
    assert raiz.status_code == 200 and "text/html" in raiz.headers["content-type"]
    for modulo in MODULOS_JS:
        assert client_sin_sesion.get(f"/js/{modulo}").status_code == 200, modulo
    assert client_sin_sesion.get("/css/estilos.css").status_code == 200


def test_rnf02_cabeceras_de_seguridad_en_interfaz_y_docs(client_sin_sesion):
    raiz = client_sin_sesion.get("/")
    assert raiz.headers["x-content-type-options"] == "nosniff"
    assert raiz.headers["x-frame-options"] == "DENY"
    assert raiz.headers["referrer-policy"] == "no-referrer"
    assert "default-src 'self'" in raiz.headers["content-security-policy"]

    docs = client_sin_sesion.get("/docs")
    assert docs.status_code == 200
    assert docs.headers["x-content-type-options"] == "nosniff"
    assert "content-security-policy" not in docs.headers


def test_interfaz_contiene_pantallas_aup_sin_ids_duplicados():
    ids = [atributos["id"] for _etiqueta, atributos in _analizar_index() if "id" in atributos]
    assert len(ids) == len(set(ids)), "hay ids repetidos"
    assert IDS_BASE_AUP <= set(ids), f"faltan ids AUP: {IDS_BASE_AUP - set(ids)}"


def test_interfaz_cada_elemento_declara_data_trace_con_codigo_aup():
    for _etiqueta, atributos in _analizar_index():
        if "id" not in atributos:
            continue
        traza = atributos.get("data-trace", "").split()
        assert traza, f"#{atributos['id']} no declara data-trace"
        assert set(traza) <= CODIGOS_PERMITIDOS, (atributos["id"], traza)


def test_interfaz_todo_control_tiene_id_trazado():
    for etiqueta, atributos in _analizar_index():
        if etiqueta in CONTROLES:
            assert atributos.get("id"), f"<{etiqueta}> sin id trazado: {atributos}"


def test_interfaz_sin_innerhtml_ni_recursos_externos():
    prohibidos = ["innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval("]
    for ruta in [WEB / "index.html", WEB / "css" / "estilos.css", *[WEB / "js" / m for m in MODULOS_JS]]:
        contenido = ruta.read_text(encoding="utf-8")
        assert not re.search(r"https?://", contenido), f"{ruta.name} referencia un recurso externo"
        if ruta.suffix == ".js":
            for patron in prohibidos:
                assert patron not in contenido, f"{ruta.name} usa {patron}"


def test_env_example_no_contiene_valores_secretos():
    """Principio VI: la plantilla lista los nombres de las variables y no trae valores secretos."""
    lineas = (RAIZ / ".env.example").read_text(encoding="utf-8").splitlines()
    asignaciones = {}
    for linea in lineas:
        coincidencia = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", linea)
        if coincidencia:
            asignaciones[coincidencia.group(1)] = coincidencia.group(2).strip()
    secretas = {
        "BYTETRACK_JWT_SECRET",
        "BYTETRACK_RECEPCIONISTA_CLAVE",
        "BYTETRACK_TECNICO_CLAVE",
    }
    assert secretas <= set(asignaciones)
    assert all(asignaciones[nombre] == "" for nombre in secretas)
    assert all(valor == "" for valor in asignaciones.values()), "solo valores vacíos sin comentar"


def test_gitignore_ignora_env_pero_no_env_example():
    lineas = {
        l.strip() for l in (RAIZ / ".gitignore").read_text(encoding="utf-8").splitlines() if l.strip()
    }
    assert ".env" in lineas
    assert ".env.example" not in lineas and ".env*" not in lineas
