from collections.abc import Callable
from dataclasses import replace
from typing import TypeVar

from app.application.ports import UnitOfWork
from app.domain.entities import DelegationMode, Order, OrderStatus
from app.domain.exceptions import EntityNotFound, PermissionDenied

T = TypeVar("T")


def atomic(uow: UnitOfWork, operation: Callable[[], T]) -> T:
    try:
        result = operation()
        uow.commit()
        return result
    except Exception:
        uow.rollback()
        raise


def require_bioquimico(uow: UnitOfWork, id_usuario: int) -> None:
    if not uow.users.exists_active_bioquimico(id_usuario):
        raise PermissionDenied("La operación requiere un usuario BIOQUIMICO activo.")


def get_order(uow: UnitOfWork, id_orden: int) -> Order:
    order = uow.orders.get_by_id(id_orden)
    if order is None:
        raise EntityNotFound("Orden no encontrada.")
    return order


def get_order_for_user(uow: UnitOfWork, id_orden: int, id_usuario: int) -> Order:
    order = get_order(uow, id_orden)
    require_bioquimico(uow, id_usuario)
    if order.estado is not OrderStatus.DRAFT or order.id_usuario_autor == id_usuario:
        return order

    delegation = uow.delegations.get_active_for_order(order.id_orden or 0)
    if (
        delegation is None
        or not delegation.aceptada
        or delegation.id_usuario_colaborador != id_usuario
    ):
        raise PermissionDenied("El usuario no tiene permiso para consultar esta orden.")
    if delegation.modalidad is DelegationMode.COMPLETE:
        return order

    visible_studies = [study for study in order.estudios if study.id_estudio in delegation.estudios]
    if not visible_studies:
        raise PermissionDenied("El usuario no tiene estudios delegados en esta orden.")
    return replace(order, estudios=visible_studies)


def require_edit_access(
    uow: UnitOfWork,
    order: Order,
    id_usuario: int,
    id_estudio: int | None = None,
) -> None:
    require_bioquimico(uow, id_usuario)
    if order.id_usuario_autor == id_usuario:
        return

    delegation = uow.delegations.get_active_for_order(order.id_orden or 0)
    if (
        delegation is None
        or not delegation.aceptada
        or delegation.id_usuario_colaborador != id_usuario
        or order.estado is not OrderStatus.DRAFT
    ):
        raise PermissionDenied("El usuario no tiene permiso para modificar esta orden.")
    if delegation.modalidad is DelegationMode.STUDIES and id_estudio not in delegation.estudios:
        raise PermissionDenied("El usuario no tiene permiso sobre este estudio.")


def require_order_author(uow: UnitOfWork, order: Order, id_usuario: int) -> None:
    require_bioquimico(uow, id_usuario)
    if order.id_usuario_autor != id_usuario:
        raise PermissionDenied("Solo el autor original puede realizar esta operación.")


def record_event(
    uow: UnitOfWork,
    accion: str,
    id_usuario: int,
    *,
    order: Order | None = None,
    id_orden_estudio: int | None = None,
    id_resultado_version: int | None = None,
    descripcion: str | None = None,
    old: dict[str, object] | None = None,
    new: dict[str, object] | None = None,
) -> None:
    from app.domain.entities import AuditEvent

    uow.audits.add(
        AuditEvent(
            accion=accion,
            id_usuario=id_usuario,
            id_orden=order.id_orden if order else None,
            id_orden_estudio=id_orden_estudio,
            id_resultado_version=id_resultado_version,
            entidad="orden" if order else None,
            entidad_id=order.id_orden if order else None,
            descripcion=descripcion,
            datos_anteriores=old,
            datos_nuevos=new,
        )
    )