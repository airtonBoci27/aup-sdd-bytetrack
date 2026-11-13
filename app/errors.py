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
    """RNF-02: las operaciones de recepción están restringidas al rol Recepcionista."""

    status_http = 403
    codigo = "ROL_NO_PERMITIDO"

    def __init__(self):
        super().__init__("Su rol no tiene acceso a las operaciones de recepción")
