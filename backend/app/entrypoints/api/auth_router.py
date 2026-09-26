from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.adapters.db.session import get_db
from app.adapters.db.models import UsuarioModel
from app.adapters.security.auth import verify_password, create_access_token
from app.entrypoints.api.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.correo == credentials.correo).first()
    
    if not usuario or not verify_password(credentials.password, usuario.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos"
        )
    
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador."
        )

    token_data = {
        "sub": str(usuario.id_usuario),
        "correo": usuario.correo,
        "rol": usuario.rol.nombre
    }
    
    access_token = create_access_token(token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "nombre_completo": usuario.nombre_completo,
            "correo": usuario.correo,
            "rol": usuario.rol.nombre,
            "foto_perfil_url": usuario.foto_perfil_url
        }
    }