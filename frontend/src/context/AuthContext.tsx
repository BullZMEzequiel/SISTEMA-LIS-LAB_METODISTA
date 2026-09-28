import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import type { LoginResponse, Usuario } from '../types';

interface AuthContextValue {
  token: string | null;
  user: Usuario | null;
  login: (payload: LoginResponse) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function readStoredUser(): Usuario | null {
  const rawUser = localStorage.getItem('lis_user');
  if (!rawUser) return null;

  try {
    return JSON.parse(rawUser) as Usuario;
  } catch {
    return null;
  }
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const payloadBase64 = token.split('.')[1];
    if (!payloadBase64) return null;

    const normalized = payloadBase64.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    const decoded = window.atob(padded);
    return JSON.parse(decoded) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function isJwtExpired(token: string | null): boolean {
  if (!token) return true;

  const payload = decodeJwtPayload(token);
  const expiration = payload?.exp;

  if (payload === null || typeof expiration !== 'number' || Number.isNaN(expiration)) {
    return true;
  }

  return Date.now() >= expiration * 1000;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => {
    const storedToken = localStorage.getItem('lis_token');
    if (isJwtExpired(storedToken)) {
      localStorage.removeItem('lis_token');
      localStorage.removeItem('lis_user');
      return null;
    }
    return storedToken;
  });

  const [user, setUser] = useState<Usuario | null>(() => readStoredUser());

  useEffect(() => {
    if (token && !isJwtExpired(token)) {
      localStorage.setItem('lis_token', token);
    } else {
      localStorage.removeItem('lis_token');
      setToken(null);
      setUser(null);
    }
  }, [token]);

  useEffect(() => {
    if (user) {
      localStorage.setItem('lis_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('lis_user');
    }
  }, [user]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      login: (payload: LoginResponse) => {
        setToken(payload.access_token);
        setUser(payload.usuario);
      },
      logout: () => {
        localStorage.removeItem('lis_token');
        localStorage.removeItem('lis_user');
        setToken(null);
        setUser(null);
      },
    }),
    [token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }

  return context;
}
