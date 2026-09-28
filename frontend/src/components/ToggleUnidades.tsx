interface ToggleUnidadesProps {
  value: 'porcentaje' | 'decimal';
  onChange: (value: 'porcentaje' | 'decimal') => void;
}

export function ToggleUnidades({ value, onChange }: ToggleUnidadesProps) {
  return (
    <div className="toggle-unidades">
      <button
        type="button"
        className={value === 'porcentaje' ? 'active' : ''}
        onClick={() => onChange('porcentaje')}
      >
        %
      </button>
      <button
        type="button"
        className={value === 'decimal' ? 'active' : ''}
        onClick={() => onChange('decimal')}
      >
        Decimal
      </button>
    </div>
  );
}
