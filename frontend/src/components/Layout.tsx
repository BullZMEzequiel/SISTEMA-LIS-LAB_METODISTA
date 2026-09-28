import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">LIS Hospital Metodista</div>
          <div className="subtitle">Laboratorio digital</div>
        </div>

        <nav className="topnav">
          <NavLink to="/dashboard">Dashboard</NavLink>
          <NavLink to="/modulos/hemograma">Hemograma</NavLink>
          <NavLink to="/modulos/perfil-proteico">Perfil Proteico</NavLink>
          {user?.rol === 'ADMIN' ? (
            <>
              <NavLink to="/admin/usuarios">Usuarios</NavLink>
              <NavLink to="/admin/auditoria">Auditoría</NavLink>
            </>
          ) : null}
        </nav>

        <div className="user-box">
          <div>
            <strong>{user?.nombre_completo ?? 'Usuario'}</strong>
            <span>{user?.rol ?? 'Sin rol'}</span>
          </div>
          <button type="button" onClick={logout} className="logout-btn">
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="page-container">
        <Outlet />
      </main>
    </div>
  );
}
