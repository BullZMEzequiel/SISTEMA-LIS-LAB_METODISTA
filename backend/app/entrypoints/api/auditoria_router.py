from fastapi import APIRouter, Depends

from app.adapters.persistence.models import UsuarioModel
from app.adapters.security.dependencies import require_roles
from app.application.ports import UnitOfWork
from app.application.use_cases import ConsultarAuditoria
from app.domain.entities import AuditEvent
from app.domain.exceptions import DomainError
from app.entrypoints.api.contracts import AuditEventResponse
from app.entrypoints.api.dependencies import get_unit_of_work
from app.entrypoints.api.http_errors import as_http_error

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


def _response(event: AuditEvent) -> AuditEventResponse:
    return AuditEventResponse(
        id_auditoria=event.id_auditoria,
        id_usuario=event.id_usuario,
        id_orden=event.id_orden,
        id_orden_estudio=event.id_orden_estudio,
        id_resultado_version=event.id_resultado_version,
        accion=event.accion,
        entidad=event.entidad,
        entidad_id=event.entidad_id,
        descripcion=event.descripcion,
        creado_en=event.creado_en,
    )


@router.get("", response_model=list[AuditEventResponse])
def list_audit(
    limit: int = 200,
    user: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[AuditEventResponse]:
    if not 1 <= limit <= 500:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit debe estar entre 1 y 500.")
    try:
        return [_response(event) for event in ConsultarAuditoria(uow).reciente(user.id_usuario, limit)]
    except DomainError as exc:
        raise as_http_error(exc) from exc


@router.get("/ordenes/{id_orden}", response_model=list[AuditEventResponse])
def list_order_audit(
    id_orden: int,
    limit: int = 200,
    user: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> list[AuditEventResponse]:
    if not 1 <= limit <= 500:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="limit debe estar entre 1 y 500.")
    try:
        return [_response(event) for event in ConsultarAuditoria(uow).por_orden(id_orden, user.id_usuario, limit)]
    except DomainError as exc:
        raise as_http_error(exc) from exc