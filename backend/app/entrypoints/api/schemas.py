from datetime import date, datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    usuario: str
    password: str


class AdminUsuarioCreate(BaseModel):
    ci: str
    nombre_completo: str
    correo: Optional[str] = None
    id_rol: int
    password: str
    activo: bool = True


class AdminUsuarioUpdate(BaseModel):
    ci: Optional[str] = None
    nombre_completo: Optional[str] = None
    correo: Optional[str] = None
    id_rol: Optional[int] = None
    activo: Optional[bool] = None


class AdminUsuarioResetPassword(BaseModel):
    nueva_password: str


class AdminUsuarioResponse(BaseModel):
    id_usuario: int
    ci: str
    nombre_completo: str
    correo: Optional[str] = None
    id_rol: int
    rol: Optional[str] = None
    activo: bool

    model_config = ConfigDict(from_attributes=True)


class AuditoriaAdminResponse(BaseModel):
    id_enmienda: int
    id_orden: int
    id_resultado: Optional[int] = None
    modulo: Optional[str] = None
    usuario_solicitante: Optional[str] = None
    rol_usuario: Optional[str] = None
    fecha: Optional[str] = None
    motivo: Optional[str] = None
    estado: Optional[str] = None


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


class DelegarOrdenRequest(BaseModel):
    id_orden: int
    id_usuario_destino: int
    observacion: Optional[str] = None
    
class PacienteCreate(BaseModel):
    ci: str
    nombres: str
    apellido_paterno: str
    apellido_materno: Optional[str] = None
    fecha_nacimiento: date
    sexo: str = Field(pattern="^[MF]$")
    telefono: Optional[str] = None
    correo: Optional[str] = None
 
 
class PacienteUpdate(BaseModel):
    nombres: Optional[str] = None
    apellido_paterno: Optional[str] = None
    apellido_materno: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = Field(default=None, pattern="^[MF]$")
    telefono: Optional[str] = None
    correo: Optional[str] = None
 
 
class PacienteResponse(BaseModel):
    id_paciente: int
    ci: str
    nombres: str
    apellido_paterno: str
    apellido_materno: Optional[str]
    fecha_nacimiento: date
    sexo: str
    telefono: Optional[str]
    correo: Optional[str]
 
    class Config:
        from_attributes = True
 
