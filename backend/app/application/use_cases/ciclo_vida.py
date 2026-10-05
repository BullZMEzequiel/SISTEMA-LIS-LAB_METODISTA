from app.application.ports import Clock, PdfPort, UnitOfWork
from app.application.use_cases._support import atomic, get_order, record_event, require_order_author
from app.domain.entities import Order, OrderStatus
from app.domain.exceptions import EntityNotFound, InvalidState, ValidationError


class MoverOrdenAPapelera:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def execute(self, id_orden: int, id_usuario: int, motivo: str) -> Order:
        reason = motivo.strip()
        if not reason:
            raise ValidationError("El motivo para mover la orden a papelera es obligatorio.")

        def operation() -> Order:
            order = get_order(self._uow, id_orden)
            require_order_author(self._uow, order, id_usuario)
            if order.estado is not OrderStatus.OFFICIAL:
                raise InvalidState("Solo las órdenes oficiales pueden moverse a papelera.")
            order.estado_anterior_papelera = order.estado
            order.estado = OrderStatus.TRASH
            order.eliminado_por = id_usuario
            order.eliminado_en = self._clock.now()
            order.motivo_papelera = reason
            saved = self._uow.orders.save(order)
            record_event(
                self._uow,
                "ORDEN_A_PAPELERA",
                id_usuario,
                order=order,
                descripcion=reason,
                old={"estado": OrderStatus.OFFICIAL.value},
                new={"estado": OrderStatus.TRASH.value},
            )
            return saved

        return atomic(self._uow, operation)


class RestaurarOrden:
    def __init__(self, uow: UnitOfWork, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    def execute(self, id_orden: int, id_usuario: int) -> Order:
        def operation() -> Order:
            order = get_order(self._uow, id_orden)
            require_order_author(self._uow, order, id_usuario)
            if order.estado is not OrderStatus.TRASH:
                raise InvalidState("La orden no está en papelera.")
            order.estado = order.estado_anterior_papelera or OrderStatus.OFFICIAL
            order.eliminado_por = None
            order.eliminado_en = None
            order.motivo_papelera = None
            order.restaurado = True
            order.restaurado_por = id_usuario
            order.restaurado_en = self._clock.now()
            saved = self._uow.orders.save(order)
            record_event(
                self._uow,
                "ORDEN_RESTAURADA",
                id_usuario,
                order=order,
                new={"estado": order.estado.value, "restaurado_en": self._clock.now().isoformat()},
            )
            return saved

        return atomic(self._uow, operation)


class GenerarPDF:
    def __init__(self, uow: UnitOfWork, pdf: PdfPort) -> None:
        self._uow = uow
        self._pdf = pdf

    def execute(self, id_orden: int) -> bytes:
        order = get_order(self._uow, id_orden)
        if order.estado is not OrderStatus.OFFICIAL:
            raise InvalidState("Solo se puede generar PDF de una orden oficial.")
        results = self._uow.results.latest_official_order_results(id_orden)
        if not results:
            raise EntityNotFound("La orden no tiene resultados oficiales.")
        return self._pdf.render_official(order, results)