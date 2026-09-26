from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Date, CHAR, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.adapters.db.session import Base

class RolModel(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "laboratorio"}

    id_rol = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    permisos = Column(JSON, nullable=False, default={})

class UsuarioModel(Base):
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "laboratorio"}

    id_usuario = Column(Integer, primary_key=True, index=True)
    id_rol = Column(Integer, ForeignKey("laboratorio.roles.id_rol"), nullable=False)
    ci = Column(String(20), unique=True, nullable=False)
    nombre_completo = Column(String(150), nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    hash_password = Column(String(255), nullable=False)
    foto_perfil_url = Column(String(255), default=None)
    activo = Column(Boolean, default=True)
    intentos_fallidos_login = Column(Integer, default=0)

    rol = relationship("RolModel")

class PacienteModel(Base):
    __tablename__ = "pacientes"
    __table_args__ = {"schema": "laboratorio"}

    id_paciente = Column(Integer, primary_key=True, index=True)
    ci = Column(String(20), unique=True, nullable=False)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    sexo = Column(CHAR(1), nullable=False)
    telefono = Column(String(20))
    correo = Column(String(100))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    ordenes = relationship("OrdenExamenModel", back_populates="paciente")


class OrdenExamenModel(Base):
    __tablename__ = "ordenes_examen"
    __table_args__ = {"schema": "laboratorio"}

    id_orden = Column(Integer, primary_key=True, index=True)
    id_paciente = Column(Integer, ForeignKey("laboratorio.pacientes.id_paciente"), nullable=False)
    id_usuario_creador = Column(Integer, ForeignKey("laboratorio.usuarios.id_usuario"), nullable=False)
    medico_solicitante = Column(String(150), nullable=False)
    pieza_cama = Column(String(50), nullable=True)
    fecha_recepcion = Column(DateTime(timezone=True), server_default=func.now())
    estado = Column(String(30), nullable=False, default="BORRADOR")

    paciente = relationship("PacienteModel", back_populates="ordenes")
    usuario_creador = relationship("UsuarioModel")
    resultados = relationship("ResultadoModuloModel", back_populates="orden")


class ResultadoModuloModel(Base):
    __tablename__ = "resultados_modulo"
    __table_args__ = {"schema": "laboratorio"}

    id_resultado = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey("laboratorio.ordenes_examen.id_orden"), nullable=False)
    codigo_modulo = Column(String(50), nullable=False)
    valores_entrada = Column(JSON, nullable=False)
    valores_calculados = Column(JSON, nullable=False)
    advertencias = Column(JSON, nullable=True)
    id_usuario_validador = Column(Integer, ForeignKey("laboratorio.usuarios.id_usuario"), nullable=True)
    fecha_validacion = Column(DateTime(timezone=True), nullable=True)

    orden = relationship("OrdenExamenModel", back_populates="resultados")
    validador = relationship("UsuarioModel")


class AuditoriaEnmiendaModel(Base):
    __tablename__ = "auditoria_enmiendas"
    __table_args__ = {"schema": "laboratorio"}

    id_enmienda = Column(Integer, primary_key=True, index=True)
    id_orden = Column(Integer, ForeignKey("laboratorio.ordenes_examen.id_orden"), nullable=False)
    id_resultado = Column(Integer, ForeignKey("laboratorio.resultados_modulo.id_resultado"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("laboratorio.usuarios.id_usuario"), nullable=False)
    motivo = Column(Text, nullable=False)
    valores_previos = Column(JSON, nullable=False)
    valores_nuevos = Column(JSON, nullable=False)
    fecha_enmienda = Column(DateTime(timezone=True), server_default=func.now())

    orden = relationship("OrdenExamenModel")
    usuario = relationship("UsuarioModel")
    resultado = relationship("ResultadoModuloModel")