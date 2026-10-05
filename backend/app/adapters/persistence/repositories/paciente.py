from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import PacienteModel


class PacienteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, id_paciente: int) -> PacienteModel | None:
        return self._session.get(PacienteModel, id_paciente)

    def get_by_ci(self, ci: str) -> PacienteModel | None:
        return self._session.scalar(select(PacienteModel).where(PacienteModel.ci == ci))

    def search(self, query: str, limit: int = 50) -> list[PacienteModel]:
        pattern = f"%{query.strip()}%"
        statement = (
            select(PacienteModel)
            .where(
                PacienteModel.eliminado_en.is_(None),
                or_(
                    PacienteModel.ci.ilike(pattern),
                    PacienteModel.nombres.ilike(pattern),
                    PacienteModel.apellido_paterno.ilike(pattern),
                    PacienteModel.apellido_materno.ilike(pattern),
                ),
            )
            .order_by(PacienteModel.apellido_paterno, PacienteModel.nombres)
            .limit(limit)
        )
        return list(self._session.scalars(statement))

    def add(self, paciente: PacienteModel) -> PacienteModel:
        self._session.add(paciente)
        return paciente