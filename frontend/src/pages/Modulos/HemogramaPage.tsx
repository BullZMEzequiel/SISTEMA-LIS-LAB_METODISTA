import { useMemo, useState } from 'react';
import { AlertasClinicas } from '../../components/AlertasClinicas';
import { ToggleUnidades } from '../../components/ToggleUnidades';
import { useAuth } from '../../context/AuthContext';
import { analisisService } from '../../services/analisisService';
import { pacientesService } from '../../services/pacientesService';
import type { Paciente } from '../../types';

type DisplayMode = 'porcentaje' | 'decimal';

const initialForm = {
  hematocrito: '48',
  globulos_blancos: '7500',
  segmentados: '62',
  linfocitos: '30',
  eosinofilos: '3',
  monocitos: '4',
  cayados: '1',
};

export function HemogramaPage() {
  const { user } = useAuth();
  const [ci, setCi] = useState('9999999');
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [form, setForm] = useState(initialForm);
  const [unidad, setUnidad] = useState<DisplayMode>('porcentaje');
  const [resultado, setResultado] = useState<Record<string, string | number>>({});
  const [advertencias, setAdvertencias] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSaveDraft = user?.rol === 'BIOQUIMICO';
  const canApproveOfficial = user?.rol === 'BIOQUIMICO';

  const convertirAentrada = (valor: string) => {
    const numero = Number(valor);
    if (Number.isNaN(numero)) return 0;
    return unidad === 'porcentaje' ? numero / 100 : numero;
  };

  const metadataPaciente = useMemo(
    () =>
      paciente
        ? `${paciente.nombres} ${paciente.apellidos} · C.I. ${paciente.ci}`
        : 'Sin paciente cargado',
    [paciente],
  );

  const diferencialTotal = useMemo(() => {
    const valores = [
      convertirAentrada(form.segmentados),
      convertirAentrada(form.linfocitos),
      convertirAentrada(form.eosinofilos),
      convertirAentrada(form.monocitos),
      convertirAentrada(form.cayados),
    ];

    return valores.reduce((acumulado, valor) => acumulado + valor, 0);
  }, [form, unidad]);

  const diferenciaAbsoluta = Math.abs(diferencialTotal - 1);
  const bloqueoLeucocitos = diferencialTotal > 1.01 || diferencialTotal < 0.99;
  const avisoLeucocitos = diferenciaAbsoluta > 0.0001 && diferenciaAbsoluta <= 0.01;

  const handleBuscarPaciente = async () => {
    try {
      const data = await pacientesService.buscarPorCi(ci);
      setPaciente(data);
      setError(null);
    } catch {
      setError('No se encontró un paciente con esa C.I.');
    }
  };

  const handleFieldChange = (field: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [field]: value }));
  };

  const handleCalcular = async () => {
    if (bloqueoLeucocitos) {
      setError('El diferencial de leucocitos queda fuera del rango clínico aceptable; corrige los valores antes de calcular.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        codigo_modulo: 'HEMOGRAMA',
        entradas: {
          hematocrito: Number(form.hematocrito),
          globulos_blancos: Number(form.globulos_blancos),
          segmentados: convertirAentrada(form.segmentados),
          linfocitos: convertirAentrada(form.linfocitos),
          eosinofilos: convertirAentrada(form.eosinofilos),
          monocitos: convertirAentrada(form.monocitos),
          cayados: convertirAentrada(form.cayados),
        },
      };

      const response = await analisisService.calcular(payload);
      setResultado(response.calculados);
      setAdvertencias(response.advertencias ?? []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'No se pudo calcular el hemograma.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleGuardarOrden = async (estado: 'BORRADOR' | 'OFICIAL') => {
    if (!paciente) {
      setError('Primero debes buscar un paciente para guardar la orden.');
      return;
    }

    if (bloqueoLeucocitos) {
      setError('El diferencial no cumple la tolerancia de leucocitos; no se puede enviar la orden.');
      return;
    }

    if (estado === 'OFICIAL' && !canApproveOfficial) {
      setError('No tienes permisos para aprobar y firmar un resultado oficial.');
      return;
    }

    try {
      await analisisService.guardar({
        id_paciente: paciente.id_paciente,
        medico_solicitante: 'Médico de laboratorio',
        pieza_cama: 'SALA 1',
        codigo_modulo: 'HEMOGRAMA',
        valores_entrada: {
          hematocrito: Number(form.hematocrito),
          globulos_blancos: Number(form.globulos_blancos),
          segmentados: convertirAentrada(form.segmentados),
          linfocitos: convertirAentrada(form.linfocitos),
          eosinofilos: convertirAentrada(form.eosinofilos),
          monocitos: convertirAentrada(form.monocitos),
          cayados: convertirAentrada(form.cayados),
        },
        estado_solicitado: estado,
        id_usuario_creador: user?.id_usuario ?? 1,
        rol_usuario: user?.rol ?? 'BIOQUIMICO',
      });
      setError(null);
      setAdvertencias(['Orden guardada correctamente.']);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'No se pudo guardar la orden.';
      setError(message);
    }
  };

  return (
    <div className="module-page">
      <header className="page-header compact-header">
        <div>
          <p className="eyebrow">Módulo</p>
          <h1>HC-QMC-SEROL-EGO</h1>
        </div>
        <ToggleUnidades value={unidad} onChange={setUnidad} />
      </header>

      <section className="panel-grid two-columns">
        <div className="panel">
          <h3>Paciente</h3>
          <div className="inline-search">
            <input value={ci} onChange={(e) => setCi(e.target.value)} placeholder="C.I. del paciente" />
            <button type="button" className="secondary-btn" onClick={handleBuscarPaciente}>
              Buscar
            </button>
          </div>
          <div className="patient-meta">{metadataPaciente}</div>
        </div>

        <div className="panel">
          <h3>Parámetros clínicos</h3>
          <div className="grid-form">
            <label>
              <span>Hematocrito</span>
              <input value={form.hematocrito} onChange={(e) => handleFieldChange('hematocrito', e.target.value)} />
            </label>
            <label>
              <span>Glóbulos blancos</span>
              <input value={form.globulos_blancos} onChange={(e) => handleFieldChange('globulos_blancos', e.target.value)} />
            </label>
            <label>
              <span>Segmentados</span>
              <input
                value={unidad === 'porcentaje' ? String(Number(form.segmentados) * 100 || 0) : form.segmentados}
                onChange={(e) => handleFieldChange('segmentados', e.target.value)}
              />
            </label>
            <label>
              <span>Linfocitos</span>
              <input
                value={unidad === 'porcentaje' ? String(Number(form.linfocitos) * 100 || 0) : form.linfocitos}
                onChange={(e) => handleFieldChange('linfocitos', e.target.value)}
              />
            </label>
            <label>
              <span>Eosinófilos</span>
              <input
                value={unidad === 'porcentaje' ? String(Number(form.eosinofilos) * 100 || 0) : form.eosinofilos}
                onChange={(e) => handleFieldChange('eosinofilos', e.target.value)}
              />
            </label>
            <label>
              <span>Monocitos</span>
              <input
                value={unidad === 'porcentaje' ? String(Number(form.monocitos) * 100 || 0) : form.monocitos}
                onChange={(e) => handleFieldChange('monocitos', e.target.value)}
              />
            </label>
            <label>
              <span>Cayados</span>
              <input
                value={unidad === 'porcentaje' ? String(Number(form.cayados) * 100 || 0) : form.cayados}
                onChange={(e) => handleFieldChange('cayados', e.target.value)}
              />
            </label>
          </div>
        </div>
      </section>

      <div className="action-row">
        <button type="button" className="primary-btn" onClick={handleCalcular} disabled={loading || bloqueoLeucocitos}>
          {loading ? 'Calculando...' : 'Calcular'}
        </button>

        {canSaveDraft ? (
          <button type="button" className="secondary-btn" onClick={() => handleGuardarOrden('BORRADOR')} disabled={loading || bloqueoLeucocitos}>
            Guardar borrador
          </button>
        ) : null}

        {canApproveOfficial ? (
          <button type="button" className="success-btn" onClick={() => handleGuardarOrden('OFICIAL')} disabled={loading || bloqueoLeucocitos}>
            Aprobar y firmar oficial
          </button>
        ) : null}
      </div>

      {avisoLeucocitos ? (
        <div className="alerta-clinica">
          Diferencial total: {(diferencialTotal * 100).toFixed(1)}% · Ajuste cercano a 100%: revisión clínica recomendada, pero el valor sigue siendo válido.
        </div>
      ) : null}

      {bloqueoLeucocitos ? (
        <div className="error-box" style={{ borderColor: '#dc2626', color: '#b91c1c', background: '#fef2f2' }}>
          Diferencial total: {(diferencialTotal * 100).toFixed(1)}% · Fuera del rango clínico aceptable; no se permite guardar ni aprobar.
        </div>
      ) : null}

      {error ? <div className="error-box">{error}</div> : null}
      <AlertasClinicas advertencias={advertencias} />

      <section className="panel results-panel">
        <h3>Resultados calculados</h3>
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
