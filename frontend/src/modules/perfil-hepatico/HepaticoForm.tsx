import { useState } from 'react';
import { ModuleFormProps } from '../types';

export interface HepaticoData {
  got_ast: number | string;
  gpt_alt: number | string;
  fosfatasa_alcalina: number | string;
  bilirrubina_total: number | string;
  bilirrubina_directa: number | string;
}

export const HepaticoForm = ({ initialValues, onChange }: ModuleFormProps<HepaticoData>) => {
  const [formData, setFormData] = useState<HepaticoData>({
    got_ast: initialValues?.got_ast ?? '',
    gpt_alt: initialValues?.gpt_alt ?? '',
    fosfatasa_alcalina: initialValues?.fosfatasa_alcalina ?? '',
    bilirrubina_total: initialValues?.bilirrubina_total ?? '',
    bilirrubina_directa: initialValues?.bilirrubina_directa ?? '',
  });

  const handleChange = (field: keyof HepaticoData, value: string) => {
    const updated = { ...formData, [field]: value };
    setFormData(updated);
    if (onChange) onChange(updated);
  };

  return (
    <div className="grid grid-cols-2 gap-3 text-sm">
      <div>
        <label className="block text-gray-700">GOT / AST (U/L)</label>
        <input
          type="number"
          value={formData.got_ast}
          onChange={(e) => handleChange('got_ast', e.target.value)}
          className="w-full mt-1 p-2 border rounded border-gray-300"
        />
      </div>
      <div>
        <label className="block text-gray-700">GPT / ALT (U/L)</label>
        <input
          type="number"
          value={formData.gpt_alt}
          onChange={(e) => handleChange('gpt_alt', e.target.value)}
          className="w-full mt-1 p-2 border rounded border-gray-300"
        />
      </div>
      <div>
        <label className="block text-gray-700">Fosfatasa Alcalina (U/L)</label>
        <input
          type="number"
          value={formData.fosfatasa_alcalina}
          onChange={(e) => handleChange('fosfatasa_alcalina', e.target.value)}
          className="w-full mt-1 p-2 border rounded border-gray-300"
        />
      </div>
      <div>
        <label className="block text-gray-700">Bilirrubina Total (mg/dL)</label>
        <input
          type="number"
          step="0.1"
          value={formData.bilirrubina_total}
          onChange={(e) => handleChange('bilirrubina_total', e.target.value)}
          className="w-full mt-1 p-2 border rounded border-gray-300"
        />
      </div>
    </div>
  );
};