import { useState } from "react";
import { pacientesService } from "../../services/pacientesService";
import type { Paciente, PacienteCreatePayload } from "../../services/pacientesService";

const FORM_VACIO: PacienteCreatePayload = {
  ci: "", nombres: "", apellido_paterno: "", apellido_materno: "",
  fecha_nacimiento: "", sexo: "M", telefono: "", correo: "",
};

export function PacientesPage() {
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState<Paciente[]>([]);
  const [buscando, setBuscando] = useState(false);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [form, setForm] = useState<PacienteCreatePayload>(FORM_VACIO);
  const [error, setError] = useState<string | null>(null);

  async function buscar(e?: React.FormEvent) {
    e?.preventDefault();
    if (query.trim().length < 2) return;
    setBuscando(true);
    setError(null);
    try {
      const data = await pacientesService.buscar(query.trim());
      setResultados(data);
      if (data.length === 0) {
        setMostrarForm(true);
        setForm({ ...FORM_VACIO, ci: /^\d+$/.test(query.trim()) ? query.trim() : "" });
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Error al buscar pacientes.");
    } finally {
      setBuscando(false);
    }
  }

  async function crearPaciente(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const nuevo = await pacientesService.crear(form);
      setResultados((prev) => [nuevo, ...prev]);
      setMostrarForm(false);
      setForm(FORM_VACIO);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Error al crear el paciente.");
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-2">Pacientes</h1>

      <form onSubmit={buscar} className="flex gap-2 my-4">
        <input
          type="text"
          placeholder="Buscar por CI, nombre o apellido..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="border rounded px-3 py-2 flex-1"
        />
        <button type="submit" disabled={buscando}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50">
          Buscar
        </button>
        <button type="button" onClick={() => { setMostrarForm(true); setForm(FORM_VACIO); }}
          className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300">
          + Nuevo paciente
        </button>
      </form>

      {error && <p className="text-red-600 mb-3">{error}</p>}

      {resultados.length > 0 && (
        <table className="w-full border-collapse mt-2">
          <thead>
            <tr className="border-b text-left text-sm text-gray-500">
              <th className="py-2">CI</th>
              <th>Nombre completo</th>
              <th>Fecha Nac.</th>
              <th>Sexo</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {resultados.map((p) => (
              <tr key={p.id_paciente} className="border-b hover:bg-gray-50">
                <td className="py-2">{p.ci}</td>
                <td>{p.nombres} {p.apellido_paterno} {p.apellido_materno ?? ""}</td>
                <td>{p.fecha_nacimiento}</td>
                <td>{p.sexo}</td>
                <td>
                  {/* Fase 13.3: este botón navegará a Nueva Orden con el paciente preseleccionado */}
                  <button type="button" className="text-blue-600 hover:underline text-sm">
                    Nueva orden
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {mostrarForm && (
        <form onSubmit={crearPaciente} className="mt-6 grid gap-3 max-w-md border rounded p-4">
          <h3 className="font-semibold">Registrar nuevo paciente</h3>
          <input placeholder="C.I." required value={form.ci} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, ci: e.target.value })} />
          <input placeholder="Nombres" required value={form.nombres} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, nombres: e.target.value })} />
          <input placeholder="Apellido paterno" required value={form.apellido_paterno} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, apellido_paterno: e.target.value })} />
          <input placeholder="Apellido materno" value={form.apellido_materno} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, apellido_materno: e.target.value })} />
          <input type="date" required value={form.fecha_nacimiento} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, fecha_nacimiento: e.target.value })} />
          <select value={form.sexo} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, sexo: e.target.value as "M" | "F" })}>
            <option value="M">Masculino</option>
            <option value="F">Femenino</option>
          </select>
          <input placeholder="Teléfono" value={form.telefono} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
          <input placeholder="Correo (opcional)" value={form.correo} className="border rounded px-3 py-2"
            onChange={(e) => setForm({ ...form, correo: e.target.value })} />
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            Guardar paciente
          </button>
        </form>
      )}
    </div>
  );
}