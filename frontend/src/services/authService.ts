import api from './api';
import type { LoginRequest, LoginResponse } from '../types';

export const authService = {
  login: async (payload: LoginRequest): Promise<LoginResponse> => {
    const response = await api.post('/auth/login', payload);
    return response.data as LoginResponse;
  },
};
