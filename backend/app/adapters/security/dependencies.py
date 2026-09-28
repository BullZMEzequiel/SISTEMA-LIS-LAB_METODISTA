from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.adapters.db.models import UsuarioModel
from app.adapters.db.session import get_db
from app.adapters.security.auth import ALGORITHM, SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UsuarioModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id_usuario = payload.get("sub")
        if id_usuario is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    usuario = db.query(UsuarioModel).filter(UsuarioModel.id_usuario == int(id_usuario)).first()
    if usuario is None or not usuario.activo:
        raise credentials_exception

    return usuario


def require_roles(roles_permitidos: list[str]) -> Callable[[UsuarioModel], UsuarioModel]:
    """Dependencia que valida que el usuario autenticado tenga alguno de los roles permitidos."""

    def role_checker(usuario_actual: UsuarioModel = Depends(get_current_user)) -> UsuarioModel:
        rol_actual = usuario_actual.rol.nombre.upper() if usuario_actual.rol else ""
        if rol_actual not in {rol.strip().upper() for rol in roles_permitidos}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Permisos insuficientes. "
                    f"Requiere uno de estos roles: {roles_permitidos}"
                ),
            )
        return usuario_actual

    return role_checker
