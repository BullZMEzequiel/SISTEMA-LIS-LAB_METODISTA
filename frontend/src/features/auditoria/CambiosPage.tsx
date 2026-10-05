import { WorkflowNoticePage } from '../workflow/WorkflowNoticePage';

export function CambiosPage() {
  return (
    <WorkflowNoticePage
      eyebrow="Trazabilidad"
      title="Cambios y versiones"
      description="Revisión de correcciones, diferencias entre versiones y auditoría clínica por orden."
      nextPhase="la fase de revisión y comparación de interfaz"
    />
  );
}
