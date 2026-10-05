import { WorkflowNoticePage } from '../workflow/WorkflowNoticePage';

export function DelegacionesPage() {
  return (
    <WorkflowNoticePage
      eyebrow="Colaboración"
      title="Órdenes colaborativas"
      description="Aceptación, seguimiento y finalización de trabajo delegado por orden o estudio."
      nextPhase="la fase de colaboración de interfaz"
    />
  );
}
