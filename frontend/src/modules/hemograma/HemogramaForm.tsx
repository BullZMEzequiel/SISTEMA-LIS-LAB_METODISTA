import { useState, useEffect } from 'react';
import { ModuleFormProps } from '../types';

export interface HemogramaData {
  eritrocitos: number | string;
  hemoglobina: number | string;
  hematocrito: number | string;
  leucocitos: number | string;
  plaquetas: number | string;
  observaciones?: string;
}

export const HemogramaForm = ({ initialValues, onChange }: ModuleFormProps<HemogramaData>) => {
  const [formData, setFormData] = useState<HemogramaData>({
    eritrocitos: initialValues?.eritrocitos ?? '',
    hemoglobina: initialValues?.hemoglobina ?? '',
    hematocrito: initialValues?.hematocrito ?? '',
    leucocitos: initialValues?.leucocitos ?? '',
    plaquetas: initialValues?.plaquetas ?? '',
    observaciones: initialValues?.observaciones ?? '',
  });

  const handleChange = (field: keyof HemogramaData, value: string) => {
    const updated = { ...formData, [field]: value };
    setFormData(updated);
    if (onChange) onChange(updated);
  };

  return (
    <div className="space-y-4 text-sm">
      <h4 className="font-semibold text-gray-800 border-b pb-1">Serie Roja y Blanca</h4>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-gray-700">Eritrocitos (M/µL)</label>
          <input
            type="number"
            step="0.01"
            value={formData.eritrocitos}
            onChange={(e) => handleChange('eritrocitos', e.target.value)}
            className="w-full mt-1 p-2 border rounded border-gray-300"
          />
        </div>
        <div>
          <label className="block text-gray-700">Hemoglobina (g/dL)</label>
          <input
            type="number"
            step="0.1"
            value={formData.hemoglobina}
            onChange={(e) => handleChange('hemoglobina', e.target.value)}
            className="w-full mt-1 p-2 border rounded border-gray-300"
          />
        </div>
        <div>
          <label className="block text-gray-700">Hematocrito (%)</label>
          <input
            type="number"
            step="0.1"
            value={formData.hematocrito}
            onChange={(e) => handleChange('hematocrito', e.target.value)}
            className="w-full mt-1 p-2 border rounded border-gray-300"
          />
        </div>
        <div>
          <label className="block text-gray-700">Leucocitos (/µL)</label>
          <input
            type="number"
            value={formData.leucocitos}
            onChange={(e) => handleChange('leucocitos', e.target.value)}
            className="w-full mt-1 p-2 border rounded border-gray-300"
          />
        </div>
      </div>

      <h4 className="font-semibold text-gray-800 border-b pb-1 pt-2">Plaquetas y Observaciones</h4>
      <div className="grid grid-cols-1 gap-3">
        <div>
          <label className="block text-gray-700">Plaquetas (/µL)</label>
          <input
            type="number"
            value={formData.plaquetas}
            onChange={(e) => handleChange('plaquetas', e.target.value)}
            className="w-full mt-1 p-2 border rounded border-gray-300"
          />
        </div>
        <div>
          <label className="block text-gray-700">Observaciones frotis</label>
          <textarea
            rows={2}
            value={formData.observaciones}
            onChange={(e) => handleChange('observaciones', e.target.value)}
            className="w-full mt-1 p-2 border rounded border-gray-300"
          />
        </div>
      </div>
    </div>
  );
};