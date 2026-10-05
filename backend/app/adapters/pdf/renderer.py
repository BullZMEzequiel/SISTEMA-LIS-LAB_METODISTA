from html import escape
from typing import Sequence

from weasyprint import HTML

from app.domain.entities import Order, ResultVersion


class OfficialPdfRenderer:
    def render_official(self, order: Order, results: Sequence[ResultVersion]) -> bytes:
        patient = order.paciente
        patient_name = ""
        patient_ci = ""
        if patient:
            patient_name = " ".join(
                value
                for value in (patient.nombres, patient.apellido_paterno, patient.apellido_materno)
                if value
            )
            patient_ci = patient.ci

        sections = []
        for result in results:
            rows = []
            values = {**result.entradas, **result.calculados}
            snapshot = result.snapshot_completo
            units = snapshot.get("unidades", {})
            references = snapshot.get("referencias", {})
            for code, value in values.items():
                unit = units.get(code, "") if isinstance(units, dict) else ""
                reference = references.get(code, "") if isinstance(references, dict) else ""
                rows.append(
                    "<tr>"
                    f"<td>{escape(str(code))}</td>"
                    f"<td>{escape(str(value))}</td>"
                    f"<td>{escape(str(unit))}</td>"
                    f"<td>{escape(str(reference))}</td>"
                    "</tr>"
                )
            name = escape(str(snapshot.get("nombre_estudio", "Estudio")))
            sections.append(
                f"<section><h2>{name}</h2><table>"
                "<thead><tr><th>Parámetro</th><th>Resultado</th><th>Unidad</th><th>Referencia</th></tr></thead>"
                f"<tbody>{''.join(rows)}</tbody></table>"
                f"<p>{escape(result.comentario_estudio or '')}</p></section>"
            )

        document = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm; }}
body {{ font-family: sans-serif; color: #17212b; font-size: 10pt; }}
h1 {{ font-size: 18pt; margin-bottom: 4px; }} h2 {{ font-size: 13pt; border-bottom: 1px solid #b8c2cc; padding-bottom: 5px; }}
.meta {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px 20px; margin: 18px 0 24px; }}
table {{ border-collapse: collapse; width: 100%; }} th,td {{ border-bottom: 1px solid #d8dee4; padding: 6px; text-align: left; }}
th {{ background: #f2f5f7; }} section {{ break-inside: avoid; margin-bottom: 22px; }}
</style></head><body>
<h1>Informe de laboratorio</h1>
<div class="meta"><span>Folio: {escape(order.folio)}</span><span>Estado: OFICIAL</span>
<span>Paciente: {escape(patient_name)}</span><span>CI: {escape(patient_ci)}</span>
<span>Pieza: {escape(order.pieza or '')}</span><span>Fecha: {escape(order.oficializado_en.isoformat() if order.oficializado_en else '')}</span></div>
{''.join(sections)}
</body></html>"""
        return HTML(string=document).write_pdf()