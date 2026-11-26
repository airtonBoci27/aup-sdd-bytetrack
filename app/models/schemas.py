"""Esquemas Pydantic de entrada y salida (ver contracts/api-c1.md)."""

from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

# RN-01: el DNI son exactamente 8 dígitos numéricos.
PATRON_DNI = r"^[0-9]{8}$"
_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
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

    @field_validator("correo")
    @classmethod
    def _validar_correo(cls, valor: str | None) -> str | None:
        if valor is None or valor == "":
            return None
        if not _PATRON_CORREO.fullmatch(valor):
            raise ValueError("El correo electrónico no tiene un formato válido")
        return valor


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
    cola: int  # CU-01 paso 6 / GUI-01 («N en cola»); dato de solo lectura


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


# ---- Acceso por rol (RNF-02) ---------------------------------------------------------


class TokenOut(BaseModel):
    """Respuesta del inicio de sesión (flujo OAuth2 de contraseña). ``rol`` es informativo."""

    access_token: str
    token_type: str = "bearer"
    rol: str


# ---- Seguimiento, Laboratorio, Decisión y Liquidación (CU-02, 03, 04, 07, 08) --------


class RepuestoOut(_Salida):
    id: int
    sku: str
    nombre: str
    stock_disponible: int
    stock_reservado: int
    stock_libre: int
    precio_unitario: Decimal


class PaginaRepuestosOut(BaseModel):
    items: list[RepuestoOut]
    total: int
    page: int
    limit: int
    total_pages: int


class DetalleRepuestoOut(_Salida):
    repuesto_id: int
    sku: str
    nombre: str
    cantidad: int
    precio_cotizado: Decimal
    subtotal: Decimal
    estado_reserva: str


class DiagnosticoOut(_Salida):
    informe_tecnico: str
    costo_mano_obra: Decimal
    subtotal_repuestos: Decimal
    total_presupuesto: Decimal
    fecha_emision: str
    detalles: list[DetalleRepuestoOut]


class ComprobantePagoOut(_Salida):
    numero: str
    metodo_pago: str
    monto_total: Decimal
    fecha_emision: str
    conformidad_entrega: bool


class OrdenDetalleOut(BaseModel):
    codigo: str
    estado: str
    fecha_ingreso: str
    cliente: ClienteOut
    equipo: EquipoOut
    tecnico: TecnicoResumenOut
    accesorios: str | None = None
    estado_fisico: str
    falla_reportada: str
    costo_revision: Decimal
    diagnostico: DiagnosticoOut | None = None
    decision_canal: str | None = None
    decision_fecha: str | None = None
    decision_evidencia: str | None = None
    trabajo_realizado: str | None = None
    prueba_conforme: bool | None = None
    resultado_prueba: str | None = None
    comprobante: ComprobantePagoOut | None = None


class PaginaOrdenesOut(BaseModel):
    items: list[OrdenDetalleOut]
    total: int
    page: int
    limit: int
    total_pages: int


class ResumenTallerOut(BaseModel):
    total_ordenes: int
    por_estado: dict[str, int]
    tecnicos_disponibles: int
    repuestos_stock_bajo: int


class TecnicoCargaOut(_Salida):
    id: int
    nombres: str
    apellidos: str
    disponible: bool
    cola: int


class PaginaClientesOut(BaseModel):
    items: list[BusquedaClienteOut]
    total: int
    page: int
    limit: int
    total_pages: int


class ItemRepuestoIn(_Entrada):
    repuesto_id: int
    cantidad: int = Field(gt=0)


class DiagnosticoIn(_Entrada):
    id_op: TextoObligatorio
    informe_tecnico: TextoObligatorio
    costo_mano_obra: Decimal = Field(ge=Decimal("0.00"))
    repuestos: list[ItemRepuestoIn] = Field(default_factory=list)


class EmitirDiagnosticoOut(BaseModel):
    orden: OrdenDetalleOut
    reintento: bool = False


class DecisionIn(_Entrada):
    id_op: TextoObligatorio
    decision: Literal["APROBADO", "RECHAZADO"]
    canal: Literal["WHATSAPP", "LLAMADA", "PRESENCIAL"]
    evidencia: TextoObligatorio


class RegistrarDecisionOut(BaseModel):
    orden: OrdenDetalleOut
    reintento: bool = False


class FinalizarReparacionIn(_Entrada):
    id_op: TextoObligatorio
    trabajo_realizado: TextoObligatorio
    prueba_conforme: bool
    resultado_prueba: TextoObligatorio


class FinalizarReparacionOut(BaseModel):
    orden: OrdenDetalleOut
    reintento: bool = False


class LiquidarOrdenIn(_Entrada):
    id_op: TextoObligatorio
    metodo_pago: Literal["EFECTIVO", "TARJETA", "TRANSFERENCIA"]
    monto_recibido: Decimal = Field(ge=Decimal("0.00"))
    conformidad_entrega: bool


class LiquidarOrdenOut(BaseModel):
    orden: OrdenDetalleOut
    comprobante: ComprobantePagoOut
    reintento: bool = False
