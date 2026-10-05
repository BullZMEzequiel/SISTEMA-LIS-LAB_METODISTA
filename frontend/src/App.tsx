import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { NuevaOrdenPage } from './pages/Ordenes/NuevaOrdenPage';
import { PerfilPage } from './features/auth/PerfilPage';
import { CambiosPage } from './features/auditoria/CambiosPage';
import { HistorialAuditoriaPage as AuditoriaAdminPage } from './features/auditoria/HistorialAuditoriaPage';
import { DelegacionesPage } from './features/delegaciones/DelegacionesPage';
import { HistorialPage } from './features/historial/HistorialPage';
import { OrdenesPage } from './features/ordenes/OrdenesPage';
import { PapeleraPage } from './features/ordenes/PapeleraPage';
import { PendientesPage } from './features/ordenes/PendientesPage';
import { PacientesPage } from './features/pacientes/PacientesPage';
import { GestionUsuariosPage as UsuariosPage } from './features/usuarios/GestionUsuariosPage';
import { HemogramaPage } from './modules/hemograma/HemogramaPage';
import { PerfilProteicoPage } from './modules/perfil-proteico/PerfilProteicoPage';
import './App.css';

function AppRoutes() {
  const { token } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={token ? <Navigate to="/inicio" replace /> : <LoginPage />}
      />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/inicio" element={<DashboardPage />} />
        <Route path="/dashboard" element={<Navigate to="/inicio" replace />} />
        <Route
          path="/pacientes"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><PacientesPage /></ProtectedRoute>}
        />
        <Route
          path="/ordenes/nueva"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><NuevaOrdenPage /></ProtectedRoute>}
        />
        <Route
          path="/ordenes"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><OrdenesPage /></ProtectedRoute>}
        />
        <Route
          path="/pendientes"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><PendientesPage /></ProtectedRoute>}
        />
        <Route
          path="/delegaciones"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><DelegacionesPage /></ProtectedRoute>}
        />
        <Route
          path="/historial"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><HistorialPage /></ProtectedRoute>}
        />
        <Route
          path="/cambios"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><CambiosPage /></ProtectedRoute>}
        />
        <Route
          path="/papelera"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><PapeleraPage /></ProtectedRoute>}
        />
        <Route path="/perfil" element={<PerfilPage />} />
        <Route
          path="/modulos/hemograma"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><HemogramaPage /></ProtectedRoute>}
        />
        <Route
          path="/modulos/perfil-proteico"
          element={<ProtectedRoute allowedRoles={['BIOQUIMICO']}><PerfilProteicoPage /></ProtectedRoute>}
        />
        <Route
          path="/admin/usuarios"
          element={<ProtectedRoute allowedRoles={['ADMIN']}><UsuariosPage /></ProtectedRoute>}
        />
        <Route
          path="/admin/auditoria"
          element={<ProtectedRoute allowedRoles={['ADMIN']}><AuditoriaAdminPage /></ProtectedRoute>}
        />
      </Route>

      <Route path="/" element={<Navigate to={token ? '/inicio' : '/login'} replace />} />
      <Route path="*" element={<Navigate to={token ? '/inicio' : '/login'} replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
