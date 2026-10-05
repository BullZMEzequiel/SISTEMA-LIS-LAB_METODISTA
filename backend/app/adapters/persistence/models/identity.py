from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CHAR, Date, DateTime, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint, CheckConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .collaboration import DelegacionModel
    from .orders import OrdenModel
    from .results import ResultadoVersionModel


class RolModel(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": SCHEMA}

    id_rol: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    usuarios: Mapped[list[UsuarioModel]] = relationship(back_populates="rol")


class UsuarioModel(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        Index("idx_usuarios_rol", "id_rol"),
        Index("idx_usuarios_activo", "activo"),
        {"schema": SCHEMA},
    )

    id_usuario: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_rol: Mapped[int] = mapped_column(SmallInteger, ForeignKey(f"{SCHEMA}.roles.id_rol"), nullable=False)
    ci: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_materno: Mapped[str | None] = mapped_column(String(100))
    correo: Mapped[str | None] = mapped_column(String(150), unique=True)
    hash_password: Mapped[str] = mapped_column(String(255), nullable=False)
    foto_perfil_url: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    ultimo_ingreso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rol: Mapped[RolModel] = relationship(back_populates="usuarios")
    pacientes_creados: Mapped[list[PacienteModel]] = relationship(foreign_keys="PacienteModel.creado_por", back_populates="creador")
    ordenes_autor: Mapped[list[OrdenModel]] = relationship(foreign_keys="OrdenModel.id_usuario_autor")
    delegaciones_autor: Mapped[list[DelegacionModel]] = relationship(foreign_keys="DelegacionModel.id_usuario_autor")
    delegaciones_recibidas: Mapped[list[DelegacionModel]] = relationship(foreign_keys="DelegacionModel.id_usuario_colaborador")
    versiones_creadas: Mapped[list[ResultadoVersionModel]] = relationship(foreign_keys="ResultadoVersionModel.creado_por")


class PacienteModel(Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        CheckConstraint("sexo IN ('M', 'F')"),
        Index("idx_pacientes_ci", "ci"),
        Index("idx_pacientes_nombre", "apellido_paterno", "apellido_materno", "nombres"),
        Index("idx_pacientes_fecha_nacimiento", "fecha_nacimiento"),
        {"schema": SCHEMA},
    )

    id_paciente: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ci: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_paterno: Mapped[str] = mapped_column(String(100), nullable=False)
    apellido_materno: Mapped[str | None] = mapped_column(String(100))
    fecha_nacimiento: Mapped[date] = mapped_column(Date, nullable=False)
    sexo: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(30))
    correo: Mapped[str | None] = mapped_column(String(150))
    creado_por: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creador: Mapped[UsuarioModel | None] = relationship(foreign_keys=[creado_por], back_populates="pacientes_creados")
    ordenes: Mapped[list[OrdenModel]] = relationship(back_populates="paciente")