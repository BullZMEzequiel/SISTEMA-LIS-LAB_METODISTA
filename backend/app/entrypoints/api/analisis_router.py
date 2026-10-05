from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.adapters.security.dependencies import require_roles
from app.domain.calculations.base import ValidationClinicaError
from app.domain.calculations.hemograma import HemogramaStrategy
from app.domain.calculations.hepatograma import HepatogramaStrategy
from app.domain.calculations.perfil_lipidico import PerfilLipidicoStrategy
from app.domain.calculations.proteinograma import ProteinogramaStrategy
from app.entrypoints.api.schemas import CalculationRequest

router = APIRouter(
    prefix="/api/analisis",
    tags=["Análisis de Laboratorio"],
    dependencies=[Depends(require_roles(["BIOQUIMICO"]))],
)

STRATEGIES = {
    "HEMOGRAMA": HemogramaStrategy(),
    "PERFIL_LIPIDICO": PerfilLipidicoStrategy(),
    "HEPATOGRAMA": HepatogramaStrategy(),
    "PROTEINOGRAMA": ProteinogramaStrategy(),
}


def _normalizar_entrada(dato: Any) -> Any:
    if isinstance(dato, dict):
        return {k: _normalizar_entrada(v) for k, v in dato.items()}
    if isinstance(dato, list):
        return [_normalizar_entrada(v) for v in dato]
    if isinstance(dato, Decimal):
        return dato
    if isinstance(dato, (int, float, str)):
        try:
            return Decimal(str(dato))
        except (InvalidOperation, ValueError):
            return dato
    return dato


def _serializar_json(valor: Any) -> Any:
    if isinstance(valor, dict):
        return {str(k): _serializar_json(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_serializar_json(v) for v in valor]
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


@router.post("/calcular")
def calcular_modulo(req: CalculationRequest):
    modulo = req.codigo_modulo.upper()
    estrategia = STRATEGIES.get(modulo)

    if not estrategia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Módulo '{modulo}' no soportado. "
                f"Módulos válidos: {list(STRATEGIES.keys())}"
            ),
        )

    try:
        entrada_decimal = _normalizar_entrada(req.entradas)
        resultado = estrategia.calcular(entrada_decimal)
        calculados = {k: v for k, v in resultado.items() if k != "advertencias"}
        advertencias = resultado.get("advertencias", [])

        return {
            "modulo": modulo,
            "calculados": _serializar_json(calculados),
            "advertencias": _serializar_json(advertencias),
        }
    except ValidationClinicaError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # pragma: no cover - manejo defensivo
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo calcular el módulo '{modulo}': {exc}",
        ) from exc


@router.post("/calcular/{codigo_modulo}")
def calcular_modulo_por_ruta(
    codigo_modulo: str,
    entradas: dict[str, Any] = Body(..., description="Valores de entrada del módulo"),
):
    req = CalculationRequest(codigo_modulo=codigo_modulo, entradas=entradas)
    return calcular_modulo(req)


@router.post("/guardar", deprecated=True)
def guardar_orden():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="El guardado se habilitará con el flujo de órdenes y resultados versionados.",
    )
