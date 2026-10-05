"""
Pruebas del motor de cálculo de Hemograma.
Correr con: pytest tests/unit/test_hemograma.py -v
"""
from decimal import Decimal

import pytest

from app.domain.calculations.base import ValidationClinicaError
from app.domain.calculations.hemograma import HemogramaStrategy


@pytest.fixture
def strategy() -> HemogramaStrategy:
    return HemogramaStrategy()


def test_globulos_rojos_y_hemoglobina_estimados(strategy: HemogramaStrategy) -> None:
    entrada = {
        "hematocrito": Decimal("48"),
        "globulos_blancos": Decimal("7500"),
        "segmentados": Decimal("0.62"),
        "linfocitos": Decimal("0.30"),
        "eosinofilos": Decimal("0.03"),
        "monocitos": Decimal("0.04"),
        "cayados": Decimal("0.01"),
    }
    resultado = strategy.calcular(entrada)

    assert resultado["globulos_rojos_estimado"] == Decimal("5136000")  # 107000 * 48
    assert resultado["hemoglobina_estimada"] == Decimal("15.36")  # 0.32 * 48


def test_diferencial_absoluto_correcto(strategy: HemogramaStrategy) -> None:
    entrada = {
        "hematocrito": Decimal("48"),
        "globulos_blancos": Decimal("7500"),
        "segmentados": Decimal("0.62"),
        "linfocitos": Decimal("0.30"),
        "eosinofilos": Decimal("0.03"),
        "monocitos": Decimal("0.04"),
        "cayados": Decimal("0.01"),
    }
    resultado = strategy.calcular(entrada)

    assert resultado["segmentados_absoluto"] == Decimal("4650")  # 0.62 * 7500
    assert resultado["linfocitos_absoluto"] == Decimal("2250")  # 0.30 * 7500
    assert resultado["cayados_absoluto"] == Decimal("75")  # 0.01 * 7500


def test_diferencial_dentro_de_tolerancia_no_falla(strategy: HemogramaStrategy) -> None:
    # Suma = 0.999 (99.9%) -> límite inferior aceptado
    entrada = {
        "hematocrito": Decimal("48"),
        "globulos_blancos": Decimal("7500"),
        "segmentados": Decimal("0.619"),
        "linfocitos": Decimal("0.30"),
        "eosinofilos": Decimal("0.03"),
        "monocitos": Decimal("0.04"),
        "cayados": Decimal("0.01"),
    }
    resultado = strategy.calcular(entrada)  # no debe lanzar excepción
    assert len(resultado["advertencias"]) == 1  # 0.999 != 1.000 -> advertencia leve


def test_diferencial_exacto_100_sin_advertencia(strategy: HemogramaStrategy) -> None:
    entrada = {
        "hematocrito": Decimal("48"),
        "globulos_blancos": Decimal("7500"),
        "segmentados": Decimal("0.62"),
        "linfocitos": Decimal("0.30"),
        "eosinofilos": Decimal("0.03"),
        "monocitos": Decimal("0.04"),
        "cayados": Decimal("0.01"),
    }
    resultado = strategy.calcular(entrada)
    assert resultado["advertencias"] == []


def test_diferencial_fuera_de_tolerancia_bloquea(strategy: HemogramaStrategy) -> None:
    # Suma = 0.985 (98.5%) -> fuera del rango 99.9%-100.1%
    entrada = {
        "hematocrito": Decimal("48"),
        "globulos_blancos": Decimal("7500"),
        "segmentados": Decimal("0.60"),
        "linfocitos": Decimal("0.30"),
        "eosinofilos": Decimal("0.03"),
        "monocitos": Decimal("0.04"),
        "cayados": Decimal("0.015"),
    }
    with pytest.raises(ValidationClinicaError, match="fuera de tolerancia"):
        strategy.calcular(entrada)