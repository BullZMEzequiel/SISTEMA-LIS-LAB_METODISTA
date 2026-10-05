from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CHAR, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA

if TYPE_CHECKING:
    from .identity import UsuarioModel
    from .orders import OrdenEstudioModel
    from .results import ResultadoValorModel


class PanelModel(Base):
    __tablename__ = "paneles"
    __table_args__ = {"schema": SCHEMA}

    id_panel: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    estudios_asignados: Mapped[list[PanelEstudioModel]] = relationship(back_populates="panel")


class EstudioModel(Base):
    __tablename__ = "estudios"
    __table_args__ = (
        Index("idx_estudios_activo", "activo"),
        {"schema": SCHEMA},
    )

    id_estudio: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text)
    modulo_frontend: Mapped[str | None] = mapped_column(String(100))
    estrategia_calculo: Mapped[str | None] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    paneles_asignados: Mapped[list[PanelEstudioModel]] = relationship(back_populates="estudio")
    versiones: Mapped[list[EstudioVersionModel]] = relationship(back_populates="estudio")
    ordenes: Mapped[list[OrdenEstudioModel]] = relationship(back_populates="estudio")


class PanelEstudioModel(Base):
    __tablename__ = "panel_estudios"
    __table_args__ = (
        Index("idx_panel_estudios_estudio", "id_estudio"),
        {"schema": SCHEMA},
    )

    id_panel: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.paneles.id_panel", ondelete="CASCADE"), primary_key=True)
    id_estudio: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.estudios.id_estudio", ondelete="RESTRICT"), primary_key=True)
    orden_visualizacion: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))

    panel: Mapped[PanelModel] = relationship(back_populates="estudios_asignados")
    estudio: Mapped[EstudioModel] = relationship(back_populates="paneles_asignados")


class EstudioVersionModel(Base):
    __tablename__ = "estudio_versiones"
    __table_args__ = (
        UniqueConstraint("id_estudio", "numero_version"),
        Index("idx_estudio_versiones_estudio", "id_estudio"),
        Index("idx_estudio_versiones_activa", "activa"),
        {"schema": SCHEMA},
    )

    id_estudio_version: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_estudio: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.estudios.id_estudio", ondelete="RESTRICT"), nullable=False)
    numero_version: Mapped[int] = mapped_column(Integer, nullable=False)
    descripcion_cambios: Mapped[str | None] = mapped_column(Text)
    configuracion: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    creado_por: Mapped[int | None] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.usuarios.id_usuario"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    estudio: Mapped[EstudioModel] = relationship(back_populates="versiones")
    creador: Mapped[UsuarioModel | None] = relationship()
    parametros: Mapped[list[ParametroModel]] = relationship(back_populates="estudio_version")
    ordenes_estudio: Mapped[list[OrdenEstudioModel]] = relationship(back_populates="estudio_version")


class ParametroModel(Base):
    __tablename__ = "parametros"
    __table_args__ = (
        CheckConstraint("tipo_campo IN ('ENTRADA_MANUAL', 'CALCULADO_AUTOMATICO', 'TEXTO', 'BOOLEANO', 'SELECCION')"),
        CheckConstraint("tipo_dato IN ('DECIMAL', 'ENTERO', 'TEXTO', 'BOOLEANO', 'FECHA')"),
        UniqueConstraint("id_estudio_version", "codigo"),
        Index("idx_parametros_estudio_version", "id_estudio_version"),
        {"schema": SCHEMA},
    )

    id_parametro: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_estudio_version: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.estudio_versiones.id_estudio_version", ondelete="RESTRICT"), nullable=False)
    codigo: Mapped[str] = mapped_column(String(80), nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_campo: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo_dato: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'DECIMAL'"))
    unidad_medida: Mapped[str | None] = mapped_column(String(50))
    formula_codigo: Mapped[str | None] = mapped_column(Text)
    orden_visualizacion: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))
    obligatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("FALSE"))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    estudio_version: Mapped[EstudioVersionModel] = relationship(back_populates="parametros")
    rangos_referencia: Mapped[list[RangoReferenciaModel]] = relationship(back_populates="parametro")
    valores: Mapped[list[ResultadoValorModel]] = relationship(back_populates="parametro")


class RangoReferenciaModel(Base):
    __tablename__ = "rangos_referencia"
    __table_args__ = (
        CheckConstraint("sexo IN ('M', 'F') OR sexo IS NULL"),
        CheckConstraint("edad_minima IS NULL OR edad_maxima IS NULL OR edad_minima <= edad_maxima"),
        CheckConstraint("limite_inferior IS NULL OR limite_superior IS NULL OR limite_inferior <= limite_superior"),
        Index("idx_rangos_referencia_parametro", "id_parametro"),
        Index("idx_rangos_referencia_sexo", "sexo"),
        {"schema": SCHEMA},
    )

    id_rango_referencia: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_parametro: Mapped[int] = mapped_column(BigInteger, ForeignKey(f"{SCHEMA}.parametros.id_parametro", ondelete="RESTRICT"), nullable=False)
    sexo: Mapped[str | None] = mapped_column(CHAR(1))
    edad_minima: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    edad_maxima: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    unidad: Mapped[str | None] = mapped_column(String(50))
    limite_inferior: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    limite_superior: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    referencia_texto: Mapped[str | None] = mapped_column(Text)
    observaciones: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    parametro: Mapped[ParametroModel] = relationship(back_populates="rangos_referencia")