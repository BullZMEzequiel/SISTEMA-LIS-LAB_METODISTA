"""
Strategy: Hepatograma (Bilirrubinas).
Fuente: hojas 'HC-QMC-SEROL-EGO.' (B39-B41) y 'HC-QMC-SERO-PROT' (B42-B46).

B.Indirecta = B.Total - B.Directa
"""
from __future__ import annotations

from decimal import Decimal

from .base import CalculationStrategy, redondear


class HepatogramaStrategy:
    def calcular(self, entrada: dict[str, Decimal]) -> dict[str, Decimal]:
        bilirrubina_total = entrada["bilirrubina_total"]
        bilirrubina_directa = entrada["bilirrubina_directa"]

        bilirrubina_indirecta = redondear(bilirrubina_total - bilirrubina_directa, 2)

        return {"bilirrubina_indirecta": bilirrubina_indirecta}