"""
Strategy: Proteinograma.
Fuente: hoja 'HC-QMC-SERO-PROT', celdas G42-G48.

Globulina    = Prot.Totales - Albumina      (G46 = G42 - G44)
Relacion A/G = Albumina / Globulina          (G48 = G44 / G46)

Caso especial detectado en el Excel original: si Globulina = 0, la celda
G48 queda en '#DIV/0!'. Aquí lo tratamos como ERROR BLOQUEANTE explícito
en vez de dejar propagar un error silencioso.
"""
from __future__ import annotations

from decimal import Decimal

from .base import CalculationStrategy, ValidationClinicaError, redondear


class ProteinogramaStrategy:
    def calcular(self, entrada: dict[str, Decimal]) -> dict[str, Decimal]:
        proteinas_totales = entrada["proteinas_totales"]
        albumina = entrada["albumina"]

        globulina = redondear(proteinas_totales - albumina, 2)

        if globulina == 0:
            raise ValidationClinicaError(
                "Globulina calculada en 0 — no se puede calcular la Relación A/G "
                "(división por cero). Verificar Proteínas Totales y Albúmina ingresadas."
            )

        relacion_ag = redondear(albumina / globulina, 2)

        return {"globulina": globulina, "relacion_ag": relacion_ag}