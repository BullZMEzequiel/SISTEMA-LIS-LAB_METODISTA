from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.entities import DelegationMode


ClinicalValue = Decimal | str | bool | None


class UserResponse(BaseModel):
    id_usuario: int
    nombre_completo: str
    correo: str | None
    rol: str
    foto_perfil_url: str | None = None


class MeResponse(UserResponse):
    ci: str


class PatientCreateRequest(BaseModel):
    ci: str = Field(min_length=1, max_length=30)
    nombres: str = Field(min_length=1, max_length=100)
    apellido_paterno: str | None = Field(default=None, max_length=100)
    apellido_materno: str | None = Field(default=None, max_length=100)
    apellidos: str | None = None
    fecha_nacimiento: date
    sexo: str = Field(min_length=1, max_length=1)
    telefono: str | None = None
    correo: str | None = None

    @model_validator(mode="after")
    def split_legacy_surnames(self) -> "PatientCreateRequest":
        if self.apellido_paterno:
            return self
        parts = (self.apellidos or "").strip().split(maxsplit=1)
        if parts:
            self.apellido_paterno = parts[0]
            self.apellido_materno = self.apellido_materno or (parts[1] if len(parts) > 1 else None)
        return self


class PatientUpdateRequest(BaseModel):
    ci: str | None = Field(default=None, max_length=30)
    nombres: str | None = Field(default=None, max_length=100)
    apellido_paterno: str | None = Field(default=None, max_length=100)
    apellido_materno: str | None = Field(default=None, max_length=100)
    fecha_nacimiento: date | None = None
    sexo: str | None = Field(default=None, min_length=1, max_length=1)
    telefono: str | None = None
    correo: str | None = None


class PatientResponse(BaseModel):
    id_paciente: int
    ci: str
    nombres: str
    apellido_paterno: str
    apellido_materno: str | None
    apellidos: str
    fecha_nacimiento: date
    sexo: str
    telefono: str | None
    correo: str | None
    creado_en: datetime | None = None


class StudyResponse(BaseModel):
    id_estudio: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    id_estudio_version: int
    numero_version: int
    estrategia_calculo: str | None = None
    parametros_obligatorios: list[str]


class PanelResponse(BaseModel):
    id_panel: int
    codigo: str
    nombre: str
    descripcion: str | None = None


class OrderCreateRequest(BaseModel):
    id_paciente: int
    ids_estudio: list[int] = Field(min_length=1)
    pieza: str | None = Field(default=None, max_length=100)


class OrderDraftUpdateRequest(BaseModel):
    pieza: str | None = Field(default=None, max_length=100)
    comentario_general: str | None = None


class OrderStudyResponse(BaseModel):
    id_orden_estudio: int | None
    id_estudio: int
    id_estudio_version: int
    estado: str
    observaciones: str | None = None


class OrderResponse(BaseModel):
    id_orden: int
    folio: str
    id_paciente: int
    id_usuario_autor: int
    pieza: str | None
    estado: str
    comentario_general: str | None = None
    creado_en: datetime | None
    actualizado_en: datetime | None = None
    oficializado_en: datetime | None
    estudios: list[OrderStudyResponse]
    paciente: PatientResponse | None = None


class AddStudyRequest(BaseModel):
    id_estudio: int


class SaveDraftRequest(BaseModel):
    entradas: dict[str, ClinicalValue]
    comentario: str | None = None


class CalculateResponse(BaseModel):
    id_resultado_version: int | None
    id_orden_estudio: int
    numero_version: int
    estado: str
    entradas: dict[str, ClinicalValue]
    calculados: dict[str, ClinicalValue]
    advertencias: list[str]


class DelegationRequest(BaseModel):
    id_usuario_colaborador: int
    modalidad: DelegationMode
    ids_estudio: list[int] = []
    comentario: str | None = None


class DelegationResponse(BaseModel):
    id_delegacion: int
    id_orden: int
    id_usuario_autor: int
    id_usuario_colaborador: int
    modalidad: str
    estudios: list[int]
    activa: bool
    aceptada: bool
    creada_en: datetime | None
    finalizada_en: datetime | None


class CorrectionRequest(BaseModel):
    id_orden_estudio: int
    motivo: str = Field(min_length=10)
    nuevas_entradas: dict[str, ClinicalValue]


class TrashRequest(BaseModel):
    motivo: str = Field(min_length=1, max_length=2000)


class ResultVersionResponse(BaseModel):
    id_resultado_version: int | None
    id_orden_estudio: int
    numero_version: int
    creado_por: int
    estado: str
    motivo_correccion: str | None
    creado_en: datetime | None
    oficializado_en: datetime | None
    entradas: dict[str, ClinicalValue]
    calculados: dict[str, ClinicalValue]
    advertencias: list[str]
    snapshot_completo: dict[str, Any]


class ResultChangeResponse(BaseModel):
    id_parametro: int | None
    codigo_parametro: str
    id_orden_estudio: int | None
    numero_version: int | None
    valor_anterior: str | None
    valor_nuevo: str | None
    comentario: str
    id_usuario: int
    creado_en: datetime | None


class AuditEventResponse(BaseModel):
    id_auditoria: int | None = None
    id_usuario: int
    id_orden: int | None
    id_orden_estudio: int | None
    id_resultado_version: int | None
    accion: str
    entidad: str | None
    entidad_id: int | None
    descripcion: str | None
    creado_en: datetime | None = None


class SecurityAuditEventResponse(BaseModel):
    id_evento: int
    id_usuario: int | None
    evento: str
    ip_origen: str | None
    user_agent: str | None
    detalles: dict[str, Any] | None
    creado_en: datetime


class TrashRestoreResponse(BaseModel):
    id_orden: int
    folio: str
    estado: str
    eliminado_por: int | None
    eliminado_en: datetime | None
    motivo: str | None


class HistoryQuery(BaseModel):
    paciente_ci: str | None = None
    nombre: str | None = None
    folio: str | None = None
    desde: date | None = None
    hasta: date | None = None
    id_estudio: int | None = None
    id_usuario_autor: int | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "HistoryQuery":
        if self.desde and self.hasta and self.desde > self.hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")
        return self