import { useEffect, useMemo, useState, type FormEvent } from 'react';
import type { Paciente } from '../../types';
import { catalogoService, type Estudio, type Panel } from '../../services/catalogoService';
import { ordenesService, type OrdenCreada } from '../../services/ordenesService';

export function NuevaOrdenPage() {
  const [studies, setStudies] = useState<Estudio[]>([]);
  const [panels, setPanels] = useState<Panel[]>([]);
  const [manualStudyIds, setManualStudyIds] = useState<number[]>([]);
  const [panelStudyIds, setPanelStudyIds] = useState<number[]>([]);
  const [excludedPanelStudyIds, setExcludedPanelStudyIds] = useState<number[]>([]);
  const [selectedPanelId, setSelectedPanelId] = useState('');
  const [patient, setPatient] = useState<Paciente | null>(null);
  const [ci, setCi] = useState('');
  const [patientForm, setPatientForm] = useState({
    nombres: '',
    apellidos: '',
    fecha_nacimiento: '',
    sexo: 'F',
  });
  const [order, setOrder] = useState<OrdenCreada | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([catalogoService.listarEstudios(), catalogoService.listarPaneles()])
      .then(([catalogueStudies, cataloguePanels]) => {
        if (!active) return;
        setStudies(catalogueStudies);
        setPanels(cataloguePanels);
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el catálogo de estudios y paneles.');
      });
    return () => {
      active = false;
    };
  }, []);

  const selectedStudies = useMemo(
    () => {
      const selectedIds = new Set([
        ...manualStudyIds,
        ...panelStudyIds.filter((id) => !excludedPanelStudyIds.includes(id)),
      ]);
      return studies.filter((study) => selectedIds.has(study.id_estudio));
    },
    [studies, manualStudyIds, panelStudyIds, excludedPanelStudyIds],
  );

  const searchPatient = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setNotice(null);
    setPatient(null);
    setOrder(null);
    try {
      const matches = await ordenesService.buscarPaciente(ci.trim());
      if (matches.length) {
        setPatient(matches[0]);
        setNotice('Paciente encontrado.');
      } else {
        setNotice('No existe un paciente con esa CI. Complete los datos para registrarlo.');
      }
    } catch {
      setError('No se pudo buscar el paciente.');
    } finally {
      setLoading(false);
    }
  };

  const createPatient = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const created = await ordenesService.crearPaciente({
        ci: ci.trim(),
        ...patientForm,
      });
      setPatient(created);
      setOrder(null);
      setNotice('Paciente registrado y seleccionado.');
    } catch {
      setError('No se pudo registrar el paciente. Verifique la CI y los datos ingresados.');
    } finally {
      setLoading(false);
    }
  };

  const selectPanel = async (value: string) => {
    setSelectedPanelId(value);
    setError(null);
    setOrder(null);
    if (!value) {
      setManualStudyIds((current) => [
        ...new Set([
          ...current,
          ...panelStudyIds.filter((id) => !excludedPanelStudyIds.includes(id)),
        ]),
      ]);
      setPanelStudyIds([]);
      setExcludedPanelStudyIds([]);
      return;
    }
    setLoading(true);
    try {
      const panelStudies = await catalogoService.estudiosDePanel(Number(value));
      setPanelStudyIds(panelStudies.map((study) => study.id_estudio));
      setExcludedPanelStudyIds([]);
      if (!panelStudies.length) {
        setNotice('Este panel aún no tiene estudios asociados en el catálogo.');
      } else {
        setNotice(`Se agregaron ${panelStudies.length} estudio(s) del panel. Puede ajustar la selección.`);
      }
    } catch {
      setError('No se pudieron cargar los estudios asociados al panel.');
    } finally {
      setLoading(false);
    }
  };

  const toggleStudy = (idEstudio: number) => {
    const isSelected = selectedStudies.some((study) => study.id_estudio === idEstudio);
    if (panelStudyIds.includes(idEstudio)) {
      setExcludedPanelStudyIds((current) => isSelected
        ? [...new Set([...current, idEstudio])]
        : current.filter((id) => id !== idEstudio));
    }
    setManualStudyIds((current) => isSelected
      ? current.filter((id) => id !== idEstudio)
      : [...new Set([...current, idEstudio])]);
    setOrder(null);
  };

  const createOrder = async () => {
    if (!patient) {
      setError('Busque o registre un paciente antes de crear la orden.');
      return;
    }
    if (!selectedStudies.length) {
      setError('Seleccione al menos un estudio antes de crear la orden.');
      return;
    }
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const created = await ordenesService.crearOrden(patient.id_paciente, selectedStudies);
      setOrder(created);
      setNotice('Orden creada correctamente.');
    } catch {
      setError('No se pudo crear la orden. Confirme que el paciente y los estudios sigan activos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="module-page order-creation">
      <header className="page-header">
        <div>
          <p className="eyebrow">Laboratorio</p>
          <h1>Nueva orden</h1>
          <p>Seleccione un paciente y uno o más estudios. El folio se genera al crear la orden.</p>
        </div>
      </header>

      {error ? <div className="error-box" role="alert">{error}</div> : null}
      {notice ? <div className="order-notice" role="status">{notice}</div> : null}

      <section className="panel order-step">
        <h2>1. Paciente</h2>
        <form className="order-inline-form" onSubmit={searchPatient}>
          <label>
            <span>CI del paciente</span>
            <input
              value={ci}
              onChange={(event) => {
                setCi(event.target.value);
                setPatient(null);
                setOrder(null);
                setNotice(null);
              }}
              required
            />
          </label>
          <button className="secondary-btn" type="submit" disabled={loading}>Buscar paciente</button>
        </form>
        {patient ? (
          <p className="order-selected-patient">
            Seleccionado: <strong>{patient.nombres} {patient.apellidos}</strong> · CI {patient.ci}
          </p>
        ) : ci.trim() && notice?.includes('No existe') ? (
          <form className="order-patient-form" onSubmit={createPatient}>
            <label>
              <span>Nombres</span>
              <input
                value={patientForm.nombres}
                onChange={(event) => setPatientForm({ ...patientForm, nombres: event.target.value })}
                required
              />
            </label>
            <label>
              <span>Apellidos</span>
              <input
                value={patientForm.apellidos}
                onChange={(event) => setPatientForm({ ...patientForm, apellidos: event.target.value })}
                required
              />
            </label>
            <label>
              <span>Fecha de nacimiento</span>
              <input
                type="date"
                value={patientForm.fecha_nacimiento}
                onChange={(event) => setPatientForm({ ...patientForm, fecha_nacimiento: event.target.value })}
                required
              />
            </label>
            <label>
              <span>Sexo</span>
              <select
                value={patientForm.sexo}
                onChange={(event) => setPatientForm({ ...patientForm, sexo: event.target.value })}
              >
                <option value="F">F</option>
                <option value="M">M</option>
              </select>
            </label>
            <button className="secondary-btn" type="submit" disabled={loading}>Registrar paciente</button>
          </form>
        ) : null}
      </section>

      <section className="panel order-step">
        <h2>2. Selección de estudios</h2>
        <label className="order-panel-select">
          <span>Panel opcional</span>
          <select
            value={selectedPanelId}
            onChange={(event) => void selectPanel(event.target.value)}
            disabled={loading}
          >
            <option value="">Sin panel</option>
            {panels.map((panel) => (
              <option key={panel.id_panel} value={panel.id_panel}>{panel.nombre}</option>
            ))}
          </select>
        </label>
        <p className="order-help">El panel agrega sus estudios asociados; también puede seleccionar o quitar estudios manualmente.</p>
        <div className="order-study-list">
          {studies.map((study) => (
            <label className="order-study-option" key={study.id_estudio}>
              <input
                type="checkbox"
                checked={selectedStudies.some((selected) => selected.id_estudio === study.id_estudio)}
                onChange={() => toggleStudy(study.id_estudio)}
              />
              <span><strong>{study.nombre}</strong><small>{study.codigo}</small></span>
            </label>
          ))}
          {!studies.length ? <p>No hay estudios activos cargados en el catálogo.</p> : null}
        </div>
        <div className="order-selection-summary">
          <strong>Selección revisada: {selectedStudies.length} estudio(s)</strong>
          {selectedStudies.length ? (
            <ul>{selectedStudies.map((study) => <li key={study.id_estudio}>{study.nombre}</li>)}</ul>
          ) : <p>La orden requiere al menos un estudio.</p>}
        </div>
      </section>

      <div className="action-row">
        <button
          type="button"
          className="primary-btn"
          onClick={() => void createOrder()}
          disabled={loading || !patient || selectedStudies.length === 0 || order !== null}
        >
          {loading ? 'Procesando...' : order ? 'Orden creada' : 'Crear orden'}
        </button>
      </div>

      {order ? (
        <section className="order-created" role="status">
          <p>Orden creada</p>
          <strong>Folio: {order.folio}</strong>
          <span>{order.estudios.length} estudio(s) · estado {order.estado}</span>
        </section>
      ) : null}
    </div>
  );
}
