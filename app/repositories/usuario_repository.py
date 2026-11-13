"""Acceso a datos de usuarios y de sesiones cerradas (RNF-02)."""

from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.models.entities import TokenRevocado, Usuario


class UsuarioRepository:
    def __init__(self, sesion: Session):
        self.sesion = sesion

    def obtener_por_nombre(self, nombre_usuario: str) -> Usuario | None:
        return self.sesion.scalar(select(Usuario).where(Usuario.nombre_usuario == nombre_usuario))

    def crear_o_actualizar(self, nombre_usuario: str, clave_hash: str, rol: str) -> Usuario:
        """Crea el usuario o actualiza su hash y su rol si ya existe (carga inicial, RNF-02)."""
        usuario = self.obtener_por_nombre(nombre_usuario)
        if usuario is None:
            usuario = Usuario(nombre_usuario=nombre_usuario, clave_hash=clave_hash, rol=rol)
            self.sesion.add(usuario)
        else:
            usuario.clave_hash = clave_hash
            usuario.rol = rol
        self.sesion.flush()
        return usuario

    def esta_revocado(self, jti: str) -> bool:
        return self.sesion.get(TokenRevocado, jti) is not None

    def revocar(self, jti: str, expira_en: int) -> None:
        """Registra la sesión cerrada; es idempotente (cerrar dos veces no falla)."""
        self.sesion.execute(
            sqlite_insert(TokenRevocado)
            .values(jti=jti, expira_en=expira_en)
            .on_conflict_do_nothing(index_elements=["jti"])
        )

    def purgar_vencidos(self, ahora: int) -> None:
        """Borra los tokens revocados cuya expiración ya pasó (ya no podrían usarse)."""
        self.sesion.execute(delete(TokenRevocado).where(TokenRevocado.expira_en < ahora))
