from fastapi import APIRouter, Depends

from app.adapters.persistence.models import UsuarioModel
from app.adapters.security.dependencies import require_roles
from app.application.ports import UnitOfWork
from app.application.use_cases.consultas import ConsultarEstudios, ConsultarPaneles
from app.domain.entities import PanelDefinition, StudyDefinition
from app.domain.exceptions import DomainError
from app.entrypoints.api.contracts import PanelResponse, StudyResponse
from app.entrypoints.api.dependencies import get_unit_of_work
from app.entrypoints.api.http_errors import as_http_error

study_router = APIRouter(prefix="/estudios", tags=["Estudios"])
panel_router = APIRouter(prefix="/paneles", tags=["Paneles"])


def _study_response(study: StudyDefinition) -> StudyResponse:
    return StudyResponse(
        id_estudio=study.id_estudio,
        codigo=study.codigo,
        nombre=study.nombre,
        id_estudio_version=study.id_estudio_version,
        numero_version=study.numero_version,
        estrategia_calculo=study.estrategia_calculo,
        parametros_obligatorios=list(study.parametros_obligatorios),
    )


def _panel_response(panel: PanelDefinition) -> PanelResponse:
    return PanelResponse(
        id_panel=panel.id_panel,
        codigo=panel.codigo,
        nombre=panel.nombre,
        descripcion=panel.descripcion,
    )


@study_router.get("", response_model=list[StudyResponse])
def list_studies(
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[StudyResponse]:
    del current_user
    return [_study_response(study) for study in ConsultarEstudios(uow).execute()]


@study_router.get("/{id_estudio}", response_model=StudyResponse)
def get_study(
    id_estudio: int,
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> StudyResponse:
    del current_user
    try:
        return _study_response(ConsultarEstudios(uow).por_id(id_estudio))
    except DomainError as exc:
        raise as_http_error(exc) from exc


@panel_router.get("", response_model=list[PanelResponse])
def list_panels(
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[PanelResponse]:
    del current_user
    return [_panel_response(panel) for panel in ConsultarPaneles(uow).execute()]


@panel_router.get("/{id_panel}", response_model=PanelResponse)
def get_panel(
    id_panel: int,
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> PanelResponse:
    del current_user
    try:
        return _panel_response(ConsultarPaneles(uow).por_id(id_panel))
    except DomainError as exc:
        raise as_http_error(exc) from exc


@panel_router.get("/{id_panel}/estudios", response_model=list[StudyResponse])
def list_panel_studies(
    id_panel: int,
    current_user: UsuarioModel = Depends(require_roles(["BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[StudyResponse]:
    del current_user
    try:
        studies = ConsultarPaneles(uow).estudios(id_panel)
        return [_study_response(study) for study in studies]
    except DomainError as exc:
        raise as_http_error(exc) from exc