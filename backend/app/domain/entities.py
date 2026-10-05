from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias

from app.domain.exceptions import Conflict, InvalidState

Value: TypeAlias = Decimal | str | bool | None


class OrderStatus(StrEnum):
    DRAFT = "BORRADOR"
    OFFICIAL = "OFICIAL"
    TRASH = "PAPELERA"


class OrderStudyStatus(StrEnum):
    DRAFT = "BORRADOR"
    OFFICIAL = "OFICIAL"
    CANCELED = "ANULADO"


class ResultStatus(StrEnum):
    DRAFT = "BORRADOR"
    OFFICIAL = "OFICIAL"
    SUPERSEDED = "SUPERADA"
    CANCELED = "ANULADA"


class DelegationMode(StrEnum):
    COMPLETE = "TRABAJO_COMPLETO"
    STUDIES = "POR_ESTUDIO"


@dataclass(slots=True)
class Patient:
    ci: str
    nombres: str
    apellido_paterno: str
    fecha_nacimiento: date
    sexo: str
    id_paciente: int | None = None
    apellido_materno: str | None = None
    telefono: str | None = None
    correo: str | None = None
    creado_por: int | None = None
    creado_en: datetime | None = None
    eliminado: bool = False


@dataclass(frozen=True, slots=True)
class StudyDefinition:
    id_estudio: int
    codigo: str
    nombre: str
    id_estudio_version: int
    numero_version: int
    estrategia_calculo: str | None = None
    parametros_obligatorios: tuple[str, ...] = ()
    parameter_ids: dict[str, int] = field(default_factory=dict)
    unidades: dict[str, str] = field(default_factory=dict)
    referencias: dict[str, str] = field(default_factory=dict)
    configuracion: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PanelDefinition:
    id_panel: int
    codigo: str
    nombre: str
    descripcion: str | None = None


@dataclass(slots=True)
class OrderStudy:
    id_estudio: int
    id_estudio_version: int
    id_orden_estudio: int | None = None
    estado: OrderStudyStatus = OrderStudyStatus.DRAFT
    observaciones: str | None = None


@dataclass(slots=True)
class Order:
    id_paciente: int
    id_usuario_autor: int
    folio: str
    estudios: list[OrderStudy]
    id_orden: int | None = None
    pieza: str | None = None
    estado: OrderStatus = OrderStatus.DRAFT
    comentario_general: str | None = None
    creado_en: datetime | None = None
    oficializado_en: datetime | None = None
    eliminado_por: int | None = None
    eliminado_en: datetime | None = None
    motivo_papelera: str | None = None
    estado_anterior_papelera: OrderStatus | None = None
    restaurado: bool = False
    restaurado_por: int | None = None
    restaurado_en: datetime | None = None
    paciente: Patient | None = None

    def add_study(self, study: StudyDefinition) -> OrderStudy:
        self.ensure_draft()
        if any(item.id_estudio == study.id_estudio for item in self.estudios):
            raise Conflict("El estudio ya pertenece a la orden.")
        assigned = OrderStudy(
            id_estudio=study.id_estudio,
            id_estudio_version=study.id_estudio_version,
        )
        self.estudios.append(assigned)
        return assigned

    def remove_study(self, id_estudio: int) -> OrderStudy:
        self.ensure_draft()
        if len(self.estudios) <= 1:
            raise InvalidState("Una orden debe conservar al menos un estudio.")
        for index, assigned in enumerate(self.estudios):
            if assigned.id_estudio == id_estudio:
                return self.estudios.pop(index)
        raise InvalidState("El estudio no pertenece a la orden.")

    def ensure_draft(self) -> None:
        if self.estado is not OrderStatus.DRAFT:
            raise InvalidState("La orden ya no está pendiente de edición.")


@dataclass(slots=True)
class ResultVersion:
    id_orden_estudio: int
    numero_version: int
    id_estudio_version: int
    creado_por: int
    entradas: dict[str, Value] = field(default_factory=dict)
    calculados: dict[str, Value] = field(default_factory=dict)
    advertencias: list[str] = field(default_factory=list)
    motivo_correccion: str | None = None
    estado: ResultStatus = ResultStatus.DRAFT
    id_resultado_version: int | None = None
    creado_en: datetime | None = None
    oficializado_en: datetime | None = None
    comentario_estudio: str | None = None
    snapshot_completo: dict[str, object] = field(default_factory=dict)

    def mark_official(self, when: datetime) -> None:
        if self.estado is not ResultStatus.DRAFT:
            raise InvalidState("Solo un borrador puede oficializarse.")
        self.estado = ResultStatus.OFFICIAL
        self.oficializado_en = when


@dataclass(slots=True)
class ResultChange:
    id_parametro: int | None
    codigo_parametro: str
    valor_anterior: str | None
    valor_nuevo: str | None
    comentario: str
    id_usuario: int
    id_orden_estudio: int | None = None
    numero_version: int | None = None
    creado_en: datetime | None = None


@dataclass(slots=True)
class Delegation:
    id_orden: int
    id_usuario_autor: int
    id_usuario_colaborador: int
    modalidad: DelegationMode
    id_delegacion: int | None = None
    estudios: set[int] = field(default_factory=set)
    activa: bool = True
    aceptada: bool = False
    comentario: str | None = None
    creada_en: datetime | None = None
    finalizada_en: datetime | None = None


@dataclass(frozen=True, slots=True)
class AuditEvent:
    accion: str
    id_usuario: int
    id_orden: int | None = None
    id_orden_estudio: int | None = None
    id_resultado_version: int | None = None
    entidad: str | None = None
    entidad_id: int | None = None
    descripcion: str | None = None
    datos_anteriores: dict[str, object] | None = None
    datos_nuevos: dict[str, object] | None = None
    id_auditoria: int | None = None
    creado_en: datetime | None = None


@dataclass(frozen=True, slots=True)
class CalculationOutcome:
    calculados: dict[str, Value]
    advertencias: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class HistoryFilter:
    paciente_ci: str | None = None
    nombre: str | None = None
    folio: str | None = None
    desde: date | None = None
    hasta: date | None = None
    id_estudio: int | None = None
    id_usuario_autor: int | None = None