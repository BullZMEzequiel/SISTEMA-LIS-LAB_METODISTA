from decimal import Decimal

import pytest

from app.domain.calculations.hepatograma import HepatogramaStrategy


@pytest.fixture
def strategy() -> HepatogramaStrategy:
    return HepatogramaStrategy()


def test_bilirrubina_indirecta(strategy: HepatogramaStrategy) -> None:
    entrada = {
        "bilirrubina_total": Decimal("1.0"),
        "bilirrubina_directa": Decimal("0.25"),
    }
    resultado = strategy.calcular(entrada)

    assert resultado["bilirrubina_indirecta"] == Decimal("0.75")