from decimal import Decimal, InvalidOperation

from app.domain.calculations.base import ValidationClinicaError
from app.domain.calculations.hemograma import HemogramaStrategy
from app.domain.calculations.hepatograma import HepatogramaStrategy
from app.domain.calculations.perfil_lipidico import PerfilLipidicoStrategy
from app.domain.calculations.proteinograma import ProteinogramaStrategy
from app.domain.entities import CalculationOutcome, Value
from app.domain.exceptions import ValidationError


class CalculationEngine:
    def __init__(self) -> None:
        self._strategies = {
            "HEMOGRAMA": HemogramaStrategy(),
            "HEPATOGRAMA": HepatogramaStrategy(),
            "PERFIL_LIPIDICO": PerfilLipidicoStrategy(),
            "PROTEINOGRAMA": ProteinogramaStrategy(),
        }

    def calculate(self, strategy: str, inputs: dict[str, Value]) -> CalculationOutcome:
        strategy_key = strategy.strip().upper()
        if strategy_key.endswith("STRATEGY"):
            strategy_key = strategy_key[: -len("STRATEGY")]
        implementation = self._strategies.get(strategy_key)
        if implementation is None:
            raise ValidationError(f"No existe estrategia de cálculo para '{strategy}'.")
        try:
            decimal_inputs = {
                name: value if isinstance(value, Decimal) else Decimal(str(value))
                for name, value in inputs.items()
                if value is not None and not isinstance(value, bool)
            }
        except (InvalidOperation, ValueError) as exc:
            raise ValidationError("Las entradas de cálculo deben ser valores numéricos válidos.") from exc
        if any(not value.is_finite() for value in decimal_inputs.values()):
            raise ValidationError("Las entradas de cálculo deben ser números finitos.")
        try:
            result = implementation.calcular(decimal_inputs)
        except ValidationClinicaError:
            raise
        except KeyError as exc:
            raise ValidationError(f"Falta un parámetro requerido: {exc.args[0]}.") from exc
        except (InvalidOperation, ZeroDivisionError) as exc:
            raise ValidationError("No se pudo completar el cálculo con los valores ingresados.") from exc
        warnings = result.get("advertencias", [])
        calculated = {key: value for key, value in result.items() if key != "advertencias"}
        if not all(isinstance(value, Decimal) for value in calculated.values()):
            raise ValidationError("La estrategia devolvió un valor calculado no numérico.")
        return CalculationOutcome(calculados=calculated, advertencias=tuple(warnings))