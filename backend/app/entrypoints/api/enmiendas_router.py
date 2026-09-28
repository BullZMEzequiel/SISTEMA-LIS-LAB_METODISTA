from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db.models import (
    AuditoriaEnmiendaModel,
    OrdenExamenModel,
    ResultadoModuloModel,
    UsuarioModel,
)
from app.adapters.db.session import get_db
from app.adapters.security.dependencies import require_roles
from app.entrypoints.api.analisis_router import STRATEGIES, _serializar_json
from app.entrypoints.api.schemas import DelegarOrdenRequest, SolicitudEnmiendaRequest

router = APIRouter(prefix="/enmiendas", tags=["Enmiendas y Delegación"])


def _normalizar_valores_para_calculo(entradas: dict[str, Any]) -> dict[str, Any]:
    normalizados: dict[str, Any] = {}
    for clave, valor in entradas.items():
        if isinstance(valor, (int, float, str)):
            normalizados[clave] = Decimal(str(valor))
        else:
            normalizados[clave] = valor
    return normalizados


@router.post("/solicitar-edicion")
def solicitar_enmienda(
    req: SolicitudEnmiendaRequest,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
):
    resultado_db = (
        db.query(ResultadoModuloModel)
        .filter(ResultadoModuloModel.id_resultado == req.id_resultado)
        .first()
    )
    if not resultado_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resultado no encontrado.",
        )

    modulo = resultado_db.codigo_modulo.upper()
    estrategia = STRATEGIES.get(modulo)
    if not estrategia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Módulo '{modulo}' no tiene estrategia de cálculo soportada.",
        )

    nuevos_valores = _normalizar_valores_para_calculo(req.nuevos_valores_entrada)
    resultado_calculado = estrategia.calcular(nuevos_valores)
    calculados = {k: v for k, v in resultado_calculado.items() if k != "advertencias"}

    auditoria = AuditoriaEnmiendaModel(
        id_orden=resultado_db.id_orden,
        id_resultado=resultado_db.id_resultado,
        id_usuario_solicitante=usuario_actual.id_usuario,
        motivo_justificativo=req.motivo_justificativo,
        valores_anteriores={
            "entradas": resultado_db.valores_entrada,
            "calculados": resultado_db.valores_calculados,
        },
        valores_nuevos={
            "entradas": req.nuevos_valores_entrada,
            "calculados": _serializar_json(calculados),
        },
        estado_enmienda="APROBADA",
    )
    db.add(auditoria)

    resultado_db.valores_entrada = _serializar_json(req.nuevos_valores_entrada)
    resultado_db.valores_calculados = _serializar_json(calculados)
    if resultado_db.orden is not None:
        resultado_db.orden.estado = "ENMENDADO"

    db.commit()
    db.refresh(auditoria)

    return {
        "message": "Enmienda procesada correctamente y registrada en auditoría.",
        "id_enmienda": auditoria.id_enmienda,
        "estado": auditoria.estado_enmienda,
    }


@router.post("/delegar-orden")
def delegar_orden(
    req: DelegarOrdenRequest,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
):
    orden = db.query(OrdenExamenModel).filter(OrdenExamenModel.id_orden == req.id_orden).first()
    if not orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden no encontrada.",
        )

    usuario_destino = (
        db.query(UsuarioModel)
        .filter(UsuarioModel.id_usuario == req.id_usuario_destino)
        .first()
    )
    if not usuario_destino or not usuario_destino.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario de destino no es válido o está inactivo.",
        )

    orden.id_usuario_creador = usuario_destino.id_usuario
    db.commit()

    return {
        "message": f"Orden #{orden.id_orden} reasignada exitosamente a {usuario_destino.nombre_completo}.",
        "orden": {
            "id_orden": orden.id_orden,
            "id_usuario_creador": orden.id_usuario_creador,
            "estado": orden.estado,
        },
        "usuario_actual": usuario_actual.nombre_completo,
    }
