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

export interface RangoReferencia {
  sexo: 'M' | 'F' | null;
  edad_minima: number | null;
  edad_maxima: number | null;
  limite_inferior: number | null;
  limite_superior: number | null;
  referencia_texto: string | null;
  unidad: string | null;
}

export interface Parametro {
  id_parametro: number;
  codigo: string;
  nombre: string;
  tipo_campo: 'ENTRADA_MANUAL' | 'CALCULADO_AUTOMATICO' | 'TEXTO' | 'BOOLEANO' | 'SELECCION';
  tipo_dato: string;
  unidad_medida: string | null;
  obligatorio: boolean;
  orden_visualizacion: number;
  rangos_referencia: RangoReferencia[];
}

export interface EstudioConParametros {
  id_estudio: number;
  codigo: string;
  nombre: string;
  id_estudio_version: number;
  estrategia_calculo: string | null;
  parametros: Parametro[];
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

  parametrosDeEstudio: async (idEstudio: number): Promise<EstudioConParametros> => {
    const response = await api.get(`/estudios/${idEstudio}/parametros`);
    return response.data as EstudioConParametros;
  },
};