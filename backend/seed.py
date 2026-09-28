import sys
from pathlib import Path

# Ajustar path para importar desde app
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from passlib.context import CryptContext
from app.adapters.db.session import SessionLocal
from app.adapters.db.models import RolModel, UsuarioModel

# Configuración de hashing de contraseñas
pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def seed_data():
    db = SessionLocal()
    try:
        print("🌱 Iniciando carga de datos iniciales (Seed)...")

        # 1. Verificar e insertar Roles
        roles_base = [
            {"nombre": "ADMIN", "descripcion": "Administrador total del sistema"},
            {"nombre": "BIOQUIMICO", "descripcion": "Captura, calcula, delega y firma oficial"},
            {"nombre": "INTERNO", "descripcion": "Captura borradores pendientes de validación"},
            {"nombre": "MEDICO_LECTOR", "descripcion": "Consulta resultados en solo lectura"},
            {"nombre": "JEFE_AREA", "descripcion": "Supervisa y aprueba enmiendas clínicas"},
        ]

        roles_db = {}
        for r in roles_base:
            rol_existente = db.query(RolModel).filter_by(nombre=r["nombre"]).first()
            if not rol_existente:
                nuevo_rol = RolModel(nombre=r["nombre"], descripcion=r["descripcion"])
                db.add(nuevo_rol)
                db.commit()
                db.refresh(nuevo_rol)
                roles_db[r["nombre"]] = nuevo_rol
                print(f"  └─ Rol creado: {r['nombre']}")
            else:
                roles_db[r["nombre"]] = rol_existente

        # 2. Usuarios de Prueba Initiales
        usuarios_base = [
            {
                "ci": "1234567",
                "nombre_completo": "Administrador Sistema",
                "correo": "admin@hospitalmetodista.org",
                "password": "12345",
                "rol": roles_db["ADMIN"].id_rol,
                "foto_perfil_url": "/avatars/admin.png"
            },
            {
                "ci": "7654321",
                "nombre_completo": "Dra. Bioquímica Principal",
                "correo": "bioquimica@hospitalmetodista.org",
                "password": "12345",
                "rol": roles_db["BIOQUIMICO"].id_rol,
                "foto_perfil_url": "/avatars/dra1.png"
            },
            {
                "ci": "8888888",
                "nombre_completo": "Interno de Laboratorio",
                "correo": "interno@hospitalmetodista.org",
                "password": "12345",
                "rol": roles_db["INTERNO"].id_rol,
                "foto_perfil_url": "/avatars/interno.png"
            }
        ]

        for u in usuarios_base:
            usr_existente = db.query(UsuarioModel).filter_by(correo=u["correo"]).first()
            if not usr_existente:
                nuevo_usuario = UsuarioModel(
                    ci=u["ci"],
                    nombre_completo=u["nombre_completo"],
                    correo=u["correo"],
                    hash_password=hash_password(u["password"]),
                    id_rol=u["rol"],
                    foto_perfil_url=u["foto_perfil_url"],
                    activo=True
                )
                db.add(nuevo_usuario)
                db.commit()
                print(f"  └─ Usuario creado: {u['correo']} ({u['nombre_completo']})")

        print("✅ Seed completado con éxito.")

    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()