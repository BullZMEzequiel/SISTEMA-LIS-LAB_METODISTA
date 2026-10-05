"""
Strategy: Perfil Lipídico (fórmula de Friedewald).
Fuente: hoja 'HC-QMC-SEROL-EGO.', celdas K39-K43.

VLDL = Trigliceridos / 5
LDL  = Colesterol - HDL - VLDL

Nota clínica: la fórmula de Friedewald pierde precisión con Triglicéridos
> 400 mg/dl. No se valida aquí (decisión de negocio pendiente: ¿bloquear o
solo advertir?) — dejar como TODO hasta confirmar con la doctora.
"""
from __future__ import annotations

from decimal import Decimal

from .base import CalculationStrategy, redondear


class PerfilLipidicoStrategy:
    def calcular(self, entrada: dict[str, Decimal]) -> dict[str, Decimal]:
        colesterol = entrada["colesterol"]
        trigliceridos = entrada["trigliceridos"]
        hdl = entrada["hdl"]

        vldl = redondear(trigliceridos / Decimal("5"), 2)
        ldl = redondear(colesterol - hdl - vldl, 2)

        return {"vldl": vldl, "ldl": ldl}