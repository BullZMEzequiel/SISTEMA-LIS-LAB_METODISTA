import { useState } from 'react';

// --- Interfaces de Tipos TypeScript ---
export interface EstudioItem {
  id: number;
  codigo_modulo?: string;
  nombre: string;
  [key: string]: unknown;
}

export interface OrdenData {
  id_orden: number;
  folio: string;
  paciente_nombre?: string;
  paciente_ci?: string;
  [key: string]: unknown;
}

interface OrderWorkspacePageProps {
  orden: OrdenData;
  estudios: EstudioItem[];
  onGuardarBorrador?: (idEstudio: number, datos: Record<string, unknown>) => void | Promise<void>;
  onOficializar?: () => void | Promise<void>;
}

// --- Componentes Reemplazables (Mocks / Selectores) ---
const EstudioFormSelector = ({ 
  estudio, 
  onCalculate 
}: { 
  estudio: EstudioItem; 
  onCalculate: (datos: Record<string, unknown>) => void; 
}) => {
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-500">Módulo de captura activo: {estudio.codigo_modulo || estudio.nombre}</p>
      {/* Aquí se montan los formularios específicos de los 7 estudios principales */}
      <button
        onClick={() => onCalculate({})}
        className="px-4 py-2 bg-indigo-600 text-white rounded text-sm font-medium hover:bg-indigo-700 transition-colors"
      >
        Guardar borrador de {estudio.nombre}
      </button>
    </div>
  );
};

const EstudioPreviewSelector = ({ estudio }: { estudio: EstudioItem }) => {
  return (
    <div className="p-4 bg-white rounded border border-gray-200">
      <p className="text-sm font-semibold text-gray-700">Vista Previa: {estudio.nombre}</p>
      <p className="text-xs text-gray-500 mt-1">Los resultados calculados y observaciones aparecerán en este panel.</p>
    </div>
  );
};

// --- Componente Principal ---
export const OrderWorkspacePage = ({
  orden,
  estudios,
  onGuardarBorrador,
  onOficializar,
}: OrderWorkspacePageProps) => {
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const currentEstudio = estudios[currentIndex];

  const guardarYBorrador = (idEstudio: number, datos: Record<string, unknown>) => {
    if (onGuardarBorrador) {
      onGuardarBorrador(idEstudio, datos);
    }
  };

  const oficializarOrden = () => {
    if (onOficializar) {
      onOficializar();
    }
  };

  if (!estudios || estudios.length === 0) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <p className="text-gray-500">No hay estudios asignados a esta orden.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header fijo con datos del paciente y Folio */}
      <header className="bg-white p-4 shadow flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold">Folio: {orden.folio}</h2>
          <p className="text-sm text-gray-600">
            Paciente: {orden.paciente_nombre || 'N/A'} | CI: {orden.paciente_ci || 'N/A'}
          </p>
        </div>

        {/* Selector / Stepper de Estudios */}
        <div className="flex gap-2">
          {estudios.map((est: EstudioItem, idx: number) => (
            <button
              key={est.id}
              onClick={() => setCurrentIndex(idx)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                idx === currentIndex ? 'bg-blue-600 text-white font-medium' : 'bg-gray-200 hover:bg-gray-300'
              }`}
            >
              {est.nombre}
            </button>
          ))}
        </div>
      </header>

      {/* Contenido en 2 columnas estilo Develab / LIS moderno */}
      <div className="flex-1 flex overflow-hidden p-4 gap-4">
        {/* Lado Izquierdo: Formulario de Datos / Cálculos */}
        <div className="w-1/2 bg-white p-6 rounded shadow overflow-y-auto">
          <h3 className="font-bold text-lg mb-4">
            Ingreso de Datos - {currentEstudio?.nombre}
          </h3>
          {currentEstudio && (
            <EstudioFormSelector
              estudio={currentEstudio}
              onCalculate={(datos: Record<string, unknown>) =>
                guardarYBorrador(currentEstudio.id, datos)
              }
            />
          )}
        </div>

        {/* Lado Derecho: Informe Preliminar / Preview del Resultado */}
        <div className="w-1/2 bg-gray-100 p-6 rounded shadow overflow-y-auto border border-gray-300">
          <h3 className="font-bold text-lg mb-4 text-gray-700">Informe Preliminar</h3>
          {currentEstudio && <EstudioPreviewSelector estudio={currentEstudio} />}
        </div>
      </div>

      {/* Footer de Navegación Secuencial */}
      <footer className="bg-white p-4 border-t flex justify-between items-center">
        <button
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((prev) => prev - 1)}
          className="px-4 py-2 border rounded disabled:opacity-50 hover:bg-gray-50"
        >
          Anterior
        </button>
        <div>
          {currentIndex < estudios.length - 1 ? (
            <button
              onClick={() => setCurrentIndex((prev) => prev + 1)}
              className="px-6 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
            >
              Siguiente Estudio
            </button>
          ) : (
            <button
              onClick={() => oficializarOrden()}
              className="px-6 py-2 bg-green-600 text-white rounded font-medium hover:bg-green-700"
            >
              Finalizar y Oficializar Orden
            </button>
          )}
        </div>
      </footer>
    </div>
  );
};

export default OrderWorkspacePage;