import { useEffect, useState } from 'react';
import { adminService } from '../../services/adminService';
import type { UsuarioAdmin, UsuarioAdminPayload } from '../../types';
import { ModalUsuario } from './ModalUsuario';

export function GestionUsuariosPage() {
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [modo, setModo] = useState<'crear' | 'editar'>('crear');
  const [usuarioSeleccionado, setUsuarioSeleccionado] = useState<UsuarioAdmin | null>(null);

  const fetchUsuarios = async () => {
    try {
      const data = await adminService.getUsuarios();
      setUsuarios(data);
    } catch (error) {
      console.error('No se pudo cargar usuarios', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchUsuarios();
  }, []);

  const handleCreateOrEdit = async (payload: UsuarioAdminPayload) => {
    if (modo === 'crear') {
      await adminService.createUsuario(payload);
    } else if (usuarioSeleccionado) {
      await adminService.updateUsuario(usuarioSeleccionado.id_usuario, payload);
    }

    await fetchUsuarios();
  };

  const openNewModal = () => {
    setModo('crear');
    setUsuarioSeleccionado(null);
    setModalOpen(true);
  };

  const openEditModal = (usuario: UsuarioAdmin) => {
    setModo('editar');
    setUsuarioSeleccionado(usuario);
    setModalOpen(true);
  };

  const handleResetPassword = async (usuario: UsuarioAdmin) => {
    const nueva = window.prompt(`Ingrese la nueva contraseña para ${usuario.nombre_completo}:`, '123456');
    if (!nueva || nueva.trim().length < 4) {
      window.alert('La contraseña debe tener al menos 4 caracteres.');
      return;
    }

    try {
      await adminService.resetPassword(usuario.id_usuario, nueva.trim());
      window.alert('Contraseña actualizada correctamente.');
    } catch (error) {
      console.error(error);
      window.alert('No se pudo restablecer la contraseña.');
    }
  };

  const toggleActivo = async (usuario: UsuarioAdmin) => {
    try {
      await adminService.updateUsuario(usuario.id_usuario, {
        activo: !usuario.activo,
      });
      await fetchUsuarios();
    } catch (error) {
      console.error(error);
      window.alert('No se pudo actualizar el estado del usuario.');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.headerRow}>
        <div>
          <p style={styles.eyebrow}>Administración</p>
          <h1>Gestión de usuarios</h1>
        </div>

        <button type="button" className="primary-btn" onClick={openNewModal}>
          + Nuevo Usuario
        </button>
      </div>

      <div style={styles.panel}>
        {loading ? (
          <p>Cargando usuarios...</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th>C.I.</th>
                <th>Nombre completo</th>
                <th>Rol</th>
                <th>Correo</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((usuario) => (
                <tr key={usuario.id_usuario}>
                  <td>{usuario.ci}</td>
                  <td>{usuario.nombre_completo}</td>
                  <td>{usuario.rol ?? 'Sin rol'}</td>
                  <td>{usuario.correo}</td>
                  <td>
                    <span
                      style={{
                        ...styles.badge,
                        background: usuario.activo ? '#dcfce7' : '#fee2e2',
                        color: usuario.activo ? '#166534' : '#991b1b',
                      }}
                    >
                      {usuario.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td>
                    <div style={styles.actionGroup}>
                      <button type="button" onClick={() => openEditModal(usuario)} style={styles.secondaryButton}>
                        Editar
                      </button>
                      <button type="button" onClick={() => handleResetPassword(usuario)} style={styles.secondaryButton}>
                        Restablecer clave
                      </button>
                      <button type="button" onClick={() => toggleActivo(usuario)} style={styles.secondaryButton}>
                        {usuario.activo ? 'Desactivar' : 'Activar'}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <ModalUsuario
        open={modalOpen}
        modo={modo}
        usuario={usuarioSeleccionado}
        onClose={() => setModalOpen(false)}
        onSubmit={handleCreateOrEdit}
      />
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    display: 'grid',
    gap: '20px',
  },
  headerRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '16px',
  },
  eyebrow: {
    margin: 0,
    color: '#2563eb',
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    fontWeight: 700,
    fontSize: '0.7rem',
  },
  panel: {
    background: '#fff',
    borderRadius: '14px',
    padding: '20px',
    boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  badge: {
    display: 'inline-block',
    padding: '6px 10px',
    borderRadius: '999px',
    fontSize: '0.75rem',
    fontWeight: 700,
  },
  secondaryButton: {
    padding: '8px 12px',
    borderRadius: '8px',
    border: '1px solid #cbd5e1',
    background: '#fff',
    cursor: 'pointer',
  },
  actionGroup: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
};
