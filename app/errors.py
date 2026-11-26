"""Excepciones de dominio con código estable (ver contracts/api-c1.md)."""


class ErrorDominio(Exception):
    """Error de negocio que la API traduce a ``{codigo, mensaje, detalle}``."""

    status_http = 400
    codigo = "ERROR_DOMINIO"
    headers: dict[str, str] = {}  # cabeceras extra de la respuesta (p. ej. WWW-Authenticate)

    def __init__(self, mensaje: str, detalle: dict | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.detalle = detalle or {}


class DniInvalido(ErrorDominio):
    """RN-01: el DNI debe tener exactamente 8 dígitos."""

    status_http = 422
    codigo = "DNI_INVALIDO"

    def __init__(self):
        super().__init__("El DNI debe tener exactamente 8 dígitos")


class ClienteNoEncontrado(ErrorDominio):
    """CU-01 curso 2a: el DNI no existe; se habilita «Registrar nuevo cliente»."""

    status_http = 404
    codigo = "CLIENTE_NO_ENCONTRADO"

    def __init__(self, dni: str):
        super().__init__(
            f"No existe un cliente con DNI {dni}", {"habilitar_registro": True}
        )


class EquipoNoEncontrado(ErrorDominio):
    status_http = 404
    codigo = "EQUIPO_NO_ENCONTRADO"

    def __init__(self, equipo_id: int):
        super().__init__(f"El equipo {equipo_id} no existe o no pertenece al cliente")


class OrdenActivaError(ErrorDominio):
    """E01 (CU-01 curso 5a, RN-02): el número de serie ya tiene una orden activa."""

    status_http = 409
    codigo = "E01"

    def __init__(self, codigo_orden: str):
        super().__init__(
            f"Este número de serie ya posee la Orden activa N.° {codigo_orden} en laboratorio",
            {"orden_activa": codigo_orden},
        )


class IdOpConflicto(ErrorDominio):
    """RN-10: el ID OP ya se usó con datos distintos."""

    status_http = 409
    codigo = "ID_OP_CONFLICTO"

    def __init__(self, id_op: str):
        super().__init__(
            f"El identificador de operación {id_op} ya se usó con datos distintos"
        )


class TecnicoNoDisponible(ErrorDominio):
    """RN-03: la orden solo se asigna a un técnico disponible."""

    status_http = 409
    codigo = "TECNICO_NO_DISPONIBLE"

    def __init__(self, tecnico_id: int):
        super().__init__(f"El técnico {tecnico_id} no está disponible o no existe")


class SinTecnicosDisponibles(ErrorDominio):
    """Precondición de CU-01: debe existir al menos un técnico disponible."""

    status_http = 409
    codigo = "SIN_TECNICOS_DISPONIBLES"

    def __init__(self):
        super().__init__("No hay técnicos disponibles para asignar la orden")


class SerieEnOtroCliente(ErrorDominio):
    """RN-01: el número de serie ya está registrado para otro cliente."""

    status_http = 409
    codigo = "SERIE_EN_OTRO_CLIENTE"

    def __init__(self, numero_serie: str):
        super().__init__(
            f"El número de serie {numero_serie} ya está registrado para otro cliente"
        )


# ---- Acceso por rol (RNF-02) ---------------------------------------------------------


class CredencialesInvalidas(ErrorDominio):
    """RNF-02: usuario inexistente o contraseña incorrecta al iniciar sesión."""

    status_http = 401
    codigo = "CREDENCIALES_INVALIDAS"
    headers = {"WWW-Authenticate": "Bearer"}

    def __init__(self):
        super().__init__("Usuario o contraseña incorrectos")


class NoAutenticado(ErrorDominio):
    """RNF-02: no hay sesión activa (sin token, vencido, firma inválida, cerrada o usuario inexistente)."""

    status_http = 401
    codigo = "NO_AUTENTICADO"
    headers = {"WWW-Authenticate": "Bearer"}

    def __init__(self):
        super().__init__("Debe iniciar sesión")


class RolNoPermitido(ErrorDominio):
    """RNF-02: las operaciones están restringidas según el rol del usuario."""

    status_http = 403
    codigo = "ROL_NO_PERMITIDO"

    def __init__(self, mensaje: str = "Su rol no tiene acceso a las operaciones de recepción"):
        super().__init__(mensaje)


# ---- Laboratorio, decisión y liquidación (CU-02, CU-03, CU-04, CU-08) ----------------


class OrdenNoEncontrada(ErrorDominio):
    status_http = 404
    codigo = "ORDEN_NO_ENCONTRADA"

    def __init__(self, codigo_orden: str):
        super().__init__(f"No existe la orden de servicio {codigo_orden}")


class OrdenNoAsignada(ErrorDominio):
    """RN-03: el técnico solo accede a sus órdenes asignadas."""

    status_http = 403
    codigo = "ORDEN_NO_ASIGNADA"

    def __init__(self, codigo_orden: str):
        super().__init__(f"La orden {codigo_orden} no está asignada a su bandeja de laboratorio")


class EstadoOrdenInvalido(ErrorDominio):
    """Precondición de estado de CU-02, CU-03, CU-08 o CU-04."""

    status_http = 409
    codigo = "ESTADO_ORDEN_INVALIDO"

    def __init__(self, codigo_orden: str, estado_actual: str, estado_requerido: str):
        super().__init__(
            f"La orden {codigo_orden} está en estado {estado_actual}; se requiere {estado_requerido}",
            {"estado_actual": estado_actual, "estado_requerido": estado_requerido},
        )


class RepuestoNoEncontrado(ErrorDominio):
    status_http = 404
    codigo = "REPUESTO_NO_ENCONTRADO"

    def __init__(self, repuesto_id: int):
        super().__init__(f"El repuesto {repuesto_id} no existe en almacén")


class StockInsuficienteError(ErrorDominio):
    """E02 (CU-02 curso 9a, RN-04, RNF-01): conflicto de stock libre; no se reserva ninguno."""

    status_http = 409
    codigo = "E02"

    def __init__(self, sku: str, nombre: str, solicitado: int, libre: int):
        super().__init__(
            f"Stock libre insuficiente para {sku} ({nombre}): solicitado {solicitado}, libre {libre}. No se reservó ningún repuesto.",
            {"sku": sku, "nombre": nombre, "solicitado": solicitado, "stock_libre": libre},
        )


class PruebaNoConformeError(ErrorDominio):
    """RN-07 (CU-08 curso 4a): la reparación solo se finaliza con prueba de funcionamiento conforme."""

    status_http = 422
    codigo = "PRUEBA_NO_CONFORME"

    def __init__(self):
        super().__init__(
            "Debe marcar la prueba de funcionamiento conforme antes de finalizar la reparación"
        )


class MontoIncompletoError(ErrorDominio):
    """RN-08 (CU-04 curso 3a): el cobro es por el total en un solo pago."""

    status_http = 422
    codigo = "MONTO_INCOMPLETO"

    def __init__(self, esperado: str, recibido: str):
        super().__init__(
            f"El monto recibido (S/ {recibido}) debe coincidir exactamente con el total a cobrar (S/ {esperado})",
            {"monto_esperado": esperado, "monto_recibido": recibido},
        )


class ConformidadRequeridaError(ErrorDominio):
    """RN-08 (CU-04 curso 3a): exige conformidad de entrega del equipo y accesorios."""

    status_http = 422
    codigo = "CONFORMIDAD_REQUERIDA"

    def __init__(self):
        super().__init__("Debe marcar la conformidad de entrega del equipo y sus accesorios")
