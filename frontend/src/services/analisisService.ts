import api from './api';
import type { CalculoRequest, CalculoResponse, GuardarOrdenRequest } from '../types';

export const analisisService = {
  calcular: async (payload: CalculoRequest): Promise<CalculoResponse> => {
    const response = await api.post('/api/analisis/calcular', payload);
    return response.data as CalculoResponse;
  },

  guardar: async (payload: GuardarOrdenRequest) => {
    const response = await api.post('/api/analisis/guardar', payload);
    return response.data;
  },
};
