from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import EstudioModel, EstudioVersionModel, PanelEstudioModel


class EstudioRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, id_estudio: int) -> EstudioModel | None:
        return self._session.get(EstudioModel, id_estudio)

    def get_by_code(self, codigo: str) -> EstudioModel | None:
        return self._session.scalar(select(EstudioModel).where(EstudioModel.codigo == codigo))

    def list_active(self) -> list[EstudioModel]:
        return list(self._session.scalars(select(EstudioModel).where(EstudioModel.activo.is_(True)).order_by(EstudioModel.nombre)))

    def list_for_panel(self, id_panel: int) -> list[EstudioModel]:
        statement = (
            select(EstudioModel)
            .join(PanelEstudioModel, PanelEstudioModel.id_estudio == EstudioModel.id_estudio)
            .where(PanelEstudioModel.id_panel == id_panel, EstudioModel.activo.is_(True))
            .order_by(PanelEstudioModel.orden_visualizacion, EstudioModel.nombre)
        )
        return list(self._session.scalars(statement))

    def get_active_version(self, id_estudio: int) -> EstudioVersionModel | None:
        statement = (
            select(EstudioVersionModel)
            .options(selectinload(EstudioVersionModel.parametros))
            .where(EstudioVersionModel.id_estudio == id_estudio, EstudioVersionModel.activa.is_(True))
            .order_by(EstudioVersionModel.numero_version.desc())
            .limit(1)
        )
        return self._session.scalar(statement)