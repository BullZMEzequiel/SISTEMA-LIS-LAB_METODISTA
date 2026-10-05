from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .identity import UsuarioModel
    from .orders import OrdenEstudioModel, OrdenModel


class DelegacionModel(Base):
    __tablename__ = "delegaciones"
    __table_args__ = (
        CheckConstraint("modalidad IN ('TRABAJO_COMPLETO', 'POR_ESTUDIO')"),
        CheckConstraint("id_usuario_autor <> id_usuario_colaborador"),
        Index("idx_delegaciones_orden", "id_orden"),
        Index("idx_delegaciones_autor", "id_usuario_autor"),
        Index("idx_delegaciones_colaborador", "id_usuario_colaborador"),
        Index("uq_delegacion_activa_por_orden", "id_orden", unique=True, postgresql_where=text("activa = TRUE")),
        {"schema": SCHEMA},
    )

    id_delegacion: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_orden: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.ordenes.id_orden", ondelete="RESTRICT"), nullable=False)
    id_usuario_autor: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario", ondelete="RESTRICT"), nullable=False)
    id_usuario_colaborador: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario", ondelete="RESTRICT"), nullable=False)
    modalidad: Mapped[str] = mapped_column(String(30), nullable=False)
    comentario: Mapped[str | None] = mapped_column(Text)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("NOW()"))
    finalizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    orden: Mapped[OrdenModel] = relationship(back_populates="delegaciones")
    autor: Mapped[UsuarioModel] = relationship(foreign_keys=[id_usuario_autor], back_populates="delegaciones_autor")
    colaborador: Mapped[UsuarioModel] = relationship(foreign_keys=[id_usuario_colaborador], back_populates="delegaciones_recibidas")
    estudios: Mapped[list[DelegacionEstudioModel]] = relationship(back_populates="delegacion")


class DelegacionEstudioModel(Base):
    __tablename__ = "delegacion_estudios"
    __table_args__ = {"schema": SCHEMA}

    id_delegacion: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.delegaciones.id_delegacion", ondelete="CASCADE"), primary_key=True)
    id_orden_estudio: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.orden_estudios.id_orden_estudio", ondelete="RESTRICT"), primary_key=True)

    delegacion: Mapped[DelegacionModel] = relationship(back_populates="estudios")
    orden_estudio: Mapped[OrdenEstudioModel] = relationship()