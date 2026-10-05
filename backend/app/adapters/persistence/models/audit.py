from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .catalog import ParametroModel
    from .identity import UsuarioModel
    from .orders import OrdenEstudioModel, OrdenModel
    from .results import ResultadoVersionModel


class AuditoriaModel(Base):
    __tablename__ = "auditoria"
    __table_args__ = (
        Index("idx_auditoria_usuario", "id_usuario"),
        Index("idx_auditoria_orden", "id_orden"),
        Index("idx_auditoria_orden_estudio", "id_orden_estudio"),
        Index("idx_auditoria_fecha", "creado_en"),
        Index("idx_auditoria_accion", "accion"),
        {"schema": SCHEMA},
    )

    id_auditoria: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"))
    id_orden: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.ordenes.id_orden"))
    id_orden_estudio: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.orden_estudios.id_orden_estudio"))
    id_resultado_version: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.resultado_versiones.id_resultado_version"))
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad: Mapped[str | None] = mapped_column(String(50))
    descripcion: Mapped[str | None] = mapped_column(Text)
    datos_anteriores: Mapped[dict | None] = mapped_column(JSONB)
    datos_nuevos: Mapped[dict | None] = mapped_column(JSONB)
    ip_origen: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    usuario: Mapped[UsuarioModel | None] = relationship()
    orden: Mapped[OrdenModel | None] = relationship()
    orden_estudio: Mapped[OrdenEstudioModel | None] = relationship()
    resultado_version: Mapped[ResultadoVersionModel | None] = relationship()


class CambioResultadoModel(Base):
    __tablename__ = "cambios_resultado"
    __table_args__ = (
        Index("idx_cambios_resultado_version", "id_resultado_version"),
        Index("idx_cambios_resultado_usuario", "id_usuario"),
        Index("idx_cambios_resultado_parametro", "id_parametro"),
        {"schema": SCHEMA},
    )

    id_cambio: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_resultado_version: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.resultado_versiones.id_resultado_version", ondelete="RESTRICT"), nullable=False)
    id_parametro: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.parametros.id_parametro", ondelete="RESTRICT"))
    id_usuario: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario", ondelete="RESTRICT"), nullable=False)
    valor_anterior: Mapped[str | None] = mapped_column(Text)
    valor_nuevo: Mapped[str | None] = mapped_column(Text)
    comentario: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    resultado_version: Mapped[ResultadoVersionModel] = relationship()
    parametro: Mapped[ParametroModel | None] = relationship()
    usuario: Mapped[UsuarioModel] = relationship()


class PapeleraOrdenModel(Base):
    __tablename__ = "papelera_ordenes"
    __table_args__ = (
        Index("idx_papelera_eliminado_por", "eliminado_por"),
        Index("idx_papelera_fecha", "creado_en"),
        Index("idx_papelera_restaurado", "restaurado"),
        {"schema": SCHEMA},
    )

    id_papelera: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_orden: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.ordenes.id_orden", ondelete="RESTRICT"), nullable=False, unique=True)
    eliminado_por: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"), nullable=False)
    estado_anterior: Mapped[str] = mapped_column(String(20), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    restaurado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    restaurado_por: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"))
    restaurado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    orden: Mapped[OrdenModel] = relationship(back_populates="papelera")
    eliminador: Mapped[UsuarioModel] = relationship(foreign_keys=[eliminado_por])
    restaurador: Mapped[UsuarioModel | None] = relationship(foreign_keys=[restaurado_por])


class AuditoriaSeguridadModel(Base):
    __tablename__ = "auditoria_seguridad"
    __table_args__ = (
        Index("idx_seguridad_usuario", "id_usuario"),
        Index("idx_seguridad_evento", "evento"),
        Index("idx_seguridad_fecha", "creado_en"),
        {"schema": SCHEMA},
    )

    id_evento: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_usuario: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"))
    evento: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_origen: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
    detalles: Mapped[dict | None] = mapped_column(JSONB)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    usuario: Mapped[UsuarioModel | None] = relationship()