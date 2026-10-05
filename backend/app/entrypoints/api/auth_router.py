from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.adapters.persistence.models import UsuarioModel
from app.adapters.persistence.repositories import UsuarioRepository
from app.adapters.persistence.session import get_db
from app.adapters.persistence.uow import SqlAlchemyUnitOfWork
from app.adapters.security.auth import create_access_token, verify_password
from app.adapters.security.dependencies import SUPPORTED_ROLES, get_current_user
from app.application.use_cases.consultas import CerrarSesion
from app.entrypoints.api.schemas import LoginRequest, TokenResponse
from app.entrypoints.api.dependencies import get_unit_of_work
from app.entrypoints.api.contracts import MeResponse
from app.application.ports import UnitOfWork

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, request: Request, db: Session = Depends(get_db)):
    identificador = credentials.usuario.strip()
    usuario = UsuarioRepository(db).get_by_identifier(identificador)

    uow = SqlAlchemyUnitOfWork(db)
    ip_origen = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    if not usuario or not verify_password(credentials.password, usuario.hash_password):
        uow.audits.add_security_event(
            usuario.id_usuario if usuario else None,
            "LOGIN_FALLIDO",
            ip_origen=ip_origen,
            user_agent=user_agent,
            detalles={"identificador": identificador},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos"
        )

    if not usuario.activo:
        uow.audits.add_security_event(
            usuario.id_usuario,
            "USUARIO_DESACTIVADO",
            ip_origen=ip_origen,
            user_agent=user_agent,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador."
        )

    if not usuario.rol or usuario.rol.nombre.upper() not in SUPPORTED_ROLES:
        uow.audits.add_security_event(
            usuario.id_usuario,
            "ROL_NO_AUTORIZADO",
            ip_origen=ip_origen,
            user_agent=user_agent,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El rol del usuario no está habilitado en el sistema.",
        )

    token_data = {
        "sub": str(usuario.id_usuario),
        "correo": usuario.correo,
        "rol": usuario.rol.nombre
    }
    
    access_token = create_access_token(token_data)
    usuario.ultimo_ingreso = datetime.now(timezone.utc)
    uow.audits.add_security_event(
        usuario.id_usuario,
        "LOGIN_EXITOSO",
        ip_origen=ip_origen,
        user_agent=user_agent,
    )
    db.commit()
    nombre_completo = " ".join(
        parte for parte in (usuario.nombres, usuario.apellido_paterno, usuario.apellido_materno) if parte
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "nombre_completo": nombre_completo,
            "correo": usuario.correo,
            "rol": usuario.rol.nombre,
            "foto_perfil_url": usuario.foto_perfil_url
        }
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    usuario_actual: UsuarioModel = Depends(get_current_user),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> Response:
    CerrarSesion(uow).execute(
        usuario_actual.id_usuario,
        ip_origen=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeResponse)
def me(usuario_actual: UsuarioModel = Depends(get_current_user)) -> MeResponse:
    nombre = " ".join(
        value for value in (usuario_actual.nombres, usuario_actual.apellido_paterno, usuario_actual.apellido_materno)
        if value
    )
    return MeResponse(
        id_usuario=usuario_actual.id_usuario,
        nombre_completo=nombre,
        correo=usuario_actual.correo,
        rol=usuario_actual.rol.nombre,
        foto_perfil_url=usuario_actual.foto_perfil_url,
        ci=usuario_actual.ci,
    )