"""
Pruebas del Perfil Lipídico.
El primer caso es una PRUEBA DE REGRESIÓN REAL: usa los valores exactos
encontrados en la hoja 'HC-QMC-SEROL-EGO.' del Excel original (celdas
K39=Colesterol, K40=Trigliceridos, K41=HDL, K42=LDL esperado, K43=VLDL
esperado) para garantizar que el sistema reproduce el mismo resultado
que el Excel que la doctora usa hoy.
"""
from decimal import Decimal

import pytest

from app.domain.calculation_strategies.perfil_lipidico import PerfilLipidicoStrategy


@pytest.fixture
def strategy() -> PerfilLipidicoStrategy:
    return PerfilLipidicoStrategy()


def test_caso_real_excel_hc_qmc_serol_ego(strategy: PerfilLipidicoStrategy) -> None:
    """Regresión contra K39/K40/K41/K42/K43 de la hoja original."""
    entrada = {
        "colesterol": Decimal("164.5"),
        "trigliceridos": Decimal("102.4"),
        "hdl": Decimal("0"),  # HDL vacío en el caso de ejemplo del Excel
    }
    resultado = strategy.calcular(entrada)

    assert resultado["vldl"] == Decimal("20.48")   # igual a K43 en el Excel
    assert resultado["ldl"] == Decimal("144.02")   # igual a K42 en el Excel


def test_caso_con_hdl_informado(strategy: PerfilLipidicoStrategy) -> None:
    entrada = {
        "colesterol": Decimal("200"),
        "trigliceridos": Decimal("150"),
        "hdl": Decimal("50"),
    }
    resultado = strategy.calcular(entrada)

    assert resultado["vldl"] == Decimal("30.00")
    assert resultado["ldl"] == Decimal("120.00")  # 200 - 50 - 30