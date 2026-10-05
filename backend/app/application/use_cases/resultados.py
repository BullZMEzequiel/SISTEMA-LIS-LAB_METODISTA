from datetime import datetime, timezone

from app.application.ports import CalculationPort, Clock, UnitOfWork
from app.application.use_cases._support import (
    atomic,
    get_order,
    record_event,
    require_edit_access,
    require_order_author,
)
from app.domain.entities import (
    CalculationOutcome,
    Order,
    OrderStatus,
    OrderStudyStatus,
    ResultChange,
    ResultStatus,
    ResultVersion,
    StudyDefinition,
    Value,
)
from app.domain.exceptions import EntityNotFound, InvalidState, ValidationError


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_required_values(
    definition: StudyDefinition,
    entradas: dict[str, Value],
    calculados: dict[str, Value],
) -> None:
    required = definition.parametros_obligatorios
    if not required:
        raise InvalidState(
            f"El estudio {definition.codigo} no tiene parámetros obligatorios configurados."
        )
    available = {
        key for key, value in entradas.items() if value is not None
    } | {
        key for key, value in calculados.items() if value is not None
    }
    missing = set(required) - available
    if missing:
        raise ValidationError(
            f"Faltan campos obligatorios de {definition.codigo}: {', '.join(sorted(missing))}."
        )


class GuardarBorrador:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def execute(
        self,
        *,
        id_orden_estudio: int,
        id_usuario: int,
        entradas: dict[str, Value],
        comentario: str | None = None,
    ) -> ResultVersion:
        def operation() -> ResultVersion:
            assignment = self._uow.orders.get_order_for_study(id_orden_estudio)
            if assignment is None:
                raise EntityNotFound("El estudio asignado no existe.")
            order, order_study = assignment
            require_edit_access(self._uow, order, id_usuario, order_study.id_estudio)
            order.ensure_draft()
            current = self._uow.results.get_draft(id_orden_estudio)
            if current is None:
                latest = self._uow.results.get_latest(id_orden_estudio)
                if latest is not None:
                    raise InvalidState("El estudio ya tiene una versión; cree una corrección en lugar de editarla.")
                current = ResultVersion(
                    id_orden_estudio=id_orden_estudio,
                    numero_version=1,
                    id_estudio_version=order_study.id_estudio_version,
                    creado_por=id_usuario,
                )
            current.entradas = dict(entradas)
            current.comentario_estudio = comentario
            saved = self._uow.results.save_draft(current)
            record_event(
                self._uow,
                "BORRADOR_GUARDADO",
                id_usuario,
                order=order,
                id_orden_estudio=id_orden_estudio,
                id_resultado_version=saved.id_resultado_version,
            )
            return saved

        return atomic(self._uow, operation)


class CalcularEstudio:
    def __init__(self, uow: UnitOfWork, calculation: CalculationPort) -> None:
        self._uow = uow
        self._calculation = calculation

    def execute(self, id_orden_estudio: int, id_usuario: int) -> ResultVersion:
        def operation() -> ResultVersion:
            assignment = self._uow.orders.get_order_for_study(id_orden_estudio)
            if assignment is None:
                raise EntityNotFound("El estudio asignado no existe.")
            order, order_study = assignment
            require_edit_access(self._uow, order, id_usuario, order_study.id_estudio)
            order.ensure_draft()
            draft = self._uow.results.get_draft(id_orden_estudio)
            if draft is None:
                raise InvalidState("Guarde las entradas del estudio antes de calcular.")
            definition = self._uow.studies.get_version(order_study.id_estudio_version)
            if definition is None:
                raise EntityNotFound("No existe la versión de configuración asignada al estudio.")
            outcome = CalculationOutcome(calculados={})
            if definition.estrategia_calculo:
                outcome = self._calculation.calculate(definition.estrategia_calculo, draft.entradas)
            draft.calculados = dict(outcome.calculados)
            draft.advertencias = list(outcome.advertencias)
            saved = self._uow.results.save_draft(draft)
            record_event(
                self._uow,
                "ESTUDIO_CALCULADO",
                id_usuario,
                order=order,
                id_orden_estudio=id_orden_estudio,
                id_resultado_version=saved.id_resultado_version,
            )
            return saved

        return atomic(self._uow, operation)


