import { useEffect, useMemo, useState } from 'react';
import { adminService } from '../../services/adminService';
import type { AuditoriaAdminItem } from '../../types';

export function HistorialAuditoriaPage() {
  const [registros, setRegistros] = useState<AuditoriaAdminItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filtro, setFiltro] = useState('');
  const [fecha, setFecha] = useState('');

  useEffect(() => {
    const cargar = async () => {
      try {
        const data = await adminService.getAuditoria();
        setRegistros(data);
      } catch (error) {
        console.error('No se pudo cargar auditoría', error);
      } finally {
        setLoading(false);
      }
    };

    void cargar();
  }, []);

  const registrosFiltrados = useMemo(() => {
    return registros.filter((registro) => {
      const texto = `${registro.usuario_solicitante ?? ''} ${registro.modulo ?? ''} ${registro.motivo ?? ''}`.toLowerCase();
      const cumpleTexto = texto.includes(filtro.toLowerCase());
      const cumpleFecha = !fecha || (registro.fecha ?? '').startsWith(fecha);
      return cumpleTexto && cumpleFecha;
    });
  }, [registros, filtro, fecha]);

  return (
    <div style={styles.page}>
      <div style={styles.headerRow}>
        <div>
          <p style={styles.eyebrow}>Trazabilidad</p>
          <h1>Historial de auditoría</h1>
        </div>
      </div>

      <div style={styles.filters}>
        <input
          type="search"
          placeholder="Buscar por usuario, módulo o motivo"
          value={filtro}
          onChange={(event) => setFiltro(event.target.value)}
        />
        <input
          type="date"
          value={fecha}
          onChange={(event) => setFecha(event.target.value)}
        />
      </div>

      <div style={styles.panel}>
        {loading ? (
          <p>Cargando auditoría...</p>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Usuario</th>
                <th>Rol</th>
                <th>Módulo</th>
                <th>Motivo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {registrosFiltrados.map((registro) => (
                <tr key={registro.id_enmienda}>
                  <td>{registro.fecha ? new Date(registro.fecha).toLocaleString('es-ES') : '—'}</td>
                  <td>{registro.usuario_solicitante ?? 'Sin usuario'}</td>
                  <td>{registro.rol_usuario ?? '—'}</td>
                  <td>{registro.modulo ?? '—'}</td>
                  <td>{registro.motivo ?? '—'}</td>
                  <td>
                    <span
                      style={{
                        ...styles.badge,
                        background: registro.estado === 'APROBADA' ? '#dcfce7' : '#e2e8f0',
                        color: registro.estado === 'APROBADA' ? '#166534' : '#334155',
                      }}
                    >
                      {registro.estado ?? '—'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
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
  },
  eyebrow: {
    margin: 0,
    color: '#2563eb',
    textTransform: 'uppercase',
    letterSpacing: '0.12em',
    fontWeight: 700,
    fontSize: '0.7rem',
  },
  filters: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
    flexWrap: 'wrap',
    background: '#fff',
    borderRadius: '12px',
    padding: '14px',
    boxShadow: '0 10px 30px rgba(15, 23, 42, 0.08)',
  },
  panel: {
    background: '#fff',
    borderRadius: '14px',
    padding: '18px',
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
};
