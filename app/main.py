"""Aplicación FastAPI de ByteTrack — iteración C1 (recepción y orden de servicio).

La interfaz de uso es la documentación Swagger de FastAPI (``/docs``).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import clientes, ordenes, tecnicos
from app.api.etiquetas import METADATOS_ETIQUETAS
from app.database import crear_tablas
from app.errors import ErrorDominio


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    crear_tablas()
    yield


app = FastAPI(
    title="ByteTrack",
    description=(
        "Iteración C1: recepción de equipos y registro de orden de servicio "
        "(CU-05, CU-06 y CU-01). Fuente de requisitos: documentación AUP en docs/aup/."
    ),
    version="0.1.0",
    openapi_tags=METADATOS_ETIQUETAS,
    lifespan=ciclo_de_vida,
)


@app.exception_handler(ErrorDominio)
async def manejar_error_dominio(_solicitud: Request, error: ErrorDominio) -> JSONResponse:
    """Formato de error uniforme: {codigo, mensaje, detalle}."""
    return JSONResponse(
        status_code=error.status_http,
        content={"codigo": error.codigo, "mensaje": error.mensaje, "detalle": error.detalle},
    )

app.include_router(clientes.router)
app.include_router(tecnicos.router)
app.include_router(ordenes.router)
