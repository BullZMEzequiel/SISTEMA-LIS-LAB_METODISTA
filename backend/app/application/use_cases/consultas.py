from app.application.ports import UnitOfWork
from datetime import datetime, timezone

from app.application.use_cases._support import (
    atomic,
    get_order,
    get_order_for_user,
    require_bioquimico,
    require_edit_access,
)
from app.domain.entities import (
    AuditEvent,
    Delegation,
    HistoryFilter,
    Order,
    OrderStatus,
    OrderStudy,
    ResultChange,
    ResultVersion,
)
from app.domain.exceptions import EntityNotFound, PermissionDenied


class ConsultarHistorial:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_usuario: int, filters: HistoryFilter) -> list[Order]:
        require_bioquimico(self._uow, id_usuario)
        return list(self._uow.orders.list_official(filters))


class ConsultarEstudios:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self):
        return list(self._uow.studies.list_active())

    def por_id(self, id_estudio: int):
        study = self._uow.studies.get_active(id_estudio)
        if study is None:
            raise EntityNotFound("Estudio no encontrado o inactivo.")
        return study


class ConsultarPaneles:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self):
        return list(self._uow.panels.list_active())

    def por_id(self, id_panel: int):
        panel = self._uow.panels.get_active(id_panel)
        if panel is None:
            raise EntityNotFound("Panel no encontrado o inactivo.")
        return panel

    def estudios(self, id_panel: int):
        self.por_id(id_panel)
        return list(self._uow.panels.list_studies(id_panel))


class ConsultarVersiones:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden_estudio: int, id_usuario: int) -> list[ResultVersion]:
        assignment = self._uow.orders.get_order_for_study(id_orden_estudio)
        if assignment is None:
            raise EntityNotFound("El estudio asignado no existe.")
        order, order_study = assignment
        if order.estado is OrderStatus.DRAFT:
            require_edit_access(self._uow, order, id_usuario, order_study.id_estudio)
        else:
            require_bioquimico(self._uow, id_usuario)
        return list(self._uow.results.list_versions(id_orden_estudio))


class ConsultarCambios:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_usuario: int) -> list[ResultChange]:
        order = get_order(self._uow, id_orden)
        if order.estado is OrderStatus.DRAFT:
            require_edit_access(self._uow, order, id_usuario)
        else:
            require_bioquimico(self._uow, id_usuario)
        return list(self._uow.audits.list_changes(id_orden))


class ConsultarOrden:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_usuario: int) -> Order:
        return get_order_for_user(self._uow, id_orden, id_usuario)


class ConsultarVersionesOrden:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_usuario: int) -> list[ResultVersion]:
        order = ConsultarOrden(self._uow).execute(id_orden, id_usuario)
        versions = []
        for assigned in order.estudios:
            if assigned.id_orden_estudio is not None:
                versions.extend(self._uow.results.list_versions(assigned.id_orden_estudio))
        return sorted(versions, key=lambda version: (version.id_orden_estudio, version.numero_version))


class ConsultarOrdenes:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_usuario: int, filters: HistoryFilter | None = None) -> list[Order]:
        require_bioquimico(self._uow, id_usuario)
        filters = filters or HistoryFilter()
        orders = {
            order.id_orden: order
            for order in self._uow.orders.list_by_author(id_usuario)
            if order.estado is not OrderStatus.TRASH
        }
        for order in self._uow.orders.list_official(filters):
            orders[order.id_orden] = order
        for delegation in self._uow.delegations.list_for_collaborator(id_usuario):
            order = self._uow.orders.get_by_id(delegation.id_orden)
            if order and order.estado is not OrderStatus.TRASH and (
                order.estado is not OrderStatus.DRAFT or delegation.aceptada
            ):
                orders[order.id_orden] = ConsultarOrden(self._uow).execute(order.id_orden, id_usuario)
        orders = {
            id_order: order
            for id_order, order in orders.items()
            if _matches_order_filters(order, filters)
        }
        oldest = datetime.min.replace(tzinfo=timezone.utc)
        return sorted(orders.values(), key=lambda order: order.creado_en or oldest, reverse=True)


