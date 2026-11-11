"""Acceso a datos de operaciones idempotentes (ID OP + resultado, RN-10)."""

from sqlalchemy.orm import Session

from app.models.entities import OperacionIdempotente


class OperacionRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener(self, id_op: str) -> OperacionIdempotente | None:
        return self.sesion.get(OperacionIdempotente, id_op)

    def registrar(
        self, *, id_op: str, operacion: str, huella: str, orden_id: int, resultado: str
    ) -> OperacionIdempotente:
        """Guarda el ID OP con su resultado; solo se invoca cuando la operación se confirma."""
        registro = OperacionIdempotente(
            id_op=id_op,
            operacion=operacion,
            huella=huella,
            orden_id=orden_id,
            resultado=resultado,
        )
        self.sesion.add(registro)
        self.sesion.flush()
        return registro
