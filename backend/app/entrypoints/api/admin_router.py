from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.adapters.db.models import AuditoriaEnmiendaModel, RolModel, UsuarioModel
from app.adapters.db.session import get_db
from app.adapters.security.auth import pwd_context
from app.adapters.security.dependencies import require_roles
from app.entrypoints.api.schemas import (
    AdminUsuarioCreate,
    AdminUsuarioResetPassword,
    AdminUsuarioResponse,
    AdminUsuarioUpdate,
    AuditoriaAdminResponse,
)

router = APIRouter(prefix="/admin", tags=["Administración"])


def _serializar_usuario(usuario: UsuarioModel) -> AdminUsuarioResponse:
    return AdminUsuarioResponse(
        id_usuario=usuario.id_usuario,
        ci=usuario.ci,
        nombre_completo=usuario.nombre_completo,
        correo=usuario.correo,
        id_rol=usuario.id_rol,
        rol=usuario.rol.nombre if usuario.rol else None,
        activo=bool(usuario.activo),
    )


@router.get("/usuarios", response_model=list[AdminUsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    del usuario_actual
    usuarios = db.query(UsuarioModel).all()
    return [_serializar_usuario(usuario) for usuario in usuarios]


@router.post("/usuarios", response_model=AdminUsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: AdminUsuarioCreate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    del usuario_actual
    if not payload.ci or not payload.nombre_completo or not payload.correo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CI, nombre, correo y contraseña son obligatorios.",
        )

    if not payload.password or len(payload.password.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 4 caracteres.",
        )

    rol = db.query(RolModel).filter(RolModel.id_rol == payload.id_rol).first()
    if not rol:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol indicado no existe.",
        )

    if db.query(UsuarioModel).filter((UsuarioModel.ci == payload.ci) | (UsuarioModel.correo == payload.correo)).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese C.I. o correo.",
        )

    nuevo_usuario = UsuarioModel(
        ci=payload.ci.strip(),
        nombre_completo=payload.nombre_completo.strip(),
        correo=payload.correo.strip(),
        id_rol=payload.id_rol,
        hash_password=pwd_context.hash(payload.password),
        activo=payload.activo,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return _serializar_usuario(nuevo_usuario)


@router.put("/usuarios/{id_usuario}", response_model=AdminUsuarioResponse)
def actualizar_usuario(
    id_usuario: int,
    payload: AdminUsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    del usuario_actual
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    if payload.ci is not None:
        usuario.ci = payload.ci.strip()
    if payload.nombre_completo is not None:
        usuario.nombre_completo = payload.nombre_completo.strip()
    if payload.correo is not None:
        usuario.correo = payload.correo.strip()
    if payload.id_rol is not None:
        rol = db.query(RolModel).filter(RolModel.id_rol == payload.id_rol).first()
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol indicado no existe.",
            )
        usuario.id_rol = payload.id_rol
    if payload.activo is not None:
        usuario.activo = payload.activo

    existente = (
        db.query(UsuarioModel)
        .filter(
            (UsuarioModel.id_usuario != id_usuario)
            & ((UsuarioModel.ci == usuario.ci) | (UsuarioModel.correo == usuario.correo))
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro usuario con ese C.I. o correo.",
        )

    db.commit()
    db.refresh(usuario)
    return _serializar_usuario(usuario)


@router.put("/usuarios/{id_usuario}/reset-password")
def restablecer_password(
    id_usuario: int,
    payload: AdminUsuarioResetPassword,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    del usuario_actual
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    if not payload.nueva_password or len(payload.nueva_password.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 4 caracteres.",
        )

    usuario.hash_password = pwd_context.hash(payload.nueva_password)
    db.commit()
    return {"message": "Contraseña actualizada correctamente."}


@router.get("/auditoria", response_model=list[AuditoriaAdminResponse])
def obtener_auditoria(
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    del usuario_actual
    auditorias = db.query(AuditoriaEnmiendaModel).order_by(AuditoriaEnmiendaModel.fecha_solicitud.desc()).all()
    respuesta: list[AuditoriaAdminResponse] = []

    for item in auditorias:
        respuesta.append(
            AuditoriaAdminResponse(
                id_enmienda=item.id_enmienda,
                id_orden=item.id_orden,
                id_resultado=item.id_resultado,
                modulo=item.resultado.codigo_modulo if item.resultado else None,
                usuario_solicitante=item.solicitante.nombre_completo if item.solicitante else None,
                rol_usuario=item.solicitante.rol.nombre if item.solicitante and item.solicitante.rol else None,
                fecha=item.fecha_solicitud.isoformat() if item.fecha_solicitud else None,
                motivo=item.motivo_justificativo,
                estado=item.estado_enmienda,
            )
        )

    return respuesta
