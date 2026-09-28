import axios from 'axios';

const resolveApiBaseUrl = (): string => {
  const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL;

  if (configuredBaseUrl && configuredBaseUrl.trim()) {
    return configuredBaseUrl.replace(/\/+$/, '');
  }

  return '';
};

const api = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('lis_token');

  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
