import api from './api';
import type { AuditoriaAdminItem, UsuarioAdmin, UsuarioAdminPayload } from '../types';

export const adminService = {
  getUsuarios: async (): Promise<UsuarioAdmin[]> => {
    const response = await api.get('/admin/usuarios');
    return response.data as UsuarioAdmin[];
  },

  createUsuario: async (payload: UsuarioAdminPayload): Promise<UsuarioAdmin> => {
    const response = await api.post('/admin/usuarios', payload);
    return response.data as UsuarioAdmin;
  },

  updateUsuario: async (id: number, payload: Partial<UsuarioAdminPayload>): Promise<UsuarioAdmin> => {
    const response = await api.put(`/admin/usuarios/${id}`, payload);
    return response.data as UsuarioAdmin;
  },

  resetPassword: async (id: number, nuevaPassword: string): Promise<{ message: string }> => {
    const response = await api.put(`/admin/usuarios/${id}/reset-password`, {
      nueva_password: nuevaPassword,
    });
    return response.data as { message: string };
  },

  getAuditoria: async (): Promise<AuditoriaAdminItem[]> => {
    const response = await api.get('/admin/auditoria');
    return response.data as AuditoriaAdminItem[];
  },
};
