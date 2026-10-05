from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, Sequence, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .audit import PapeleraOrdenModel
    from .catalog import EstudioModel, EstudioVersionModel
    from .collaboration import DelegacionModel
    from .identity import PacienteModel, UsuarioModel
    from .results import ResultadoVersionModel


class OrdenModel(Base):
    __tablename__ = "ordenes"
    __table_args__ = (
        CheckConstraint("estado IN ('BORRADOR', 'OFICIAL', 'PAPELERA')"),
        Index("idx_ordenes_paciente", "id_paciente"),
        Index("idx_ordenes_autor", "id_usuario_autor"),
        Index("idx_ordenes_estado", "estado"),
        Index("idx_ordenes_creado", "creado_en"),
        Index("idx_ordenes_oficializado", "oficializado_en"),
        Index("idx_ordenes_paciente_fecha", "id_paciente", "creado_en"),
        {"schema": SCHEMA},
    )

    id_orden: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    folio: Mapped[str | None] = mapped_column(String(30), unique=True)
    id_paciente: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.pacientes.id_paciente", ondelete="RESTRICT"), nullable=False)
    id_usuario_autor: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario", ondelete="RESTRICT"), nullable=False)
    pieza: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'BORRADOR'"))
    comentario_general: Mapped[str | None] = mapped_column(Text)
    motivo_papelera: Mapped[str | None] = mapped_column(Text)
    eliminado_por: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"))
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    oficializado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    paciente: Mapped[PacienteModel] = relationship(back_populates="ordenes")
    autor: Mapped[UsuarioModel] = relationship(foreign_keys=[id_usuario_autor], back_populates="ordenes_autor")
    eliminador: Mapped[UsuarioModel | None] = relationship(foreign_keys=[eliminado_por])
    estudios: Mapped[list[OrdenEstudioModel]] = relationship(back_populates="orden")
    delegaciones: Mapped[list[DelegacionModel]] = relationship(back_populates="orden")
    papelera: Mapped[PapeleraOrdenModel | None] = relationship(back_populates="orden", uselist=False)


class OrdenEstudioModel(Base):
    __tablename__ = "orden_estudios"
    __table_args__ = (
        CheckConstraint("estado IN ('BORRADOR', 'OFICIAL', 'ANULADO')"),
        UniqueConstraint("id_orden", "id_estudio"),
        Index("idx_orden_estudios_orden", "id_orden"),
        Index("idx_orden_estudios_estudio", "id_estudio"),
        Index("idx_orden_estudios_estado", "estado"),
        {"schema": SCHEMA},
    )

    id_orden_estudio: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_orden: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.ordenes.id_orden", ondelete="RESTRICT"), nullable=False)
    id_estudio: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.estudios.id_estudio", ondelete="RESTRICT"), nullable=False)
    id_estudio_version: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.estudio_versiones.id_estudio_version", ondelete="RESTRICT"))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'BORRADOR'"))
    observaciones: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    orden: Mapped[OrdenModel] = relationship(back_populates="estudios")
    estudio: Mapped[EstudioModel] = relationship(back_populates="ordenes")
    estudio_version: Mapped[EstudioVersionModel | None] = relationship(back_populates="ordenes_estudio")
    versiones_resultado: Mapped[list[ResultadoVersionModel]] = relationship(back_populates="orden_estudio")


folio_sequence = Sequence("seq_folio_lis", schema=SCHEMA, metadata=Base.metadata)