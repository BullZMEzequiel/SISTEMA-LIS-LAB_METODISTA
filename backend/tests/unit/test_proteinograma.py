from decimal import Decimal

import pytest

from app.domain.calculations.base import ValidationClinicaError
from app.domain.calculations.proteinograma import ProteinogramaStrategy


@pytest.fixture
def strategy() -> ProteinogramaStrategy:
    return ProteinogramaStrategy()


def test_globulina_y_relacion_ag(strategy: ProteinogramaStrategy) -> None:
    entrada = {
        "proteinas_totales": Decimal("7.2"),
        "albumina": Decimal("4.5"),
    }
    resultado = strategy.calcular(entrada)

    assert resultado["globulina"] == Decimal("2.70")
    assert resultado["relacion_ag"] == Decimal("1.67")  # 4.5 / 2.70


def test_globulina_cero_bloquea_division(strategy: ProteinogramaStrategy) -> None:
    entrada = {
        "proteinas_totales": Decimal("5.0"),
        "albumina": Decimal("5.0"),
    }
    with pytest.raises(ValidationClinicaError, match="división por cero"):
        strategy.calcular(entrada)