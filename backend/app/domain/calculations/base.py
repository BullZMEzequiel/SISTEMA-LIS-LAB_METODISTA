"""
Contrato base para el motor de cálculo clínico.

Regla de oro del dominio: TODO cálculo usa decimal.Decimal, nunca float.
El error de redondeo de punto flotante binario (ej. 0.1 + 0.2 != 0.3) es
inaceptable cuando el resultado puede afectar una decisión clínica.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Protocol, TypeAlias

CalculationValue: TypeAlias = Decimal | list[str]


class ValidationClinicaError(Exception):
    """Error bloqueante: el resultado no puede avanzar de estado (BORRADOR ->
    PENDIENTE_APROBACION) mientras esta excepción no se resuelva."""


class CalculationStrategy(Protocol):
    """Puerto que implementa cada panel de examen (Strategy pattern)."""

    def calcular(self, entrada: dict[str, Decimal]) -> Mapping[str, CalculationValue]:
        """Recibe los valores de entrada manual y devuelve los valores
        calculados. No debe mutar `entrada`."""
        ...


def redondear(valor: Decimal, decimales: int = 2) -> Decimal:
    """Redondeo clínico estándar: HALF_UP (redondeo 'de farmacia'), no el
    HALF_EVEN que usa Python por defecto en operaciones bancarias."""
    cuantizador = Decimal("1." + "0" * decimales) if decimales > 0 else Decimal("1")
    return valor.quantize(cuantizador, rounding=ROUND_HALF_UP)