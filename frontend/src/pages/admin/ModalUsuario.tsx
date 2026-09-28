import { useEffect, useState, type FormEvent } from 'react';
import type { UsuarioAdmin, UsuarioAdminPayload } from '../../types';

interface ModalUsuarioProps {
  open: boolean;
  modo: 'crear' | 'editar';
  usuario?: UsuarioAdmin | null;
  onClose: () => void;
  onSubmit: (payload: UsuarioAdminPayload) => Promise<void>;
}

const emptyForm = (): UsuarioAdminPayload => ({
  ci: '',
  nombre_completo: '',
  correo: '',
  id_rol: 1,
  password: '',
  activo: true,
});

export function ModalUsuario({ open, modo, usuario, onClose, onSubmit }: ModalUsuarioProps) {
  const [form, setForm] = useState<UsuarioAdminPayload>(emptyForm());
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      if (modo === 'editar' && usuario) {
        setForm({
          ci: usuario.ci,
          nombre_completo: usuario.nombre_completo,
          correo: usuario.correo,
          id_rol: usuario.id_rol,
          activo: usuario.activo,
          password: '',
        });
      } else {
        setForm(emptyForm());
      }
    }
  }, [open, modo, usuario]);

  if (!open) return null;

  const handleChange = (field: keyof UsuarioAdminPayload, value: string | number | boolean) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);

    try {
      await onSubmit({
        ...form,
        ci: form.ci.trim(),
        nombre_completo: form.nombre_completo.trim(),
        correo: form.correo.trim(),
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={styles.modal} onClick={(event) => event.stopPropagation()}>
        <div style={styles.header}>
          <h3>{modo === 'crear' ? 'Nuevo usuario' : 'Editar usuario'}</h3>
          <button type="button" onClick={onClose} style={styles.closeButton}>×</button>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.field}>
            <span>C.I.</span>
            <input
              value={form.ci}
              onChange={(event) => handleChange('ci', event.target.value)}
              required
            />
          </label>

          <label style={styles.field}>
            <span>Nombre completo</span>
            <input
              value={form.nombre_completo}
              onChange={(event) => handleChange('nombre_completo', event.target.value)}
              required
            />
          </label>

          <label style={styles.field}>
            <span>Correo institucional</span>
            <input
              type="email"
              value={form.correo}
              onChange={(event) => handleChange('correo', event.target.value)}
              required
            />
          </label>

          <label style={styles.field}>
            <span>Rol</span>
            <select
              value={form.id_rol}
              onChange={(event) => handleChange('id_rol', Number(event.target.value))}
            >
              <option value={1}>ADMIN</option>
              <option value={2}>BIOQUIMICO</option>
              <option value={3}>INTERNO</option>
              <option value={4}>MEDICO_LECTOR</option>
            </select>
          </label>

          {modo === 'crear' ? (
            <label style={styles.field}>
              <span>Contraseña inicial</span>
              <input
                type="text"
                value={form.password ?? ''}
                onChange={(event) => handleChange('password', event.target.value)}
                placeholder="123456"
                required
              />
            </label>
          ) : null}

          <label style={styles.fieldCheckbox}>
            <input
              type="checkbox"
              checked={Boolean(form.activo)}
              onChange={(event) => handleChange('activo', event.target.checked)}
            />
            <span>Usuario activo</span>
          </label>

          <div style={styles.actions}>
            <button type="button" onClick={onClose} style={styles.secondaryButton}>Cancelar</button>
            <button type="submit" className="primary-btn" disabled={saving}>
              {saving ? 'Guardando...' : modo === 'crear' ? 'Crear usuario' : 'Guardar cambios'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(15, 23, 42, 0.6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 50,
    padding: '20px',
  },
  modal: {
    width: '100%',
    maxWidth: '560px',
    background: '#fff',
    borderRadius: '14px',
    padding: '24px',
    boxShadow: '0 20px 45px rgba(15, 23, 42, 0.2)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  closeButton: {
    border: 'none',
    background: 'transparent',
    fontSize: '2rem',
    cursor: 'pointer',
    lineHeight: 1,
  },
  form: {
    display: 'grid',
    gap: '18px',
  },
  field: {
    display: 'grid',
    gap: '8px',
    fontWeight: 600,
    color: '#0f172a',
  },
  fieldCheckbox: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontWeight: 600,
    color: '#0f172a',
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    marginTop: '10px',
  },
  secondaryButton: {
    padding: '10px 16px',
    borderRadius: '10px',
    border: '1px solid #cbd5e1',
    background: '#fff',
    cursor: 'pointer',
  },
};
