import api from './api';
import type { Paciente, PacienteCreate } from '../types';
import type { Estudio } from './catalogoService';

export interface OrdenCreada {
  id_orden: number;
  folio: string;
  id_paciente: number;
  estado: string;
  estudios: Array<{
    id_estudio: number;
    id_orden_estudio: number | null;
  }>;
}

export const ordenesService = {
  buscarPaciente: async (ci: string): Promise<Paciente[]> => {
    const term = ci.trim();
    if (!term) return [];

    try {
      // 1. Intento principal: Usar el endpoint estándar /pacientes?q=...
      // Tu backend en search_patients maneja q: str = Query(min_length=1)
      const response = await api.get('/pacientes', { params: { q: term } });
      return (response.data as Paciente[]) || [];
    } catch {
      // 2. Fallback: Si el endpoint /pacientes falla, intentamos /pacientes/buscar?ci=...
      try {
        const fallbackResponse = await api.get('/pacientes/buscar', { params: { ci: term } });
        return (fallbackResponse.data as Paciente[]) || [];
      } catch {
        return [];
      }
    }
  },

  crearPaciente: async (payload: PacienteCreate): Promise<Paciente> => {
    // Tu backend PatientCreateRequest espera apellido_paterno y apellido_materno por separado
    const parts = payload.apellidos.trim().split(/\s+/);
    const apellidoPaterno = parts[0] || '';
    const apellidoMaterno = parts.slice(1).join(' ') || null;

    const response = await api.post('/pacientes', {
      ci: payload.ci.trim(),
      nombres: payload.nombres.trim(),
      apellido_paterno: apellidoPaterno,
      apellido_materno: apellidoMaterno,
      fecha_nacimiento: payload.fecha_nacimiento,
      sexo: payload.sexo,
      telefono: payload.telefono || null,
      correo: payload.correo || null,
    });
    return response.data as Paciente;
  },

  crearOrden: async (idPaciente: number, estudios: Estudio[]): Promise<OrdenCreada> => {
    const idsEstudio = [...new Set(estudios.map((study) => study.id_estudio))];
    const response = await api.post('/ordenes', {
      id_paciente: idPaciente,
      ids_estudio: idsEstudio,
    });
    return response.data as OrdenCreada;
  },
};