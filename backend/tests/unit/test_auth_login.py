from uuid import uuid4

from app.adapters.db.models import RolModel, UsuarioModel
from app.adapters.db.session import SessionLocal
from app.adapters.security.auth import pwd_context
from app.entrypoints.api.auth_router import login
from app.entrypoints.api.schemas import LoginRequest


def test_login_accepts_ci_and_simple_password() -> None:
    db = SessionLocal()
    unique = uuid4().hex[:8]
    role = db.query(RolModel).filter_by(nombre="ADMIN").first()
    if role is None:
        role = RolModel(nombre="ADMIN", descripcion="Administrador de pruebas")
        db.add(role)
        db.commit()
        db.refresh(role)

    usuario = UsuarioModel(
        id_rol=role.id_rol,
        ci=f"CI-{unique}",
        nombre_completo=f"Usuario Prueba {unique}",
        correo=f"prueba-{unique}@hospitalmetodista.org",
        hash_password=pwd_context.hash("12345"),
        foto_perfil_url=None,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    try:
        response = login(LoginRequest(usuario=usuario.ci, password="12345"), db=db)
        assert response["usuario"]["correo"] == usuario.correo
        assert response["access_token"]
    finally:
        db.delete(usuario)
        db.commit()
        db.close()
