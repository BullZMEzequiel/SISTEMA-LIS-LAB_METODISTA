import { WorkflowNoticePage } from '../workflow/WorkflowNoticePage';

export function OrdenesPage() {
  return (
    <WorkflowNoticePage
      eyebrow="Órdenes"
      title="Mis órdenes"
      description="Espacio central para consultar y continuar las órdenes creadas por el usuario."
      nextPhase="las fases de interfaz de órdenes y resultados"
      action={{ label: 'Nueva orden', to: '/ordenes/nueva' }}
    />
  );
}
