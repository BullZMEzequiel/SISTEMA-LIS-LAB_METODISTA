from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuditoriaModel, AuditoriaSeguridadModel


class AuditoriaRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_order(self, id_orden: int, limit: int = 200) -> list[AuditoriaModel]:
        statement = (
            select(AuditoriaModel)
            .where(AuditoriaModel.id_orden == id_orden)
            .order_by(AuditoriaModel.creado_en.desc())
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def list_recent(self, limit: int = 200) -> list[AuditoriaModel]:
        statement = select(AuditoriaModel).order_by(AuditoriaModel.creado_en.desc()).limit(limit)
        return list(self._session.scalars(statement))

    def list_security_recent(self, limit: int = 200) -> list[AuditoriaSeguridadModel]:
        statement = (
            select(AuditoriaSeguridadModel)
            .order_by(AuditoriaSeguridadModel.creado_en.desc())
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def add(self, event: AuditoriaModel) -> AuditoriaModel:
        self._session.add(event)
        return event

    def add_security_event(self, event: AuditoriaSeguridadModel) -> AuditoriaSeguridadModel:
        self._session.add(event)
        return event