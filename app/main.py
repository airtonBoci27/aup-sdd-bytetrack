"""Aplicación FastAPI de ByteTrack — iteración C1 (recepción y orden de servicio) con acceso por rol.

Sirve la API (documentada en Swagger, ``/docs``) y la interfaz web estática de recepción
(GUI-01 y GUI-02) en ``/``. Las operaciones de recepción exigen sesión activa con rol Recepcionista
(RNF-02).
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.api import auth, clientes, ordenes, taller, tecnicos
from app.api.etiquetas import METADATOS_ETIQUETAS
from app.database import crear_tablas
from app.errors import ErrorDominio

DIRECTORIO_WEB = Path(__file__).parent / "web"


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    # RNF-02 / principio VI: primero el entorno (.env), luego la clave de firma obligatoria
    # (la aplicación no arranca sin una clave válida) y después la base de datos.
    config.cargar_entorno()
    config.clave_jwt()
    crear_tablas()
    yield


app = FastAPI(
    title="ByteTrack",
    description=(
        "Iteración C1: recepción de equipos y registro de orden de servicio "
        "(CU-05, CU-06 y CU-01) con acceso por rol (RNF-02): las operaciones de recepción exigen "
        "sesión activa con rol Recepcionista. Fuente de requisitos: documentación AUP en docs/aup/."
    ),
    version="0.2.0",
    openapi_tags=METADATOS_ETIQUETAS,
    lifespan=ciclo_de_vida,
)


@app.middleware("http")
async def agregar_cabeceras_seguridad(solicitud: Request, call_next):
    """Cabeceras defensivas HTTP (RNF-02); CSP estricta en la interfaz web sin romper Swagger."""
    respuesta = await call_next(solicitud)
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "no-referrer")
    if not solicitud.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        respuesta.headers.setdefault(
            "Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'"
        )
    return respuesta


@app.exception_handler(ErrorDominio)
async def manejar_error_dominio(_solicitud: Request, error: ErrorDominio) -> JSONResponse:
    """Formato de error uniforme: {codigo, mensaje, detalle} (con cabeceras como WWW-Authenticate)."""
    return JSONResponse(
        status_code=error.status_http,
        content={"codigo": error.codigo, "mensaje": error.mensaje, "detalle": error.detalle},
        headers=error.headers or None,
    )


app.include_router(auth.router)
app.include_router(clientes.router)
app.include_router(tecnicos.router)
app.include_router(ordenes.router)
app.include_router(taller.router)

# Interfaz web estática (GUI-01, GUI-02): se monta al final para que las rutas de la API tengan
# prioridad. Sin framework ni compilación (constitución, Restricciones Técnicas).
DIRECTORIO_WEB.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=DIRECTORIO_WEB, html=True), name="web")
