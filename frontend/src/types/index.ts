export type Rol = 'ADMIN' | 'BIOQUIMICO' | 'INTERNO' | 'MEDICO_LECTOR';

export interface LoginRequest {
  usuario: string;
  password: string;
}

export interface Usuario {
  id_usuario: number;
  nombre_completo: string;
  correo: string;
  rol: Rol;
  foto_perfil_url?: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  usuario: Usuario;
}

export interface UsuarioAdmin {
  id_usuario: number;
  ci: string;
  nombre_completo: string;
  correo: string;
  id_rol: number;
  rol?: string | null;
  activo: boolean;
}

export interface UsuarioAdminPayload {
  ci: string;
  nombre_completo: string;
  correo: string;
  id_rol: number;
  password?: string;
  activo?: boolean;
}

export interface AuditoriaAdminItem {
  id_enmienda: number;
  id_orden: number;
  id_resultado?: number | null;
  modulo?: string | null;
  usuario_solicitante?: string | null;
  rol_usuario?: string | null;
  fecha?: string | null;
  motivo?: string | null;
  estado?: string | null;
}

export interface Paciente {
  id_paciente: number;
  ci: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string;
  sexo: string;
  telefono?: string | null;
  correo?: string | null;
  creado_en: string;
}

export interface PacienteCreate {
  ci: string;
  nombres: string;
  apellidos: string;
  fecha_nacimiento: string;
  sexo: string;
  telefono?: string | null;
  correo?: string | null;
}

export interface CalculoRequest {
  codigo_modulo: string;
  entradas: Record<string, string | number>;
}

export interface CalculoResponse {
  modulo: string;
  calculados: Record<string, string | number>;
  advertencias: string[];
}

export interface GuardarOrdenRequest {
  id_paciente?: number | null;
  paciente_nuevo?: PacienteCreate | null;
  medico_solicitante: string;
  pieza_cama?: string | null;
  codigo_modulo: string;
  valores_entrada: Record<string, string | number>;
  estado_solicitado?: string;
  id_usuario_creador?: number | null;
  rol_usuario?: string | null;
}
