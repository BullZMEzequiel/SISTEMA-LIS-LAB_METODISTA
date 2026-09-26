"""
Strategy: Hemograma Completo.
Fuente: hojas 'HC-QMC-SEROL-EGO.' y 'HC-QMC-SERO-PROT' del Excel original.

Constantes fijas validadas con el laboratorio (NO modificar sin autorización
clínica expresa — ver docs/arquitectura.md sección 4):
    - 107000  -> factor de estimación de Globulos Rojos a partir del Hematocrito
    - 0.32    -> factor de estimación de Hemoglobina a partir del Hematocrito

Diferencial leucocitario (Segmentados, Linfocitos, Eosinofilos, Monocitos,
Cayados):
    SUPUESTO A CONFIRMAR CON LA DOCTORA: el Excel origen sugiere (dato
    D26=0.57 en la hoja) que el porcentaje se ingresa como FRACCIÓN DECIMAL
    (0.62 = 62%), ya que la fórmula real es 'C17 * C11' sin dividir entre
    100. Si en la práctica el operador escribe "62" en vez de "0.62", esta
    Strategy y la validación de tolerancia deben ajustarse.

Regla de validación (bajo el supuesto de fracción 0-1):
    La suma de las 5 fracciones debe caer en el rango 0.999 - 1.001
    (equivalente a 99.9% - 100.1%). Fuera de ese rango: ERROR BLOQUEANTE,
    no se permite pasar de BORRADOR a PENDIENTE_APROBACION.
"""
from __future__ import annotations

from decimal import Decimal

from .base import CalculationStrategy, ValidationClinicaError, redondear

FACTOR_GLOBULOS_ROJOS = Decimal("107000")
FACTOR_HEMOGLOBINA = Decimal("0.32")

TOLERANCIA_MIN = Decimal("0.999")
TOLERANCIA_MAX = Decimal("1.001")

CAMPOS_DIFERENCIAL = ("segmentados", "linfocitos", "eosinofilos", "monocitos", "cayados")


class HemogramaStrategy:
    """Implementa CalculationStrategy para el panel de Hemograma Completo."""

    def calcular(self, entrada: dict[str, Decimal]) -> dict[str, Decimal | list[str]]:
        hematocrito = entrada["hematocrito"]
        total_globulos_blancos = entrada["globulos_blancos"]

        advertencias = self._validar_diferencial(entrada)

        resultado: dict[str, Decimal | list[str]] = {
            "globulos_rojos_estimado": redondear(FACTOR_GLOBULOS_ROJOS * hematocrito, 0),
            "hemoglobina_estimada": redondear(FACTOR_HEMOGLOBINA * hematocrito, 2),
            "advertencias": advertencias,
        }

        for campo in CAMPOS_DIFERENCIAL:
            fraccion = entrada[campo]
            resultado[f"{campo}_absoluto"] = redondear(fraccion * total_globulos_blancos, 0)

        return resultado

    def _validar_diferencial(self, entrada: dict[str, Decimal]) -> list[str]:
        suma = sum((entrada[campo] for campo in CAMPOS_DIFERENCIAL), Decimal("0"))

        if not (TOLERANCIA_MIN <= suma <= TOLERANCIA_MAX):
            # Fuera de tolerancia: BLOQUEA el guardado, no pasa de BORRADOR.
            raise ValidationClinicaError(
                f"Diferencial leucocitario fuera de tolerancia: suma={suma} "
                f"(rango válido: {TOLERANCIA_MIN}-{TOLERANCIA_MAX})"
            )

        if suma != Decimal("1.000"):
            # Dentro de tolerancia pero no exacto: ADVERTENCIA leve, no bloquea.
            return [f"El diferencial leucocitario suma {suma} (no exactamente 1.000, "
                    f"dentro del margen de redondeo aceptado)."]

        return []