import { HemogramaForm } from './Hemograma/HemogramaForm';
import { QuimicaForm } from './QuimicaSanguinea/QuimicaForm';
import { UroanalisisForm } from './Uroanalisis/UroanalisisForm';
import { CoproForm } from './Coproparasitologico/CoproForm';
import { LipidicoForm } from './PerfilLipidico/LipidicoForm';
import { HepaticoForm } from './PerfilHepatico/HepaticoForm';
import { RenalForm } from './PerfilRenal/RenalForm';

interface ModuleFormSelectorProps {
  codigoModulo?: string;
  initialValues?: Record<string, unknown>;
  onChange: (values: Record<string, unknown>) => void;
}

export const ModuleFormSelector = ({
  codigoModulo,
  initialValues,
  onChange,
}: ModuleFormSelectorProps) => {
  const code = codigoModulo?.toUpperCase() || '';

  if (code.includes('HEM') || code.includes('HEMOGRAMA')) {
    return <HemogramaForm initialValues={initialValues} onChange={onChange} />;
  }
  if (code.includes('QUI') || code.includes('QUIMICA')) {
    return <QuimicaForm initialValues={initialValues} onChange={onChange} />;
  }
  if (code.includes('URO') || code.includes('ORINA')) {
    return <UroanalisisForm initialValues={initialValues} onChange={onChange} />;
  }
  if (code.includes('COP') || code.includes('PARASITO')) {
    return <CoproForm initialValues={initialValues} onChange={onChange} />;
  }
  if (code.includes('LIP') || code.includes('LIPIDICO')) {
    return <LipidicoForm initialValues={initialValues} onChange={onChange} />;
  }
  if (code.includes('HEP') || code.includes('HEPATICO')) {
    return <HepaticoForm initialValues={initialValues} onChange={onChange} />;
  }
  if (code.includes('REN') || code.includes('RENAL')) {
    return <RenalForm initialValues={initialValues} onChange={onChange} />;
  }

  return (
    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded text-yellow-800 text-sm">
      Módulo sin formulario personalizado configurado ({codigoModulo || 'Genérico'}).
    </div>
  );
};