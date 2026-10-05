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
          <NavLink to="/inicio">Inicio</NavLink>
          {user?.rol === 'BIOQUIMICO' ? (
            <>
              <NavLink to="/pacientes">Pacientes</NavLink>
              <NavLink to="/ordenes/nueva">Nueva orden</NavLink>
              <NavLink to="/ordenes">Mis órdenes</NavLink>
              <NavLink to="/pendientes">Pendientes</NavLink>
              <NavLink to="/delegaciones">Colaborativas</NavLink>
              <NavLink to="/historial">Historial</NavLink>
              <NavLink to="/cambios">Cambios</NavLink>
              <NavLink to="/papelera">Papelera</NavLink>
            </>
          ) : null}
          <NavLink to="/perfil">Perfil</NavLink>
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
