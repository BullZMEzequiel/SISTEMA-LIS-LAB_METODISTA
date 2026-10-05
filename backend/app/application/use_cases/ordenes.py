from app.application.ports import UnitOfWork
from app.application.use_cases._support import atomic, get_order, record_event, require_edit_access
from app.domain.entities import Order, OrderStatus
from app.domain.exceptions import Conflict, EntityNotFound, InvalidState, ValidationError


class CrearOrden:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        *,
        id_paciente: int,
        id_usuario_autor: int,
        ids_estudio: list[int],
        pieza: str | None = None,
    ) -> Order:
        unique_study_ids = list(dict.fromkeys(ids_estudio))
        if not unique_study_ids:
            raise ValidationError("La orden requiere al menos un estudio.")

        def operation() -> Order:
            patient = self._uow.patients.get_by_id(id_paciente)
            if patient is None or patient.eliminado:
                raise EntityNotFound("Paciente no encontrado.")
            require_edit_access_for_new_order(self._uow, id_usuario_autor)
            study_definitions = []
            for id_estudio in unique_study_ids:
                definition = self._uow.studies.get_active(id_estudio)
                if definition is None:
                    raise EntityNotFound(f"Estudio {id_estudio} no existe o está inactivo.")
                study_definitions.append(definition)
            order = Order(
                id_paciente=id_paciente,
                id_usuario_autor=id_usuario_autor,
                folio=self._uow.orders.next_folio(),
                estudios=[],
                pieza=pieza,
            )
            for study in study_definitions:
                order.add_study(study)
            saved = self._uow.orders.add(order)
            record_event(
                self._uow,
                "ORDEN_CREADA",
                id_usuario_autor,
                order=saved,
                new={"folio": saved.folio, "estudios": unique_study_ids},
            )
            return saved

        return atomic(self._uow, operation)


def require_edit_access_for_new_order(uow: UnitOfWork, id_usuario: int) -> None:
    from app.application.use_cases._support import require_bioquimico

    require_bioquimico(uow, id_usuario)


class AgregarEstudio:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_estudio: int, id_usuario: int) -> Order:
        def operation() -> Order:
            order = get_order(self._uow, id_orden)
            require_edit_access(self._uow, order, id_usuario, id_estudio)
            if order.estado is not OrderStatus.DRAFT:
                raise InvalidState("No se pueden agregar estudios a una orden oficial.")
            if any(item.id_estudio == id_estudio for item in order.estudios):
                raise Conflict("El estudio ya pertenece a la orden.")
            study = self._uow.studies.get_active(id_estudio)
            if study is None:
                raise EntityNotFound("Estudio no encontrado o inactivo.")
            order.add_study(study)
            saved = self._uow.orders.save(order)
            record_event(self._uow, "ESTUDIO_AGREGADO", id_usuario, order=order, new={"id_estudio": id_estudio})
            return saved

        return atomic(self._uow, operation)


class QuitarEstudio:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(self, id_orden: int, id_estudio: int, id_usuario: int) -> Order:
        def operation() -> Order:
            order = get_order(self._uow, id_orden)
            require_edit_access(self._uow, order, id_usuario, id_estudio)
            if order.estado is not OrderStatus.DRAFT:
                raise InvalidState("No se pueden quitar estudios de una orden oficial.")
            assigned = next((item for item in order.estudios if item.id_estudio == id_estudio), None)
            if assigned is None:
                raise EntityNotFound("El estudio no pertenece a la orden.")
            if len(order.estudios) <= 1:
                raise InvalidState("Una orden debe conservar al menos un estudio.")
            if assigned.id_orden_estudio is not None and self._uow.results.get_latest(assigned.id_orden_estudio):
                raise InvalidState("No se puede quitar un estudio que ya tiene resultados.")
            order.remove_study(id_estudio)
            saved = self._uow.orders.save(order)
            record_event(self._uow, "ESTUDIO_QUITADO", id_usuario, order=order, old={"id_estudio": id_estudio})
            return saved

        return atomic(self._uow, operation)


class ActualizarOrdenBorrador:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        id_orden: int,
        id_usuario: int,
        *,
        pieza: str | None = None,
        comentario_general: str | None = None,
    ) -> Order:
        def operation() -> Order:
            order = get_order(self._uow, id_orden)
            require_edit_access(self._uow, order, id_usuario)
            if order.estado is not OrderStatus.DRAFT:
                raise InvalidState("Solo se pueden actualizar metadatos de una orden pendiente.")
            if pieza is not None:
                order.pieza = pieza.strip() or None
            if comentario_general is not None:
                order.comentario_general = comentario_general
            saved = self._uow.orders.save(order)
            record_event(
                self._uow,
                "ORDEN_BORRADOR_ACTUALIZADA",
                id_usuario,
                order=saved,
                new={"pieza": saved.pieza, "comentario_general": saved.comentario_general},
            )
            return saved

        return atomic(self._uow, operation)