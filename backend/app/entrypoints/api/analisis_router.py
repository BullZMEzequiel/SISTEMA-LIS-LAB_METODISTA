from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db.models import (
    OrdenExamenModel,
    PacienteModel,
    ResultadoModuloModel,
    UsuarioModel,
)
from app.adapters.db.session import get_db
from app.domain.calculation_strategies.base import ValidationClinicaError
from app.domain.calculation_strategies.hemograma import HemogramaStrategy
from app.domain.calculation_strategies.hepatograma import HepatogramaStrategy
from app.domain.calculation_strategies.perfil_lipidico import PerfilLipidicoStrategy
from app.domain.calculation_strategies.proteinograma import ProteinogramaStrategy
from app.entrypoints.api.schemas import CalculationRequest, GuardarOrdenRequest

router = APIRouter(prefix="/api/analisis", tags=["Análisis de Laboratorio"])

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


def _resolver_rol(usuario: UsuarioModel | None, rol_usuario: str | None) -> str:
    if usuario and usuario.rol:
        return usuario.rol.nombre.upper()
    if rol_usuario:
        return rol_usuario.upper()
    return "INTERNO"


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


@router.post("/guardar")
def guardar_orden(
    req: GuardarOrdenRequest,
    db: Session = Depends(get_db),
):
    if req.id_paciente is None:
        if req.paciente_nuevo is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe especificar el paciente por id_paciente o paciente_nuevo.",
            )

        existente = (
            db.query(PacienteModel)
            .filter(PacienteModel.ci == req.paciente_nuevo.ci)
            .first()
        )
        if existente:
            paciente = existente
        else:
            paciente = PacienteModel(**req.paciente_nuevo.model_dump())
            db.add(paciente)
            db.commit()
            db.refresh(paciente)
    else:
        paciente = db.query(PacienteModel).filter(PacienteModel.id_paciente == req.id_paciente).first()
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paciente con id_paciente={req.id_paciente} no existe.",
            )

    usuario_creador = None
    if req.id_usuario_creador is not None:
        usuario_creador = (
            db.query(UsuarioModel)
            .filter(UsuarioModel.id_usuario == req.id_usuario_creador)
            .first()
        )

    rol_actual = _resolver_rol(usuario_creador, req.rol_usuario)
    estado_solicitado = req.estado_solicitado.upper()

    if rol_actual == "INTERNO" and estado_solicitado not in {"BORRADOR", "PENDIENTE_APROBACION"}:
        estado_final = "BORRADOR"
    elif rol_actual in {"BIOQUIMICO", "ADMIN"} and estado_solicitado in {"BORRADOR", "OFICIAL"}:
        estado_final = estado_solicitado
    elif rol_actual in {"BIOQUIMICO", "ADMIN"} and estado_solicitado == "PENDIENTE_APROBACION":
        estado_final = "PENDIENTE_APROBACION"
    else:
        estado_final = "BORRADOR"

    if estado_final == "OFICIAL" and rol_actual not in {"BIOQUIMICO", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo usuarios con rol BIOQUIMICO o ADMIN pueden guardar una orden como OFICIAL.",
        )

    modulo = req.codigo_modulo.upper()
    if modulo not in STRATEGIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Módulo '{modulo}' no soportado. Módulos válidos: {list(STRATEGIES.keys())}",
        )

    try:
        entrada_decimal = _normalizar_entrada(req.valores_entrada)
        resultado = STRATEGIES[modulo].calcular(entrada_decimal)
    except ValidationClinicaError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo calcular '{modulo}': {exc}",
        ) from exc

    id_usuario_creador_final = (
        req.id_usuario_creador
        if req.id_usuario_creador is not None
        else (usuario_creador.id_usuario if usuario_creador else 1)
    )

    orden = OrdenExamenModel(
        id_paciente=paciente.id_paciente,
        id_usuario_creador=id_usuario_creador_final,
        medico_solicitante=req.medico_solicitante,
        pieza_cama=req.pieza_cama,
        estado=estado_final,
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)

    calculados_json = {k: v for k, v in resultado.items() if k != "advertencias"}
    advertencias_json = resultado.get("advertencias", [])

    resultado_db = ResultadoModuloModel(
        id_orden=orden.id_orden,
        codigo_modulo=modulo,
        valores_entrada=_serializar_json(req.valores_entrada),
        valores_calculados=_serializar_json(calculados_json),
        advertencias=_serializar_json(advertencias_json),
        id_usuario_validador=(usuario_creador.id_usuario if estado_final == "OFICIAL" and usuario_creador else None),
        fecha_validacion=(datetime.now(timezone.utc) if estado_final == "OFICIAL" else None),
    )
    db.add(resultado_db)
    db.commit()
    db.refresh(resultado_db)

    return {
        "id_orden": orden.id_orden,
        "id_paciente": paciente.id_paciente,
        "codigo_modulo": modulo,
        "estado": orden.estado,
        "calculados": _serializar_json(calculados_json),
        "advertencias": _serializar_json(advertencias_json),
    }
