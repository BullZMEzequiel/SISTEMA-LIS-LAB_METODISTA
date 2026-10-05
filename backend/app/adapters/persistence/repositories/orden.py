from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import OrdenModel


class OrdenRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, id_orden: int) -> OrdenModel | None:
        statement = (
            select(OrdenModel)
            .options(selectinload(OrdenModel.paciente), selectinload(OrdenModel.estudios))
            .where(OrdenModel.id_orden == id_orden)
        )
        return self._session.scalar(statement)

    def list_by_author(self, id_usuario_autor: int, *, borradores: bool = True) -> list[OrdenModel]:
        statement = select(OrdenModel).where(OrdenModel.id_usuario_autor == id_usuario_autor)
        if not borradores:
            statement = statement.where(OrdenModel.estado == "OFICIAL")
        return list(self._session.scalars(statement.order_by(OrdenModel.creado_en.desc())))

    def add(self, orden: OrdenModel) -> OrdenModel:
        self._session.add(orden)
        return orden