def _matches_order_filters(order: Order, filters: HistoryFilter) -> bool:
    if filters.paciente_ci and (order.paciente is None or order.paciente.ci != filters.paciente_ci):
        return False
    if filters.nombre:
        if order.paciente is None:
            return False
        name = " ".join(
            value
            for value in (
                order.paciente.nombres,
                order.paciente.apellido_paterno,
                order.paciente.apellido_materno,
            )
            if value
        ).casefold()
        if filters.nombre.casefold() not in name:
            return False
    if filters.folio and filters.folio.casefold() not in order.folio.casefold():
        return False
    if filters.desde and (order.creado_en is None or order.creado_en.date() < filters.desde):
        return False
    if filters.hasta and (order.creado_en is None or order.creado_en.date() > filters.hasta):
        return False
    if filters.id_usuario_autor and order.id_usuario_autor != filters.id_usuario_autor:
        return False
    if filters.id_estudio and not any(study.id_estudio == filters.id_estudio for study in order.estudios):
        return False
    return True


class ConsultarEstudiosOrden:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_usuario: int) -> list:
        order = ConsultarOrden(self._uow).execute(id_orden, id_usuario)
        return list(order.estudios)


class ConsultarEstudioOrden:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_estudio: int, id_usuario: int) -> OrderStudy:
        order = get_order(self._uow, id_orden)
        assigned = next((item for item in order.estudios if item.id_estudio == id_estudio), None)
        if assigned is None:
            raise EntityNotFound("El estudio no pertenece a la orden.")
        require_edit_access(self._uow, order, id_usuario, id_estudio)
        return assigned


class ConsultarResultadoEstudio:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_estudio: int, id_usuario: int) -> ResultVersion | None:
        order = get_order(self._uow, id_orden)
        assigned = next((item for item in order.estudios if item.id_estudio == id_estudio), None)
        if assigned is None or assigned.id_orden_estudio is None:
            raise EntityNotFound("El estudio no pertenece a la orden.")
        require_edit_access(self._uow, order, id_usuario, id_estudio)
        return self._uow.results.get_latest(assigned.id_orden_estudio)


class ConsultarDelegaciones:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_usuario: int) -> list[Delegation]:
        ConsultarOrden(self._uow).execute(id_orden, id_usuario)
        return list(self._uow.delegations.list_for_order(id_orden))


class ConsultarAuditoria:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def reciente(self, id_usuario: int, limit: int = 200) -> list[AuditEvent]:
        _require_audit_access(self._uow, id_usuario)
        return list(self._uow.audits.list_recent(limit))

    def por_orden(self, id_orden: int, id_usuario: int, limit: int = 200) -> list[AuditEvent]:
        _require_audit_access(self._uow, id_usuario)
        if not self._uow.users.exists_active_admin(id_usuario):
            ConsultarOrden(self._uow).execute(id_orden, id_usuario)
        elif self._uow.orders.get_by_id(id_orden) is None:
            raise EntityNotFound("Orden no encontrada.")
        return list(self._uow.audits.list_for_order(id_orden, limit))


def _require_audit_access(uow: UnitOfWork, id_usuario: int) -> None:
    if not (
        uow.users.exists_active_bioquimico(id_usuario)
        or uow.users.exists_active_admin(id_usuario)
    ):
        raise PermissionDenied("La consulta de auditoría requiere un usuario ADMIN o BIOQUIMICO activo.")


class ConsultarPapelera:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_usuario: int) -> list[Order]:
        require_bioquimico(self._uow, id_usuario)
        return list(self._uow.orders.list_trash(id_usuario))


class CerrarSesion:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        id_usuario: int,
        ip_origen: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        def operation() -> None:
            self._uow.audits.add_security_event(
                id_usuario,
                "LOGOUT",
                ip_origen=ip_origen,
                user_agent=user_agent,
            )

        atomic(self._uow, operation)