import api from "./api"; // ajusta al nombre real de tu cliente axios (el mismo que usa adminService.ts)

export interface Paciente {
  id_paciente: number;
  ci: string;
  nombres: string;
  apellido_paterno: string;
  apellido_materno?: string;
  fecha_nacimiento: string;
  sexo: "M" | "F";
  telefono?: string;
  correo?: string;
}

export interface PacienteCreatePayload {
  ci: string;
  nombres: string;
  apellido_paterno: string;
  apellido_materno?: string;
  fecha_nacimiento: string;
  sexo: "M" | "F";
  telefono?: string;
  correo?: string;
}

export const pacientesService = {
  buscar: (q: string) =>
    api.get<Paciente[]>(`/pacientes`, { params: { q } }).then((r) => r.data),

  crear: (payload: PacienteCreatePayload) =>
    api.post<Paciente>(`/pacientes`, payload).then((r) => r.data),

  actualizar: (id: number, payload: Partial<PacienteCreatePayload>) =>
    api.put<Paciente>(`/pacientes/${id}`, payload).then((r) => r.data),
};