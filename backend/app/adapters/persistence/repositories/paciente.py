"""
backend/app/adapters/persistence/repositories/paciente.py
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.adapters.persistence.models import PacienteModel


class PacienteRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_ci(self, ci: str) -> PacienteModel | None:
        statement = select(PacienteModel).where(
            PacienteModel.ci == ci,
            PacienteModel.eliminado_en.is_(None),
        )
        return self._session.scalar(statement)

    def get_by_id(self, id_paciente: int) -> PacienteModel | None:
        statement = select(PacienteModel).where(
            PacienteModel.id_paciente == id_paciente,
            PacienteModel.eliminado_en.is_(None),
        )
        return self._session.scalar(statement)

    def buscar(self, texto: str, limite: int = 20) -> list[PacienteModel]:
        """Busca por CI exacto o por coincidencia parcial de nombre/apellido."""
        patron = f"%{texto}%"
        statement = (
            select(PacienteModel)
            .where(
                PacienteModel.eliminado_en.is_(None),
                or_(
                    PacienteModel.ci.ilike(patron),
                    PacienteModel.nombres.ilike(patron),
                    PacienteModel.apellido_paterno.ilike(patron),
                    PacienteModel.apellido_materno.ilike(patron),
                ),
            )
            .order_by(PacienteModel.apellido_paterno)
            .limit(limite)
        )
        return list(self._session.scalars(statement))

    def crear(
        self,
        ci: str,
        nombres: str,
        apellido_paterno: str,
        apellido_materno: str | None,
        fecha_nacimiento: date,
        sexo: str,
        telefono: str | None,
        correo: str | None,
        creado_por: int,
    ) -> PacienteModel:
        paciente = PacienteModel(
            ci=ci,
            nombres=nombres,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            fecha_nacimiento=fecha_nacimiento,
            sexo=sexo,
            telefono=telefono,
            correo=correo,
            creado_por=creado_por,
        )
        self._session.add(paciente)
        self._session.commit()
        self._session.refresh(paciente)
        return paciente

    def actualizar(self, paciente: PacienteModel, cambios: dict) -> PacienteModel:
        for campo, valor in cambios.items():
            if valor is not None:
                setattr(paciente, campo, valor)
        self._session.commit()
        self._session.refresh(paciente)
        return paciente