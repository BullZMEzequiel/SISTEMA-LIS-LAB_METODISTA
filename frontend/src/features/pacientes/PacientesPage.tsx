import { WorkflowNoticePage } from '../workflow/WorkflowNoticePage';

export function PacientesPage() {
  return (
    <WorkflowNoticePage
      eyebrow="Pacientes"
      title="Pacientes"
      description="Búsqueda, registro y actualización de pacientes del laboratorio."
      nextPhase="la Fase 13 — Frontend: Pacientes y órdenes"
      action={{ label: 'Crear nueva orden', to: '/ordenes/nueva' }}
    />
  );
}
