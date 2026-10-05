import api from './api';

export interface Estudio {
  id_estudio: number;
  codigo: string;
  nombre: string;
  id_estudio_version: number;
  numero_version: number;
  estrategia_calculo: string | null;
  parametros_obligatorios: string[];
}

export interface Panel {
  id_panel: number;
  codigo: string;
  nombre: string;
  descripcion: string | null;
}

export const catalogoService = {
  listarEstudios: async (): Promise<Estudio[]> => {
    const response = await api.get('/estudios');
    return response.data as Estudio[];
  },

  listarPaneles: async (): Promise<Panel[]> => {
    const response = await api.get('/paneles');
    return response.data as Panel[];
  },

  estudiosDePanel: async (idPanel: number): Promise<Estudio[]> => {
    const response = await api.get(`/paneles/${idPanel}/estudios`);
    return response.data as Estudio[];
  },
};
