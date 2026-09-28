import { Navigate } from 'react-router-dom';
import type { ReactNode } from 'react';
import { useAuth } from '../context/AuthContext';
import type { Rol } from '../types';

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: Rol[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { token, user } = useAuth();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.rol)) {
    return <Navigate to="/dashboard" replace />;
  }

  if (allowedRoles && !user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
