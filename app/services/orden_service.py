"""Reglas de negocio de CU-01 Registrar orden de servicio.

Reglas aplicadas en esta capa: RN-01 (DNI y número de serie únicos), RN-02 (una sola orden
activa por equipo), RN-03 (asignación solo a un técnico disponible) y RN-10 (idempotencia).

La operación completa se ejecuta en una sola transacción con escritura serializada
(``BEGIN IMMEDIATE``): equipo nuevo, orden y cola del técnico se confirman juntos o no se
confirma nada.
"""

import hashlib
import json
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import config
from app.database import iniciar_escritura
from app.errors import (
    ClienteNoEncontrado,
    EquipoNoEncontrado,
    IdOpConflicto,
    OrdenActivaError,
    SerieEnOtroCliente,
    SinTecnicosDisponibles,
    TecnicoNoDisponible,
)
from app.models.entities import OrdenServicio, Tecnico
from app.models.schemas import CrearOrdenOut, EquipoOut, OrdenIn, OrdenOut, TecnicoResumenOut
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.equipo_repository import EquipoRepository
from app.repositories.operacion_repository import OperacionRepository
from app.repositories.orden_repository import OrdenRepository
from app.repositories.tecnico_repository import TecnicoRepository


def listar_tecnicos_disponibles(sesion: Session) -> list[Tecnico]:
    """CU-01 paso 4 / RN-03: solo se ofrecen técnicos disponibles."""
    return TecnicoRepository(sesion).listar_disponibles()


def costo_revision_inicial() -> Decimal:
    """CU-01 paso 4: costo de revisión inicial que el Recepcionista verifica."""
    return config.costo_revision_inicial()


def _a_orden_out(orden: OrdenServicio) -> OrdenOut:
    return OrdenOut(
        codigo=orden.codigo,
        estado=orden.estado,
        dni=orden.equipo.cliente.dni,
        equipo=EquipoOut.model_validate(orden.equipo),
        tecnico=TecnicoResumenOut.model_validate(orden.tecnico),
        accesorios=orden.accesorios,
        estado_fisico=orden.estado_fisico,
        falla_reportada=orden.falla_reportada,
        costo_revision=orden.costo_revision,
    )


def _huella(datos: OrdenIn) -> str:
    """SHA-256 de la solicitud normalizada (sin el ID OP) para detectar datos distintos (RN-10)."""
    canonico = json.dumps(
        datos.model_dump(mode="json", exclude={"id_op"}),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def crear_orden(sesion: Session, datos: OrdenIn) -> tuple[CrearOrdenOut, bool]:
    """CU-01: registra la orden de servicio.

    Devuelve ``(respuesta, creada)``; ``creada`` es ``False`` cuando la respuesta proviene
    de un reintento con el mismo ID OP (CU-01 curso 6a, RN-10).
    """
    iniciar_escritura(sesion)  # BEGIN IMMEDIATE: escritores serializados
    try:
        respuesta, creada = _registrar(sesion, datos)
        if creada:
            sesion.commit()
        else:
            sesion.rollback()  # solo lectura: libera el bloqueo de escritura
        return respuesta, creada
    except IntegrityError as error:
        sesion.rollback()
        traducido = _traducir_integridad(sesion, datos, error)
        if traducido is not None:
            raise traducido from error
        raise
    except Exception:
        sesion.rollback()  # todo o nada
        raise


def _traducir_integridad(sesion: Session, datos: OrdenIn, error: IntegrityError):
    """Respaldo de RN-02 en la base: una violación del índice único parcial se informa como E01."""
    if "orden_servicio.equipo_id" not in str(error.orig):
        return None
    equipos = EquipoRepository(sesion)
    equipo = (
        equipos.obtener(datos.equipo_id)
        if datos.equipo_id is not None
        else equipos.obtener_por_serie(datos.equipo.numero_serie)
    )
    activa = OrdenRepository(sesion).obtener_activa_por_equipo(equipo.id) if equipo else None
    return OrdenActivaError(activa.codigo) if activa else None


def _registrar(sesion: Session, datos: OrdenIn) -> tuple[CrearOrdenOut, bool]:
    clientes = ClienteRepository(sesion)
    equipos = EquipoRepository(sesion)
    tecnicos = TecnicoRepository(sesion)
    ordenes = OrdenRepository(sesion)
    operaciones = OperacionRepository(sesion)

    # RN-10: si el ID OP ya se confirmó con los mismos datos se devuelve el resultado guardado;
    # con datos distintos se rechaza.
    huella = _huella(datos)
    previa = operaciones.obtener(datos.id_op)
    if previa is not None:
        if previa.huella != huella:
            raise IdOpConflicto(datos.id_op)
        guardada = CrearOrdenOut.model_validate_json(previa.resultado)
        return guardada.model_copy(update={"reintento": True}), False

    # CU-01 paso 1-2: el cliente se identifica por DNI (RN-01).
    cliente = clientes.obtener_por_dni(datos.dni)
    if cliente is None:
        raise ClienteNoEncontrado(datos.dni)

    # CU-01 paso 3: equipo existente del cliente o equipo nuevo (RN-01: serie única).
    equipo = None
    if datos.equipo_id is not None:
        equipo = equipos.obtener(datos.equipo_id)
        if equipo is None or equipo.cliente_id != cliente.id:
            raise EquipoNoEncontrado(datos.equipo_id)
    else:
        existente = equipos.obtener_por_serie(datos.equipo.numero_serie)
        if existente is not None:
            if existente.cliente_id != cliente.id:
                raise SerieEnOtroCliente(datos.equipo.numero_serie)  # RN-01
            equipo = existente

    # CU-01 paso 5 / curso 5a (RN-02): el equipo no puede tener otra orden activa.
    if equipo is not None:
        activa = ordenes.obtener_activa_por_equipo(equipo.id)
        if activa is not None:
            raise OrdenActivaError(activa.codigo)  # alerta E01

    # CU-01 paso 4: precondición y RN-03 (solo técnico disponible, revalidado en la transacción).
    if not tecnicos.listar_disponibles():
        raise SinTecnicosDisponibles()
    tecnico = tecnicos.obtener(datos.tecnico_id)
    if tecnico is None or not tecnico.disponible:
        raise TecnicoNoDisponible(datos.tecnico_id)  # RN-03

    # CU-01 paso 6: se crea el equipo nuevo (si aplica), la orden y se incrementa la cola.
    if equipo is None:
        nuevo = datos.equipo
        equipo = equipos.crear(cliente.id, nuevo.tipo, nuevo.marca, nuevo.modelo, nuevo.numero_serie)

    orden = ordenes.crear(
        equipo_id=equipo.id,
        tecnico_id=tecnico.id,
        accesorios=datos.accesorios,
        estado_fisico=datos.estado_fisico,
        falla_reportada=datos.falla_reportada,
        costo_revision=config.costo_revision_inicial(),
        id_op=datos.id_op,
    )
    tecnicos.incrementar_cola(tecnico.id)  # RN-03: la cola del técnico aumenta en 1

    sesion.refresh(orden)
    respuesta = CrearOrdenOut(orden=_a_orden_out(orden), reintento=False)

    # RN-10: se guarda el ID OP con su resultado en la misma transacción (solo si se confirma).
    operaciones.registrar(
        id_op=datos.id_op,
        huella=huella,
        orden_id=orden.id,
        resultado=respuesta.model_dump_json(),
    )
    return respuesta, True
