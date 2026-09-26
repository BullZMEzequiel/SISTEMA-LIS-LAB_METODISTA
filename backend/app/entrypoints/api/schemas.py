from datetime import date, datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: dict


class PacienteCreate(BaseModel):
    ci: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    sexo: str = Field(..., max_length=1, description="'M' o 'F'")
    telefono: Optional[str] = None
    correo: Optional[str] = None


class PacienteResponse(PacienteCreate):
    id_paciente: int
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class CalculationRequest(BaseModel):
    codigo_modulo: str
    entradas: Dict[str, Any]


class GuardarOrdenRequest(BaseModel):
    id_paciente: Optional[int] = None
    paciente_nuevo: Optional[PacienteCreate] = None
    medico_solicitante: str
    pieza_cama: Optional[str] = None
    codigo_modulo: str
    valores_entrada: Dict[str, Any]
    estado_solicitado: str = "BORRADOR"
    id_usuario_creador: Optional[int] = None
    rol_usuario: Optional[str] = None


class GuardarOrdenResponse(BaseModel):
    id_orden: int
    id_paciente: int
    codigo_modulo: str
    estado: str
    calculados: Dict[str, Any]
    advertencias: list[str] = []