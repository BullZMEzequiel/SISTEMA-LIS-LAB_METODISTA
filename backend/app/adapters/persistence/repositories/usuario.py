from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..models import RolModel, UsuarioModel


class UsuarioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, id_usuario: int) -> UsuarioModel | None:
        statement = (
            select(UsuarioModel)
            .options(selectinload(UsuarioModel.rol))
            .where(UsuarioModel.id_usuario == id_usuario)
        )
        return self._session.scalar(statement)

    def get_by_ci(self, ci: str) -> UsuarioModel | None:
        return self._session.scalar(select(UsuarioModel).where(UsuarioModel.ci == ci))

    def get_by_email(self, correo: str) -> UsuarioModel | None:
        return self._session.scalar(select(UsuarioModel).where(UsuarioModel.correo == correo))

    def get_role(self, id_rol: int) -> RolModel | None:
        return self._session.get(RolModel, id_rol)

    def get_role_by_name(self, nombre: str) -> RolModel | None:
        return self._session.scalar(select(RolModel).where(RolModel.nombre == nombre))

    def get_by_identifier(self, identifier: str) -> UsuarioModel | None:
        """Login exclusivamente por CI — decisión de negocio del 2026-10-05:
        se retiran correo y nombre como métodos de ingreso."""
        statement = (
            select(UsuarioModel)
            .options(selectinload(UsuarioModel.rol))
            .where(
                UsuarioModel.eliminado_en.is_(None),
                UsuarioModel.ci == identifier,
            )
        )
        return self._session.scalar(statement)

    def list(self) -> list[UsuarioModel]:
        statement = select(UsuarioModel).options(selectinload(UsuarioModel.rol)).order_by(UsuarioModel.id_usuario)
        return list(self._session.scalars(statement))

    def add(self, usuario: UsuarioModel) -> UsuarioModel:
        self._session.add(usuario)
        return usuario