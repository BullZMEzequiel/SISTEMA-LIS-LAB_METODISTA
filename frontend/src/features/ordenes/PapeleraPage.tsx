import { WorkflowNoticePage } from '../workflow/WorkflowNoticePage';

export function PapeleraPage() {
  return (
    <WorkflowNoticePage
      eyebrow="Papelera"
      title="Órdenes retiradas"
      description="Consulta y restauración controlada de órdenes retiradas sin borrado físico."
      nextPhase="la integración de papelera en frontend"
    />
  );
}
