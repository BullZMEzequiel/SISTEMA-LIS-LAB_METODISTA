import { Link } from 'react-router-dom';

interface WorkflowNoticePageProps {
  eyebrow: string;
  title: string;
  description: string;
  nextPhase: string;
  action?: { label: string; to: string };
}

export function WorkflowNoticePage({
  eyebrow,
  title,
  description,
  nextPhase,
  action,
}: WorkflowNoticePageProps) {
  return (
    <section className="module-page workflow-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </header>

      <div className="panel workflow-notice">
        <h2>Espacio de trabajo preparado</h2>
        <p>
          Esta ruta ya forma parte de la navegación del laboratorio. Su interacción clínica se
          conectará de forma incremental en {nextPhase}, sin sustituir ni duplicar los flujos actuales.
        </p>
        {action ? <Link className="primary-btn small-btn" to={action.to}>{action.label}</Link> : null}
      </div>
    </section>
  );
}
