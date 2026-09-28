import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { GestionUsuariosPage } from './pages/admin/GestionUsuariosPage';
import { HistorialAuditoriaPage } from './pages/admin/HistorialAuditoriaPage';
import { HemogramaPage } from './pages/Modulos/HemogramaPage';
import { PerfilProteicoPage } from './pages/Modulos/PerfilProteicoPage';
import './App.css';

function AppRoutes() {
  const { token } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={token ? <Navigate to="/dashboard" replace /> : <LoginPage />}
      />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/modulos/hemograma" element={<HemogramaPage />} />
        <Route path="/modulos/perfil-proteico" element={<PerfilProteicoPage />} />
        <Route
          path="/admin/usuarios"
          element={<ProtectedRoute allowedRoles={['ADMIN']}><GestionUsuariosPage /></ProtectedRoute>}
        />
        <Route
          path="/admin/auditoria"
          element={<ProtectedRoute allowedRoles={['ADMIN']}><HistorialAuditoriaPage /></ProtectedRoute>}
        />
      </Route>

      <Route path="/" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
      <Route path="*" element={<Navigate to={token ? '/dashboard' : '/login'} replace />} />
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
