from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .catalog import EstudioVersionModel, ParametroModel
    from .identity import UsuarioModel
    from .orders import OrdenEstudioModel


class ResultadoVersionModel(Base):
    __tablename__ = "resultado_versiones"
    __table_args__ = (
        CheckConstraint("estado IN ('BORRADOR', 'OFICIAL', 'SUPERADA', 'ANULADA')"),
        CheckConstraint("numero_version = 1 OR motivo_correccion IS NOT NULL"),
        UniqueConstraint("id_orden_estudio", "numero_version"),
        Index("idx_resultado_versiones_orden_estudio", "id_orden_estudio"),
        Index("idx_resultado_versiones_estado", "estado"),
        Index("idx_resultado_versiones_creado_por", "creado_por"),
        {"schema": SCHEMA},
    )

    id_resultado_version: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_orden_estudio: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.orden_estudios.id_orden_estudio", ondelete="RESTRICT"), nullable=False)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    id_estudio_version: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.estudio_versiones.id_estudio_version", ondelete="RESTRICT"), nullable=False)
    creado_por: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario", ondelete="RESTRICT"), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'BORRADOR'"))
    motivo_correccion: Mapped[str | None] = mapped_column(Text)
    comentario_estudio: Mapped[str | None] = mapped_column(Text)
    snapshot_completo: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    oficializado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    orden_estudio: Mapped[OrdenEstudioModel] = relationship(back_populates="versiones_resultado")
    estudio_version: Mapped[EstudioVersionModel] = relationship()
    creador: Mapped[UsuarioModel] = relationship(back_populates="versiones_creadas")
    valores: Mapped[list[ResultadoValorModel]] = relationship(back_populates="resultado_version")


class ResultadoValorModel(Base):
    __tablename__ = "resultado_valores"
    __table_args__ = (
        UniqueConstraint("id_resultado_version", "id_parametro"),
        Index("idx_resultado_valores_version", "id_resultado_version"),
        Index("idx_resultado_valores_parametro", "id_parametro"),
        {"schema": SCHEMA},
    )

    id_resultado_valor: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_resultado_version: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.resultado_versiones.id_resultado_version", ondelete="RESTRICT"), nullable=False)
    id_parametro: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.parametros.id_parametro", ondelete="RESTRICT"), nullable=False)
    valor_numerico: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    valor_texto: Mapped[str | None] = mapped_column(Text)
    valor_booleano: Mapped[bool | None] = mapped_column(Boolean)
    unidad_utilizada: Mapped[str | None] = mapped_column(String(50))
    referencia_utilizada: Mapped[str | None] = mapped_column(Text)
    fuera_de_rango: Mapped[bool | None] = mapped_column(Boolean)
    valor_calculado: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    orden_visualizacion: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    resultado_version: Mapped[ResultadoVersionModel] = relationship(back_populates="valores")
    parametro: Mapped[ParametroModel] = relationship(back_populates="valores")