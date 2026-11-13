"""Trazabilidad de la interfaz web (principio VIII; SC-006) y plantilla de configuración (principio VI).

Comprueba que la interfaz se sirve, que cada elemento declara su código AUP en ``data-trace`` y que no
existe ningún campo, botón ni listado fuera de specs/002-interfaz-recepcion-rol/contracts/ui-gui01-gui02.md.
El comportamiento de la pantalla se verifica con la lista manual de specs/002-.../checklists/.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "app" / "web"

# Contrato de interfaz: vistas, inicio de sesión, rechazo, encabezado, GUI-01 y GUI-02.
IDS_CONTRATO = {
    # vistas
    "vista-login", "vista-rechazo-rol", "vista-recepcion", "modal-cliente",
    # inicio de sesión y rechazo (RNF-02)
    "login-usuario", "login-clave", "login-entrar", "login-error", "rechazo-mensaje",
    # encabezado
    "encabezado-titulo", "sesion-etiqueta", "cerrar-sesion", "flujo-estados",
    # GUI-01 §1 cliente
    "dni", "buscar-cliente", "dni-error", "registrar-cliente-abrir", "cliente-resumen",
    # GUI-01 §2 equipo
    "equipo-selector", "equipo-tipo", "equipo-marca", "equipo-modelo", "equipo-serie",
    "acc-cargador", "acc-funda", "estado-fisico", "alerta-e01",
    # GUI-01 §3 orden de servicio
    "falla", "tecnico", "costo-revision", "estado-inicial",
    # GUI-01 resultados y pie
    "alerta-error", "confirmacion-orden", "id-operacion", "cancelar-orden", "generar-orden",
    # GUI-02
    "cli-dni", "cli-nombres", "cli-apellidos", "cli-telefono", "cli-correo",
    "cli-guardar", "cli-aviso", "cli-error", "cli-cancelar", "cli-nota",
}
CODIGOS_PERMITIDOS = {
    "RNF-02", "RF-01", "RF-02", "RN-01", "RN-02", "RN-03", "RNF-04", "GUI-01", "GUI-02",
}
CONTROLES = {"input", "select", "textarea", "button"}
LISTADOS = {"table", "ul", "ol", "dl"}
MODULOS_JS = ["app.js", "api.js", "login.js", "recepcion.js", "modal_cliente.js"]


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


def test_interfaz_el_conjunto_de_ids_coincide_con_el_contrato():
    ids = [atributos["id"] for _etiqueta, atributos in _analizar_index() if "id" in atributos]
    assert len(ids) == len(set(ids)), "hay ids repetidos"
    assert set(ids) - IDS_CONTRATO == set(), "elementos fuera del contrato de interfaz"
    assert IDS_CONTRATO - set(ids) == set(), "elementos del contrato que faltan"


def test_interfaz_cada_elemento_declara_data_trace_con_codigo_aup():
    for etiqueta, atributos in _analizar_index():
        if "id" not in atributos:
            continue
        traza = atributos.get("data-trace", "").split()
        assert traza, f"#{atributos['id']} no declara data-trace"
        assert set(traza) <= CODIGOS_PERMITIDOS, (atributos["id"], traza)


def test_interfaz_sin_controles_fuera_del_contrato():
    for etiqueta, atributos in _analizar_index():
        if etiqueta in CONTROLES:
            assert atributos.get("id") in IDS_CONTRATO, f"<{etiqueta}> sin id del contrato: {atributos}"
        assert etiqueta not in LISTADOS, f"<{etiqueta}>: no hay listados (fuera de alcance)"


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
        coincidencia = re.match(r"^([A-Z][A-Z0-9_]*)=(.*)$", linea)  # solo las líneas no comentadas
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
