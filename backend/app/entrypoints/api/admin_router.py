from ipaddress import ip_address

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.adapters.persistence.models import AuditoriaSeguridadModel, UsuarioModel
from app.adapters.persistence.repositories import AuditoriaRepository, UsuarioRepository
from app.adapters.persistence.session import get_db
from app.adapters.security.auth import pwd_context
from app.adapters.security.dependencies import SUPPORTED_ROLES, require_roles
from app.entrypoints.api.contracts import SecurityAuditEventResponse
from app.entrypoints.api.schemas import (
    AdminUsuarioCreate,
    AdminUsuarioResetPassword,
    AdminUsuarioResponse,
    AdminUsuarioUpdate,
    AuditoriaAdminResponse,
)

router = APIRouter(prefix="/admin", tags=["Administración"])


def _ip_cliente(request: Request) -> str | None:
    host = request.client.host if request.client else None
    try:
        return str(ip_address(host)) if host else None
    except ValueError:
        return None


def _registrar_evento_seguridad(
    db: Session,
    request: Request,
    id_actor: int,
    evento: str,
    detalles: dict[str, object],
) -> None:
    AuditoriaRepository(db).add_security_event(
        AuditoriaSeguridadModel(
            id_usuario=id_actor,
            evento=evento,
            ip_origen=_ip_cliente(request),
            user_agent=request.headers.get("user-agent"),
            detalles=detalles,
        )
    )


def _serializar_usuario(usuario: UsuarioModel) -> AdminUsuarioResponse:
    nombre_completo = " ".join(
        parte for parte in (usuario.nombres, usuario.apellido_paterno, usuario.apellido_materno) if parte
    )
    return AdminUsuarioResponse(
        id_usuario=usuario.id_usuario,
        ci=usuario.ci,
        nombre_completo=nombre_completo,
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
    usuarios = UsuarioRepository(db).list()
    return [_serializar_usuario(usuario) for usuario in usuarios]


@router.post("/usuarios", response_model=AdminUsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    payload: AdminUsuarioCreate,
    request: Request,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    if not payload.ci or not payload.nombre_completo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail="CI y nombre completo son obligatorios.")
        

    if not payload.password or len(payload.password.strip()) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña debe tener al menos 4 caracteres.",
        )

    repository = UsuarioRepository(db)
    rol = repository.get_role(payload.id_rol)
    if not rol or rol.nombre.upper() not in SUPPORTED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol indicado no existe o no está permitido.",
        )

    correo_normalizado = payload.correo.strip() if payload.correo else None
    if repository.get_by_ci(payload.ci.strip()) or (correo_normalizado and repository.get_by_email(correo_normalizado)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
        detail="Ya existe un usuario con ese C.I. o correo.")

    partes_nombre = payload.nombre_completo.strip().split(maxsplit=1)
    if len(partes_nombre) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ingrese nombres y apellido paterno.")

    nuevo_usuario = UsuarioModel(
        ci=payload.ci.strip(),
        nombres=partes_nombre[0],
        apellido_paterno=partes_nombre[1],
        correo=correo_normalizado,
        id_rol=payload.id_rol,
        hash_password=pwd_context.hash(payload.password),
        activo=payload.activo,
    )
    repository.add(nuevo_usuario)
    db.flush()
    _registrar_evento_seguridad(
        db,
        request,
        usuario_actual.id_usuario,
        "USUARIO_CREADO",
        {"id_usuario_objetivo": nuevo_usuario.id_usuario},
    )
    db.commit()
    db.refresh(nuevo_usuario)
    return _serializar_usuario(nuevo_usuario)


