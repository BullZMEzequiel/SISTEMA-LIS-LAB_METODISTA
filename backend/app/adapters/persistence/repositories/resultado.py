from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import ResultadoVersionModel


class ResultadoRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_version(self, id_resultado_version: int) -> ResultadoVersionModel | None:
        statement = (
            select(ResultadoVersionModel)
            .options(selectinload(ResultadoVersionModel.valores))
            .where(ResultadoVersionModel.id_resultado_version == id_resultado_version)
        )
        return self._session.scalar(statement)

    def list_versions(self, id_orden_estudio: int) -> list[ResultadoVersionModel]:
        statement = (
            select(ResultadoVersionModel)
            .where(ResultadoVersionModel.id_orden_estudio == id_orden_estudio)
            .order_by(ResultadoVersionModel.numero_version)
        )
        return list(self._session.scalars(statement))

    def add(self, version: ResultadoVersionModel) -> ResultadoVersionModel:
        self._session.add(version)
        return version