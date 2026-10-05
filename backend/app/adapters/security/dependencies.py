from typing import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.adapters.persistence.models import UsuarioModel
from app.adapters.persistence.repositories import UsuarioRepository
from app.adapters.persistence.session import get_db
from app.adapters.security.auth import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
SUPPORTED_ROLES = frozenset({"ADMIN", "BIOQUIMICO"})


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    def audit_invalid_token(id_usuario: int | None, reason: str) -> None:
        from app.adapters.persistence.uow import SqlAlchemyUnitOfWork

        uow = SqlAlchemyUnitOfWork(db)
        uow.audits.add_security_event(
            id_usuario,
            "TOKEN_INVALIDO",
            ip_origen=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            detalles={"razon": reason},
        )
        db.commit()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id_usuario = payload.get("sub")
        if id_usuario is None:
            audit_invalid_token(None, "subject_ausente")
            raise credentials_exception
    except JWTError as exc:
        audit_invalid_token(None, "token_no_valido")
        raise credentials_exception from exc

    try:
        usuario = UsuarioRepository(db).get_by_id(int(id_usuario))
    except (TypeError, ValueError) as exc:
        audit_invalid_token(None, "subject_no_valido")
        raise credentials_exception from exc
    if usuario is None or not usuario.activo:
        audit_invalid_token(int(id_usuario), "usuario_inexistente_o_inactivo")
        raise credentials_exception

    rol = usuario.rol.nombre.upper() if usuario.rol else ""
    if rol not in SUPPORTED_ROLES:
        audit_invalid_token(usuario.id_usuario, "rol_no_autorizado")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El rol del usuario no está habilitado en el sistema.",
        )

    return usuario


def require_roles(roles_permitidos: list[str]) -> Callable[[UsuarioModel], UsuarioModel]:
    """Dependencia que valida que el usuario autenticado tenga alguno de los roles permitidos."""
    roles = {rol.strip().upper() for rol in roles_permitidos} & SUPPORTED_ROLES

    def role_checker(usuario_actual: UsuarioModel = Depends(get_current_user)) -> UsuarioModel:
        rol_actual = usuario_actual.rol.nombre.upper() if usuario_actual.rol else ""
        if rol_actual not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Permisos insuficientes. "
                    f"Requiere uno de estos roles: {sorted(roles)}"
                ),
            )
        return usuario_actual

    return role_checker
