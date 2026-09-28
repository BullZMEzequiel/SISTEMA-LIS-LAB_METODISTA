import api from './api';
import type { Paciente, PacienteCreate } from '../types';

export const pacientesService = {
  buscarPorCi: async (ci: string): Promise<Paciente> => {
    const response = await api.get(`/api/pacientes/buscar/${ci}`);
    return response.data as Paciente;
  },

  crearPaciente: async (payload: PacienteCreate): Promise<Paciente> => {
    const response = await api.post('/api/pacientes/', payload);
    return response.data as Paciente;
  },
};
