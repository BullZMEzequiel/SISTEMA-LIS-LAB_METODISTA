import { useState, type ChangeEvent, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authService } from '../services/authService';

const DEFAULT_CREDENTIALS = {
  usuario: '7654321',
  password: '12345',
};

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState(DEFAULT_CREDENTIALS);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await authService.login(form);
      login(response);
      navigate('/dashboard');
    } catch (err: unknown) {
      const message =
        typeof err === 'object' && err !== null && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            'No se pudo iniciar sesión. Verifica las credenciales.'
          : err instanceof Error
            ? err.message
            : 'No se pudo iniciar sesión. Verifica las credenciales.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-shell">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-header">
          <span className="eyebrow">LIS / Seguridad</span>
          <h1>Iniciar sesión</h1>
        </div>

        <label>
          <span>Usuario / C.I.</span>
          <input
            name="usuario"
            type="text"
            value={form.usuario}
            onChange={handleChange}
            placeholder="Ingrese su CI o correo"
            required
          />
        </label>

        <label>
          <span>Contraseña</span>
          <div style={{ position: 'relative' }}>
            <input
              name="password"
              type={showPassword ? 'text' : 'password'}
              value={form.password}
              onChange={handleChange}
              placeholder="••••••••"
              required
              style={{ width: '100%', paddingRight: '44px' }}
            />
            <button
              type="button"
              aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
              onClick={() => setShowPassword((current) => !current)}
              style={{
                position: 'absolute',
                right: '10px',
                top: '50%',
                transform: 'translateY(-50%)',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                fontSize: '1.1rem',
              }}
            >
              {showPassword ? '🙈' : '👁️'}
            </button>
          </div>
        </label>

        {error ? <div className="error-box">{error}</div> : null}

        <button type="submit" className="primary-btn" disabled={loading}>
          {loading ? 'Validando...' : 'Ingresar al sistema'}
        </button>
      </form>
    </div>
  );
}
