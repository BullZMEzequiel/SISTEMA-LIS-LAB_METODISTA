from datetime import datetime, timezone

from app.application.ports import Clock, UnitOfWork
from app.application.use_cases._support import (
    atomic,
    get_order,
    record_event,
    require_bioquimico,
    require_order_author,
)
from app.domain.entities import Delegation, DelegationMode, OrderStatus
from app.domain.exceptions import Conflict, EntityNotFound, InvalidState, PermissionDenied, ValidationError


class DelegarOrden:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        *,
        id_orden: int,
        id_usuario_autor: int,
        id_usuario_colaborador: int,
        comentario: str | None = None,
    ) -> Delegation:
        return _crear_delegacion(
            self._uow,
            id_orden=id_orden,
            id_usuario_autor=id_usuario_autor,
            id_usuario_colaborador=id_usuario_colaborador,
            modalidad=DelegationMode.COMPLETE,
            estudios=set(),
            comentario=comentario,
        )


class DelegarEstudio:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        *,
        id_orden: int,
        id_usuario_autor: int,
        id_usuario_colaborador: int,
        ids_estudio: list[int],
        comentario: str | None = None,
    ) -> Delegation:
        selected = set(ids_estudio)
        if not selected:
            raise ValidationError("Seleccione al menos un estudio para delegar.")
        return _crear_delegacion(
            self._uow,
            id_orden=id_orden,
            id_usuario_autor=id_usuario_autor,
            id_usuario_colaborador=id_usuario_colaborador,
            modalidad=DelegationMode.STUDIES,
            estudios=selected,
            comentario=comentario,
        )


def _crear_delegacion(
    uow: UnitOfWork,
    *,
    id_orden: int,
    id_usuario_autor: int,
    id_usuario_colaborador: int,
    modalidad: DelegationMode,
    estudios: set[int],
    comentario: str | None,
) -> Delegation:
    def operation() -> Delegation:
        order = get_order(uow, id_orden)
        require_order_author(uow, order, id_usuario_autor)
        if order.estado is not OrderStatus.DRAFT:
            raise InvalidState("Solo se delegan órdenes pendientes.")
        if id_usuario_autor == id_usuario_colaborador:
            raise ValidationError("El autor y el colaborador deben ser usuarios distintos.")
        if not uow.users.exists_active_bioquimico(id_usuario_colaborador):
            raise EntityNotFound("El colaborador no existe o no es un BIOQUIMICO activo.")
        if uow.delegations.get_active_for_order(id_orden) is not None:
            raise Conflict("La orden ya tiene una delegación activa.")
        assigned_ids = {item.id_estudio for item in order.estudios}
        if not estudios <= assigned_ids:
            raise ValidationError("La delegación incluye estudios que no pertenecen a la orden.")
        delegation = Delegation(
            id_orden=id_orden,
            id_usuario_autor=id_usuario_autor,
            id_usuario_colaborador=id_usuario_colaborador,
            modalidad=modalidad,
            estudios=estudios,
            comentario=comentario,
        )
        saved = uow.delegations.add(delegation)
        record_event(
            uow,
            "ORDEN_DELEGADA" if modalidad is DelegationMode.COMPLETE else "ESTUDIOS_DELEGADOS",
            id_usuario_autor,
            order=order,
            new={"id_usuario_colaborador": id_usuario_colaborador, "modalidad": modalidad.value},
        )
        return saved

    return atomic(uow, operation)


class AceptarDelegacion:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_delegacion: int, id_usuario: int) -> Delegation:
        def operation() -> Delegation:
            require_bioquimico(self._uow, id_usuario)
            delegation = self._uow.delegations.get_by_id(id_delegacion)
            if delegation is None or not delegation.activa:
                raise EntityNotFound("La delegación activa no existe.")
            if delegation.id_usuario_colaborador != id_usuario:
                raise PermissionDenied("Solo el colaborador asignado puede aceptar la delegación.")
            if delegation.aceptada:
                raise Conflict("La delegación ya fue aceptada.")
            delegation.aceptada = True
            saved = self._uow.delegations.save(delegation)
            order = get_order(self._uow, delegation.id_orden)
            record_event(
                self._uow,
                "DELEGACION_ACEPTADA",
                id_usuario,
                order=order,
                new={"id_delegacion": id_delegacion},
            )
            return saved

        return atomic(self._uow, operation)


class FinalizarDelegacion:
    def __init__(self, uow: UnitOfWork, clock: Clock | None = None) -> None:
        self._uow = uow
        self._clock = clock

    def execute(self, id_delegacion: int, id_usuario: int) -> Delegation:
        def operation() -> Delegation:
            require_bioquimico(self._uow, id_usuario)
            delegation = self._uow.delegations.get_by_id(id_delegacion)
            if delegation is None:
                raise EntityNotFound("Delegación no encontrada.")
            if id_usuario not in {delegation.id_usuario_autor, delegation.id_usuario_colaborador}:
                raise PermissionDenied("El usuario no participa en esta delegación.")
            if not delegation.activa:
                raise InvalidState("La delegación ya está finalizada.")
            delegation.activa = False
            delegation.finalizada_en = self._clock.now() if self._clock else datetime.now(timezone.utc)
            saved = self._uow.delegations.save(delegation)
            order = get_order(self._uow, delegation.id_orden)
            record_event(
                self._uow,
                "DELEGACION_FINALIZADA",
                id_usuario,
                order=order,
                new={"id_delegacion": id_delegacion},
            )
            return saved

        return atomic(self._uow, operation)