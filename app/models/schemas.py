"""Esquemas Pydantic de entrada y salida (ver contracts/api-c1.md)."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# RN-01: el DNI son exactamente 8 dígitos numéricos.
PATRON_DNI = r"^[0-9]{8}$"
DniStr = Annotated[str, StringConstraints(pattern=PATRON_DNI)]
TextoObligatorio = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _Entrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class _Salida(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---- Cliente (CU-05, CU-06) ----------------------------------------------------------


class ClienteIn(_Entrada):
    dni: DniStr
    nombres: TextoObligatorio
    apellidos: TextoObligatorio
    telefono: TextoObligatorio
    correo: str | None = None


class ClienteOut(_Salida):
    dni: str
    nombres: str
    apellidos: str
    telefono: str
    correo: str | None = None


class EquipoOut(_Salida):
    id: int
    tipo: str
    marca: str
    modelo: str
    numero_serie: str


class BusquedaClienteOut(_Salida):
    cliente: ClienteOut
    equipos: list[EquipoOut]


class RegistroClienteOut(BusquedaClienteOut):
    ya_registrado: bool
    aviso: str | None = None


# ---- Técnicos ------------------------------------------------------------------------


class TecnicoOut(_Salida):
    id: int
    nombres: str
    apellidos: str


class TecnicoResumenOut(_Salida):
    id: int
    nombres: str
    apellidos: str


class CostoRevisionOut(BaseModel):
    costo_revision: Decimal


# ---- Orden de servicio (CU-01) -------------------------------------------------------


class EquipoNuevoIn(_Entrada):
    tipo: TextoObligatorio
    marca: TextoObligatorio
    modelo: TextoObligatorio
    numero_serie: TextoObligatorio


class OrdenIn(_Entrada):
    id_op: TextoObligatorio
    dni: DniStr
    equipo_id: int | None = None
    equipo: EquipoNuevoIn | None = None
    accesorios: str | None = None
    estado_fisico: TextoObligatorio
    falla_reportada: TextoObligatorio
    tecnico_id: int

    @model_validator(mode="after")
    def _exactamente_un_equipo(self):
        if (self.equipo_id is None) == (self.equipo is None):
            raise ValueError("Debe enviarse exactamente uno de 'equipo_id' o 'equipo'")
        return self


class OrdenOut(_Salida):
    codigo: str
    estado: str
    dni: str
    equipo: EquipoOut
    tecnico: TecnicoResumenOut
    accesorios: str | None = None
    estado_fisico: str
    falla_reportada: str
    costo_revision: Decimal


class CrearOrdenOut(BaseModel):
    orden: OrdenOut
    reintento: bool = Field(default=False)


# ---- Errores -------------------------------------------------------------------------


class ErrorOut(BaseModel):
    codigo: str
    mensaje: str
    detalle: dict = Field(default_factory=dict)
