from app.adapters.db.models import RolModel, UsuarioModel
from app.adapters.db.session import SessionLocal
from app.adapters.security.auth import pwd_context


def test_crear_usuario_admin_con_hash_y_lista() -> None:
    db = SessionLocal()
    role = db.query(RolModel).filter_by(nombre="ADMIN").first()
    if role is None:
        role = RolModel(nombre="ADMIN", descripcion="Administrador de pruebas")
        db.add(role)
        db.commit()
        db.refresh(role)

    usuario = UsuarioModel(
        id_rol=role.id_rol,
        ci="CI-ADMIN-TEST-1",
        nombre_completo="Administrador Test Uno",
        correo="admin-test-1@hospitalmetodista.org",
        hash_password=pwd_context.hash("123456"),
        foto_perfil_url=None,
        activo=True,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    try:
        assert usuario.ci == "CI-ADMIN-TEST-1"
        assert usuario.hash_password != "123456"
        assert usuario.activo is True
    finally:
        db.delete(usuario)
        db.commit()
        db.close()
