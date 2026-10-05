import { useAuth } from '../../context/AuthContext';

export function PerfilPage() {
  const { user } = useAuth();

  return (
    <section className="module-page workflow-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Cuenta</p>
          <h1>Perfil</h1>
          <p>Información de la sesión activa.</p>
        </div>
      </header>
      <div className="panel profile-details">
        <div><span>Nombre</span><strong>{user?.nombre_completo ?? 'No disponible'}</strong></div>
        <div><span>Rol</span><strong>{user?.rol ?? 'No disponible'}</strong></div>
        <div><span>Correo</span><strong>{user?.correo ?? 'No disponible'}</strong></div>
      </div>
    </section>
  );
}