class OficializarOrden:
    def __init__(self, uow: UnitOfWork, calculation: CalculationPort, clock: Clock | None = None) -> None:
        self._uow = uow
        self._calculation = calculation
        self._clock = clock

    def execute(self, id_orden: int, id_usuario: int) -> Order:
        def operation() -> Order:
            order = get_order(self._uow, id_orden)
            require_order_author(self._uow, order, id_usuario)
            is_correction = order.estado is OrderStatus.OFFICIAL
            if not order.estudios:
                raise InvalidState("No se puede oficializar una orden sin estudios.")
            now = self._clock.now() if self._clock else _utc_now()
            officialized = 0
            for assigned in order.estudios:
                if assigned.id_orden_estudio is None:
                    raise InvalidState("La orden contiene un estudio aún no persistido.")
                latest = self._uow.results.get_latest(assigned.id_orden_estudio)
                if latest is None:
                    raise InvalidState("Todos los estudios deben tener un resultado guardado.")
                if latest.estado is ResultStatus.OFFICIAL:
                    continue
                if latest.estado is not ResultStatus.DRAFT:
                    raise InvalidState("El resultado más reciente no puede oficializarse.")
                definition = self._uow.studies.get_version(latest.id_estudio_version)
                if definition is None:
                    raise EntityNotFound("No existe la configuración utilizada por el resultado.")
                if definition.estrategia_calculo:
                    outcome = self._calculation.calculate(definition.estrategia_calculo, latest.entradas)
                    latest.calculados = dict(outcome.calculados)
                    latest.advertencias = list(outcome.advertencias)
                _validate_required_values(definition, latest.entradas, latest.calculados)
                latest.snapshot_completo = {
                    "codigo_estudio": definition.codigo,
                    "nombre_estudio": definition.nombre,
                    "id_estudio_version": definition.id_estudio_version,
                    "numero_version_configuracion": definition.numero_version,
                    "estrategia_calculo": definition.estrategia_calculo,
                    "configuracion": dict(definition.configuracion),
                    "unidades": dict(definition.unidades),
                    "referencias": dict(definition.referencias),
                    "entradas": dict(latest.entradas),
                    "calculados": dict(latest.calculados),
                    "advertencias": list(latest.advertencias),
                }
                previous_versions = self._uow.results.list_versions(assigned.id_orden_estudio)
                for previous in previous_versions:
                    if previous.id_resultado_version != latest.id_resultado_version and previous.estado is ResultStatus.OFFICIAL:
                        previous.estado = ResultStatus.SUPERSEDED
                        self._uow.results.save(previous)
                latest.mark_official(now)
                self._uow.results.save(latest)
                assigned.estado = OrderStudyStatus.OFFICIAL
                officialized += 1

            if order.estado is not OrderStatus.DRAFT and officialized == 0:
                raise InvalidState("La orden no contiene una corrección pendiente de oficializar.")
            order.estado = OrderStatus.OFFICIAL
            order.oficializado_en = now
            saved = self._uow.orders.save(order)
            record_event(
                self._uow,
                "CORRECCION_OFICIALIZADA" if is_correction else "ORDEN_OFICIALIZADA",
                id_usuario,
                order=order,
                new={"oficializado_en": now.isoformat(), "versiones": officialized},
            )
            return saved

        return atomic(self._uow, operation)


class CrearCorreccion:
    def __init__(self, uow: UnitOfWork, calculation: CalculationPort) -> None:
        self._uow = uow
        self._calculation = calculation

    def execute(
        self,
        *,
        id_orden_estudio: int,
        id_usuario: int,
        motivo: str,
        nuevas_entradas: dict[str, Value],
    ) -> ResultVersion:
        reason = motivo.strip()
        if len(reason) < 10:
            raise ValidationError("El motivo de corrección debe tener al menos 10 caracteres.")

        def operation() -> ResultVersion:
            assignment = self._uow.orders.get_order_for_study(id_orden_estudio)
            if assignment is None:
                raise EntityNotFound("El estudio asignado no existe.")
            order, order_study = assignment
            require_order_author(self._uow, order, id_usuario)
            if order.estado is not OrderStatus.OFFICIAL:
                raise InvalidState("Solo se pueden corregir resultados oficializados.")
            latest = self._uow.results.get_latest(id_orden_estudio)
            if latest is None or latest.estado is not ResultStatus.OFFICIAL:
                raise InvalidState("La última versión del resultado no es oficial.")
            definition = self._uow.studies.get_version(latest.id_estudio_version)
            if definition is None:
                raise EntityNotFound("No existe la configuración usada por el resultado oficial.")
            outcome = CalculationOutcome(calculados={})
            if definition.estrategia_calculo:
                outcome = self._calculation.calculate(definition.estrategia_calculo, nuevas_entradas)
            _validate_required_values(definition, nuevas_entradas, outcome.calculados)
            corrected = ResultVersion(
                id_orden_estudio=id_orden_estudio,
                numero_version=latest.numero_version + 1,
                id_estudio_version=latest.id_estudio_version,
                creado_por=id_usuario,
                entradas=dict(nuevas_entradas),
                calculados=dict(outcome.calculados),
                advertencias=list(outcome.advertencias),
                motivo_correccion=reason,
                snapshot_completo={
                    "codigo_estudio": definition.codigo,
                    "nombre_estudio": definition.nombre,
                    "id_estudio_version": definition.id_estudio_version,
                    "numero_version_configuracion": definition.numero_version,
                    "estrategia_calculo": definition.estrategia_calculo,
                    "configuracion": dict(definition.configuracion),
                    "unidades": dict(definition.unidades),
                    "referencias": dict(definition.referencias),
                    "entradas": dict(nuevas_entradas),
                    "calculados": dict(outcome.calculados),
                    "advertencias": list(outcome.advertencias),
                },
            )
            old_values = {**latest.entradas, **latest.calculados}
            new_values = {**corrected.entradas, **corrected.calculados}
            changes = [
                ResultChange(
                    id_parametro=definition.parameter_ids.get(key),
                    codigo_parametro=key,
                    valor_anterior=str(old_values.get(key)) if key in old_values else None,
                    valor_nuevo=str(new_values.get(key)) if key in new_values else None,
                    comentario=reason,
                    id_usuario=id_usuario,
                )
                for key in sorted(set(old_values) | set(new_values))
                if old_values.get(key) != new_values.get(key)
            ]
            saved = self._uow.results.add_correction(corrected, changes)
            record_event(
                self._uow,
                "CORRECCION_CREADA",
                id_usuario,
                order=order,
                id_orden_estudio=id_orden_estudio,
                id_resultado_version=saved.id_resultado_version,
                descripcion=reason,
                old={"version": latest.numero_version},
                new={"version": saved.numero_version},
            )
            return saved

        return atomic(self._uow, operation)

