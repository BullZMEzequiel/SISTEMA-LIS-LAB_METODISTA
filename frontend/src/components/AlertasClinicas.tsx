interface AlertasClinicasProps {
  advertencias: string[];
}

export function AlertasClinicas({ advertencias }: AlertasClinicasProps) {
  if (!advertencias || advertencias.length === 0) {
    return null;
  }

  return (
    <div className="alerta-clinica" aria-live="polite">
      <strong>Advertencia clínica:</strong>
      <ul>
        {advertencias.map((advertencia, index) => (
          <li key={`${advertencia}-${index}`}>{advertencia}</li>
        ))}
      </ul>
    </div>
  );
}
