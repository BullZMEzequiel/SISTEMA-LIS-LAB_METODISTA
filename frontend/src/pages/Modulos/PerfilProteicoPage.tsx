import { useMemo, useState } from 'react';
import { AlertasClinicas } from '../../components/AlertasClinicas';
import { analisisService } from '../../services/analisisService';

const initialForm = {
  colesterol: '164',
  trigliceridos: '110',
  hdl: '48',
  proteinas_totales: '7.2',
  albumina: '4.1',
};

export function PerfilProteicoPage() {
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<Record<string, string | number>>({});
  const [advertencias, setAdvertencias] = useState<string[]>([]);

  const indicadoresDinamicos = useMemo(() => {
    const colesterol = Number(form.colesterol) || 0;
    const trigliceridos = Number(form.trigliceridos) || 0;
    const hdl = Number(form.hdl) || 0;
    const proteinasTotales = Number(form.proteinas_totales) || 0;
    const albumina = Number(form.albumina) || 0;

    const vldl = trigliceridos / 5;
    const ldl = colesterol - hdl - vldl;
    const globulina = proteinasTotales - albumina;
    const relacionAg = globulina > 0 ? albumina / globulina : 0;

    return {
      VLDL: vldl,
      LDL: ldl,
      Globulina: globulina,
      'Relación A/G': relacionAg,
    };
  }, [form]);

  const handleFieldChange = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleCalcular = async () => {
    setLoading(true);
    setError(null);

    try {
      const payload = {
        codigo_modulo: 'PERFIL_LIPIDICO',
        entradas: {
          colesterol: Number(form.colesterol),
          trigliceridos: Number(form.trigliceridos),
          hdl: Number(form.hdl),
        },
      };

      const respuestaLipidico = await analisisService.calcular(payload);
      const respuestaProteico = await analisisService.calcular({
        codigo_modulo: 'PROTEINOGRAMA',
        entradas: {
          proteinas_totales: Number(form.proteinas_totales),
          albumina: Number(form.albumina),
        },
      });

      const perfiles = {
        ...respuestaLipidico.calculados,
        ...respuestaProteico.calculados,
      };

      setResultado(perfiles);
      setAdvertencias([
        ...respuestaLipidico.advertencias,
        ...respuestaProteico.advertencias,
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'No se pudo calcular el perfil proteico.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="module-page">
      <header className="page-header compact-header">
        <div>
          <p className="eyebrow">Módulo</p>
          <h1>HC-QMC-SERO-PROT</h1>
        </div>
      </header>

      <section className="panel-grid two-columns">
        <div className="panel">
          <h3>Perfil lipídico</h3>
          <div className="grid-form">
            <label>
              <span>Colesterol total</span>
              <input value={form.colesterol} onChange={(e) => handleFieldChange('colesterol', e.target.value)} />
            </label>
            <label>
              <span>Triglicéridos</span>
              <input value={form.trigliceridos} onChange={(e) => handleFieldChange('trigliceridos', e.target.value)} />
            </label>
            <label>
              <span>HDL</span>
              <input value={form.hdl} onChange={(e) => handleFieldChange('hdl', e.target.value)} />
            </label>
          </div>
        </div>

        <div className="panel">
          <h3>Proteinograma</h3>
          <div className="grid-form">
            <label>
              <span>Proteínas totales</span>
              <input value={form.proteinas_totales} onChange={(e) => handleFieldChange('proteinas_totales', e.target.value)} />
            </label>
            <label>
              <span>Albúmina</span>
              <input value={form.albumina} onChange={(e) => handleFieldChange('albumina', e.target.value)} />
            </label>
          </div>
        </div>
      </section>

      <div className="action-row">
        <button type="button" className="primary-btn" onClick={handleCalcular} disabled={loading}>
          {loading ? 'Calculando...' : 'Calcular perfil'}
        </button>
        <button type="button" className="success-btn" onClick={() => alert('Guardar oficial pendiente de integración con end-point de firma.') }>
          Firmar oficial
        </button>
      </div>

      {error ? <div className="error-box">{error}</div> : null}
      <AlertasClinicas advertencias={advertencias} />

      <section className="panel results-panel">
        <h3>Indicadores automáticos</h3>
        <div className="results-grid">
          {Object.entries(indicadoresDinamicos).map(([key, value]) => (
            <div key={key} className="result-item">
              <span>{key}</span>
              <strong>{Number(value).toFixed(2)}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="panel results-panel">
        <h3>Resultados</h3>
        <div className="results-grid">
          {Object.entries(resultado).map(([key, value]) => (
            <div key={key} className="result-item">
              <span>{key}</span>
              <strong>{String(value)}</strong>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
