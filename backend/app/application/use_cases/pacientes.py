from datetime import date

from app.application.ports import UnitOfWork
from app.application.use_cases._support import atomic, require_bioquimico
from app.domain.entities import AuditEvent, Patient
from app.domain.exceptions import Conflict, EntityNotFound, ValidationError


class CrearPaciente:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        *,
        ci: str,
        nombres: str,
        apellido_paterno: str,
        fecha_nacimiento: date,
        sexo: str,
        creado_por: int,
        apellido_materno: str | None = None,
        telefono: str | None = None,
        correo: str | None = None,
    ) -> Patient:
        clean_ci = ci.strip()
        if not clean_ci or not nombres.strip() or not apellido_paterno.strip():
            raise ValidationError("CI, nombres y apellido paterno son obligatorios.")
        if sexo not in {"M", "F"}:
            raise ValidationError("El sexo debe ser M o F.")
        if fecha_nacimiento > date.today():
            raise ValidationError("La fecha de nacimiento no puede ser futura.")

        def operation() -> Patient:
            require_bioquimico(self._uow, creado_por)
            if self._uow.patients.get_by_ci(clean_ci) is not None:
                raise Conflict("Ya existe un paciente con esa CI.")
            patient = Patient(
                ci=clean_ci,
                nombres=nombres.strip(),
                apellido_paterno=apellido_paterno.strip(),
                apellido_materno=apellido_materno.strip() or None if apellido_materno else None,
                fecha_nacimiento=fecha_nacimiento,
                sexo=sexo,
                telefono=telefono,
                correo=correo,
                creado_por=creado_por,
            )
            saved = self._uow.patients.add(patient)
            self._uow.audits.add(
                AuditEvent(
                    accion="PACIENTE_CREADO",
                    id_usuario=creado_por,
                    entidad="paciente",
                    entidad_id=saved.id_paciente,
                    datos_nuevos={"id_paciente": saved.id_paciente, "ci": saved.ci},
                )
            )
            return saved

        return atomic(self._uow, operation)


class BuscarPaciente:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def por_ci(self, ci: str, id_usuario: int) -> Patient | None:
        require_bioquimico(self._uow, id_usuario)
        return self._uow.patients.get_by_ci(ci.strip())

    def por_id(self, id_paciente: int, id_usuario: int) -> Patient | None:
        require_bioquimico(self._uow, id_usuario)
        return self._uow.patients.get_by_id(id_paciente)

    def execute(self, query: str, id_usuario: int, limit: int = 50) -> list[Patient]:
        require_bioquimico(self._uow, id_usuario)
        if limit < 1 or limit > 200:
            raise ValidationError("El límite de búsqueda debe estar entre 1 y 200.")
        return list(self._uow.patients.search(query, limit))


class ActualizarPaciente:
    _allowed_fields = {
        "ci",
        "nombres",
        "apellido_paterno",
        "apellido_materno",
        "fecha_nacimiento",
        "sexo",
        "telefono",
        "correo",
    }

    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_paciente: int, id_usuario: int, cambios: dict[str, object]) -> Patient:
        invalid = set(cambios) - self._allowed_fields
        if invalid:
            raise ValidationError(f"Campos no editables: {', '.join(sorted(invalid))}.")

        def operation() -> Patient:
            require_bioquimico(self._uow, id_usuario)
            patient = self._uow.patients.get_by_id(id_paciente)
            if patient is None or patient.eliminado:
                raise EntityNotFound("Paciente no encontrado.")
            if "ci" in cambios:
                ci = str(cambios["ci"]).strip()
                other = self._uow.patients.get_by_ci(ci)
                if other is not None and other.id_paciente != id_paciente:
                    raise Conflict("Ya existe un paciente con esa CI.")
                patient.ci = ci
            old = {field: getattr(patient, field) for field in cambios}
            for field in self._allowed_fields - {"ci"}:
                if field in cambios:
                    setattr(patient, field, cambios[field])
            if patient.sexo not in {"M", "F"}:
                raise ValidationError("El sexo debe ser M o F.")
            saved = self._uow.patients.save(patient)
            self._uow.audits.add(
                AuditEvent(
                    accion="PACIENTE_ACTUALIZADO",
                    id_usuario=id_usuario,
                    entidad="paciente",
                    entidad_id=id_paciente,
                    datos_anteriores={"id_paciente": id_paciente, **old},
                    datos_nuevos={"id_paciente": id_paciente, **{field: getattr(saved, field) for field in cambios}},
                )
            )
            return saved

        return atomic(self._uow, operation)