@router.put("/usuarios/{id_usuario}", response_model=AdminUsuarioResponse)
def actualizar_usuario(
    id_usuario: int,
    payload: AdminUsuarioUpdate,
    request: Request,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    repository = UsuarioRepository(db)
    usuario = repository.get_by_id(id_usuario)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    if payload.ci is not None:
        usuario.ci = payload.ci.strip()
    if payload.nombre_completo is not None:
        partes_nombre = payload.nombre_completo.strip().split(maxsplit=1)
        if len(partes_nombre) < 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ingrese nombres y apellido paterno.")
        usuario.nombres, usuario.apellido_paterno = partes_nombre
    if payload.correo is not None:
        usuario.correo = payload.correo.strip()
    if payload.id_rol is not None:
        rol = repository.get_role(payload.id_rol)
        if not rol or rol.nombre.upper() not in SUPPORTED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rol indicado no existe o no está permitido.",
            )
        usuario.id_rol = payload.id_rol
    activo_anterior = usuario.activo
    if payload.activo is not None:
        usuario.activo = payload.activo

    existente_ci = repository.get_by_ci(usuario.ci)
    existente_correo = repository.get_by_email(usuario.correo) if usuario.correo else None
    existente = any(
        item is not None and item.id_usuario != id_usuario
        for item in (existente_ci, existente_correo)
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe otro usuario con ese C.I. o correo.",
        )

    if usuario.activo != activo_anterior:
        _registrar_evento_seguridad(
            db,
            request,
            usuario_actual.id_usuario,
            "USUARIO_DESACTIVADO" if not usuario.activo else "USUARIO_ACTIVADO",
            {"id_usuario_objetivo": id_usuario},
        )
    db.commit()
    db.refresh(usuario)
    return _serializar_usuario(usuario)


@router.put("/usuarios/{id_usuario}/reset-password")
def restablecer_password(
    id_usuario: int,
    payload: AdminUsuarioResetPassword,
    request: Request,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    usuario = UsuarioRepository(db).get_by_id(id_usuario)
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
    _registrar_evento_seguridad(
        db,
        request,
        usuario_actual.id_usuario,
        "CAMBIO_CREDENCIALES",
        {"id_usuario_objetivo": id_usuario, "tipo": "restablecimiento_password"},
    )
    db.commit()
    return {"message": "Contraseña actualizada correctamente."}


@router.get("/auditoria/seguridad", response_model=list[SecurityAuditEventResponse])
def obtener_auditoria_seguridad(
    limit: int = 200,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
) -> list[SecurityAuditEventResponse]:
    del usuario_actual
    if not 1 <= limit <= 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="limit debe estar entre 1 y 500.",
        )
    events = AuditoriaRepository(db).list_security_recent(limit)
    return [
        SecurityAuditEventResponse(
            id_evento=item.id_evento,
            id_usuario=item.id_usuario,
            evento=item.evento,
            ip_origen=str(item.ip_origen) if item.ip_origen is not None else None,
            user_agent=item.user_agent,
            detalles=item.detalles,
            creado_en=item.creado_en,
        )
        for item in events
    ]


@router.get("/auditoria", response_model=list[AuditoriaAdminResponse])
def obtener_auditoria(
    db: Session = Depends(get_db),
    usuario_actual: UsuarioModel = Depends(require_roles(["ADMIN"])),
):
    del usuario_actual
    auditorias = AuditoriaRepository(db).list_recent()
    respuesta: list[AuditoriaAdminResponse] = []

    for item in auditorias:
        respuesta.append(
            AuditoriaAdminResponse(
                id_enmienda=item.id_auditoria,
                id_orden=item.id_orden,
                id_resultado=item.id_resultado_version,
                modulo=item.entidad or item.accion,
                usuario_solicitante=(
                    " ".join(
                        parte
                        for parte in (
                            item.usuario.nombres,
                            item.usuario.apellido_paterno,
                            item.usuario.apellido_materno,
                        )
                        if parte
                    )
                    if item.usuario
                    else None
                ),
                rol_usuario=item.usuario.rol.nombre if item.usuario and item.usuario.rol else None,
                fecha=item.creado_en.isoformat() if item.creado_en else None,
                motivo=item.descripcion,
                estado=item.accion,
            )
        )

    return respuesta
