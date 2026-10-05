import { WorkflowNoticePage } from '../workflow/WorkflowNoticePage';

export function PendientesPage() {
  return (
    <WorkflowNoticePage
      eyebrow="Trabajo pendiente"
      title="Pendientes"
      description="Órdenes en borrador y estudios que requieren completar o revisar resultados."
      nextPhase="la fase de espacio de trabajo clínico"
    />
  );
}
