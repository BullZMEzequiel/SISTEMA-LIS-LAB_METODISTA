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
    const response = await api.get('/pacientes/buscar', { params: { ci } });
    return response.data as Paciente[];
  },

  crearPaciente: async (payload: PacienteCreate): Promise<Paciente> => {
    const [apellidoPaterno, ...apellidoMaterno] = payload.apellidos.trim().split(/\s+/);
    const response = await api.post('/pacientes', {
      ci: payload.ci,
      nombres: payload.nombres,
      apellido_paterno: apellidoPaterno,
      apellido_materno: apellidoMaterno.join(' ') || null,
      fecha_nacimiento: payload.fecha_nacimiento,
      sexo: payload.sexo,
      telefono: payload.telefono,
      correo: payload.correo,
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
