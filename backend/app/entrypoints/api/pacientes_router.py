from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.adapters.persistence.models import UsuarioModel
from app.adapters.security.dependencies import get_current_user, require_roles
from app.application.ports import UnitOfWork
from app.application.use_cases.pacientes import ActualizarPaciente, BuscarPaciente, CrearPaciente
from app.domain.entities import Patient
from app.domain.exceptions import DomainError
from app.entrypoints.api.contracts import PatientCreateRequest, PatientResponse, PatientUpdateRequest
from app.entrypoints.api.dependencies import get_unit_of_work
from app.entrypoints.api.http_errors import as_http_error

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def _response(patient: Patient) -> PatientResponse:
    return PatientResponse(
        id_paciente=patient.id_paciente,
        ci=patient.ci,
        nombres=patient.nombres,
        apellido_paterno=patient.apellido_paterno,
        apellido_materno=patient.apellido_materno,
        apellidos=" ".join(part for part in (patient.apellido_paterno, patient.apellido_materno) if part),
        fecha_nacimiento=patient.fecha_nacimiento,
        sexo=patient.sexo,
        telefono=patient.telefono,
        correo=patient.correo,
        creado_en=patient.creado_en,
    )


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreateRequest,
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PatientResponse:
    try:
        patient = CrearPaciente(uow).execute(
            ci=payload.ci,
            nombres=payload.nombres,
            apellido_paterno=payload.apellido_paterno or "",
            apellido_materno=payload.apellido_materno,
            fecha_nacimiento=payload.fecha_nacimiento,
            sexo=payload.sexo,
            telefono=payload.telefono,
            correo=payload.correo,
            creado_por=current_user.id_usuario,
        )
        return _response(patient)
    except DomainError as exc:
        raise as_http_error(exc) from exc


@router.get("", response_model=list[PatientResponse])
def search_patients(
    q: str = Query(min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[PatientResponse]:
    try:
        return [_response(patient) for patient in BuscarPaciente(uow).execute(q, current_user.id_usuario, limit)]
    except DomainError as exc:
        raise as_http_error(exc) from exc


@router.get("/buscar", response_model=list[PatientResponse])
def search_patient(
    ci: str | None = None,
    q: str | None = Query(default=None, min_length=1),
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[PatientResponse]:
    use_case = BuscarPaciente(uow)
    if ci:
        try:
            patient = use_case.por_ci(ci, current_user.id_usuario)
        except DomainError as exc:
            raise as_http_error(exc) from exc
        return [_response(patient)] if patient else []
    if q:
        try:
            return [_response(patient) for patient in use_case.execute(q, current_user.id_usuario)]
        except DomainError as exc:
            raise as_http_error(exc) from exc
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Indique ci o q para buscar.")


@router.get("/{id_paciente}", response_model=PatientResponse)
def get_patient(
    id_paciente: int,
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PatientResponse:
    try:
        patient = BuscarPaciente(uow).por_id(id_paciente, current_user.id_usuario)
        if patient is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado.")
        return _response(patient)
    except DomainError as exc:
        raise as_http_error(exc) from exc


@router.put("/{id_paciente}", response_model=PatientResponse)
def update_patient(
    id_paciente: int,
    payload: PatientUpdateRequest,
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PatientResponse:
    try:
        patient = ActualizarPaciente(uow).execute(
            id_paciente,
            current_user.id_usuario,
            payload.model_dump(exclude_unset=True),
        )
        return _response(patient)
    except DomainError as exc:
        raise as_http_error(exc) from exc