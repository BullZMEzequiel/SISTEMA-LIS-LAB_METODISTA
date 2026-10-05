import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function DashboardPage() {
  const { user } = useAuth();

  const workflowCards = [
    {
      title: 'Pacientes',
      description: 'Buscar y preparar el registro del paciente antes de iniciar una orden.',
      path: '/pacientes',
      roles: ['BIOQUIMICO'],
    },
    {
      title: 'Nueva orden',
      description: 'Seleccionar paciente, estudios manuales o desde un panel y generar folio.',
      path: '/ordenes/nueva',
      roles: ['BIOQUIMICO'],
    },
    {
      title: 'Pendientes',
      description: 'Continuar órdenes y estudios en borrador.',
      path: '/pendientes',
      roles: ['BIOQUIMICO'],
    },
    {
      title: 'Órdenes colaborativas',
      description: 'Consultar el trabajo delegado y su seguimiento.',
      path: '/delegaciones',
      roles: ['BIOQUIMICO'],
    },
    {
      title: 'Historial',
      description: 'Consultar órdenes oficializadas, resultados y versiones.',
      path: '/historial',
      roles: ['BIOQUIMICO'],
    },
  ];

  const adminCards = [
    {
      title: 'Gestión de usuarios',
      description: 'Crear, editar, reactivar, desactivar y resetear claves de acceso.',
      path: '/admin/usuarios',
      roles: ['ADMIN'],
    },
    {
      title: 'Auditoría',
      description: 'Revisar trazabilidad, cambios clínicos y actividades del sistema.',
      path: '/admin/auditoria',
      roles: ['ADMIN'],
    },
  ];

  return (
    <div className="dashboard-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Bienvenido</p>
          <h1>{user?.nombre_completo ?? 'Usuario del sistema'}</h1>
        </div>
        <div className="badge-role">{user?.rol ?? 'Sin rol'}</div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <span>Rol actual</span>
          <strong>{user?.rol ?? 'Sin asignación'}</strong>
        </div>
        <div className="stat-card">
          <span>Estado</span>
          <strong>Operativo</strong>
        </div>
        <div className="stat-card">
          <span>Conectado</span>
          <strong>JWT activo</strong>
        </div>
      </div>

      <section className="workflow-intro">
        <h2>Trabajo del laboratorio</h2>
        <p>Las órdenes organizan el flujo; los estudios clínicos se abren desde cada orden, no desde Inicio.</p>
      </section>

      <div className="cards-grid">
        {workflowCards.map((module) => {
          const canAccess = user ? module.roles.includes(user.rol) : false;

          return (
            <div className="module-card" key={module.path}>
              <div>
              <p className="eyebrow">Flujo</p>
                <h3>{module.title}</h3>
              </div>
              <p>{module.description}</p>
              {canAccess ? (
                <Link to={module.path} className="primary-btn small-btn">
                  Abrir espacio
                </Link>
              ) : (
                <span className="locked-label">Sin permisos</span>
              )}
            </div>
          );
        })}
      </div>

      {user?.rol === 'ADMIN' ? (
        <div className="cards-grid" style={{ marginTop: '20px' }}>
          {adminCards.map((module) => (
            <div className="module-card" key={module.path}>
              <div>
                <p className="eyebrow">Admin</p>
                <h3>{module.title}</h3>
              </div>
              <p>{module.description}</p>
              <Link to={module.path} className="primary-btn small-btn">
                Abrir panel
              </Link>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
