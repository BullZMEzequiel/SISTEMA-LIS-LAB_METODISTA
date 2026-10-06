"""
backend/app/entrypoints/api/pacientes_router.py
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.adapters.persistence.models import AuditoriaModel, UsuarioModel
from app.adapters.persistence.repositories.paciente import PacienteRepository
from app.adapters.persistence.session import get_db
from app.adapters.security.dependencies import require_roles
from app.entrypoints.api.schemas import PacienteCreate, PacienteResponse, PacienteUpdate

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


def _registrar_auditoria(
    db: Session, usuario_id: int, accion: str, entidad_id: int,
    datos_anteriores: dict | None, datos_nuevos: dict | None,
) -> None:
    db.add(AuditoriaModel(
        id_usuario=usuario_id,
        accion=accion,
        entidad="PACIENTE",
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
        descripcion=f"{accion} sobre paciente id={entidad_id}",
    ))
    db.commit()


@router.get("", response_model=list[PacienteResponse])
def buscar_pacientes(
    q: str = Query(..., min_length=2, description="CI o nombre/apellido parcial"),
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
):
    repo = PacienteRepository(db)
    return repo.buscar(q.strip())


@router.get("/{id_paciente}", response_model=PacienteResponse)
def obtener_paciente(
    id_paciente: int,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
):
    repo = PacienteRepository(db)
    paciente = repo.get_by_id(id_paciente)
    if not paciente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado.")
    return paciente


@router.post("", response_model=PacienteResponse, status_code=status.HTTP_201_CREATED)
def crear_paciente(
    payload: PacienteCreate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
):
    repo = PacienteRepository(db)

    if repo.get_by_ci(payload.ci.strip()):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un paciente registrado con ese C.I.",
        )

    paciente = repo.crear(
        ci=payload.ci.strip(),
        nombres=payload.nombres.strip(),
        apellido_paterno=payload.apellido_paterno.strip(),
        apellido_materno=payload.apellido_materno.strip() if payload.apellido_materno else None,
        fecha_nacimiento=payload.fecha_nacimiento,
        sexo=payload.sexo,
        telefono=payload.telefono,
        correo=payload.correo,
        creado_por=usuario_actual.id_usuario,
    )

    _registrar_auditoria(
        db, usuario_actual.id_usuario, "CREAR_PACIENTE", paciente.id_paciente,
        None, {"ci": paciente.ci, "nombres": paciente.nombres},
    )
    return paciente


@router.put("/{id_paciente}", response_model=PacienteResponse)
def actualizar_paciente(
    id_paciente: int,
    payload: PacienteUpdate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN", "BIOQUIMICO"])),
):
    repo = PacienteRepository(db)
    paciente = repo.get_by_id(id_paciente)
    if not paciente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paciente no encontrado.")

    datos_anteriores = {
        "nombres": paciente.nombres, "telefono": paciente.telefono, "correo": paciente.correo,
    }
    cambios = payload.model_dump(exclude_unset=True)
    paciente = repo.actualizar(paciente, cambios)

    _registrar_auditoria(
        db, usuario_actual.id_usuario, "EDITAR_PACIENTE", paciente.id_paciente,
        datos_anteriores, cambios,
    )
    return paciente