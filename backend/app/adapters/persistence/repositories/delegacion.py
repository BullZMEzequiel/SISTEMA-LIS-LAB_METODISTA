from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import DelegacionModel


class DelegacionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active_for_order(self, id_orden: int) -> DelegacionModel | None:
        statement = (
            select(DelegacionModel)
            .options(selectinload(DelegacionModel.estudios))
            .where(DelegacionModel.id_orden == id_orden, DelegacionModel.activa.is_(True))
        )
        return self._session.scalar(statement)

    def list_for_collaborator(self, id_usuario: int) -> list[DelegacionModel]:
        statement = (
            select(DelegacionModel)
            .where(DelegacionModel.id_usuario_colaborador == id_usuario, DelegacionModel.activa.is_(True))
            .order_by(DelegacionModel.creada_en.desc())
        )
        return list(self._session.scalars(statement))

    def add(self, delegacion: DelegacionModel) -> DelegacionModel:
        self._session.add(delegacion)
        return delegacion