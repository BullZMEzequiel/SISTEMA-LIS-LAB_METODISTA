# Fase 11: Papelera y restauración

**Estado:** completada en backend/API. La pantalla de papelera corresponde a fases posteriores de frontend.  
**Fecha:** 2026-10-04.

## Resultado

Las órdenes oficiales no se eliminan físicamente. El retiro usa una transición de estado `OFICIAL` → `PAPELERA` y conserva tanto la fila de `ordenes` como su relación con paciente, estudios, resultados y versiones.

Al retirar una orden, el caso de uso exige que el solicitante sea el autor original, que la orden esté oficializada y que se entregue un motivo. Se registran:

- en `ordenes`: estado `PAPELERA`, `eliminado_por`, `eliminado_en` y `motivo_papelera`;
- en `papelera_ordenes`: orden, autor del retiro, estado anterior, motivo y fecha;
- en `auditoria`: evento `ORDEN_A_PAPELERA`, actor, orden, motivo y transición de estado.

La restauración solo puede ser ejecutada por el autor original y exige estado `PAPELERA`. Restituye el estado anterior (en el flujo validado, `OFICIAL`), no borra la fila histórica de `papelera_ordenes` y registra `restaurado`, `restaurado_por`, `restaurado_en` y el evento `ORDEN_RESTAURADA`.

## API y permisos

| Operación | Ruta | Permiso |
| --- | --- | --- |
| Retirar orden oficial | `POST /ordenes/{id_orden}/papelera` | BIOQUIMICO autor, motivo obligatorio |
| Consultar papelera | `GET /papelera` | BIOQUIMICO; solo sus órdenes retiradas |
| Restaurar orden | `POST /papelera/{id_orden}/restaurar` | BIOQUIMICO autor |

No hay ruta ni caso de uso para `DELETE` de una orden. Los `DELETE` existentes se limitan a la composición de una orden en borrador y no permiten retirar una orden oficial.

## Recorrido verificado

La prueba de integración API crea una configuración clínica temporal dentro de una transacción revertida, publica una orden y verifica:

```text
OFICIAL
  → POST /ordenes/{id}/papelera
PAPELERA
  → POST /papelera/{id}/restaurar
OFICIAL
```

La prueba confirma que:

- un colaborador recibe `403` al intentar retirar una orden ajena;
- la orden persiste tras el retiro, queda en `PAPELERA` y conserva su ID;
- `papelera_ordenes` contiene autor, motivo, estado anterior `OFICIAL` y fecha;
- la lista de papelera muestra la orden retirada y queda vacía tras restaurarla;
- al restaurar, la orden vuelve a `OFICIAL` y la fila de papelera queda marcada como restaurada con actor y fecha;
- `ORDEN_A_PAPELERA` y `ORDEN_RESTAURADA` existen en la auditoría de la orden.

No se insertaron datos clínicos permanentes ni se modificó el catálogo: la transacción de prueba se revierte al finalizar.

## Verificación

```text
cd backend && venv/bin/python -m pytest -q \
  tests/integration/test_api_workflow.py::test_api_official_result_correction_preserves_v1_and_records_comparison
1 passed

cd backend && venv/bin/python -m pytest -q
29 passed, 4 warnings

cd frontend && npm run build
tsc -b y vite: aprobados

git diff --check
aprobado
```

Advertencias no bloqueantes: deprecaciones de `crypt`, HarfBuzz, `argon2.__version__` y `HTTP_422_UNPROCESSABLE_ENTITY`.

## Inventario

- Archivos creados: `docs/FASE_11_PAPELERA_RESTAURACION.md`.
- Archivos modificados: `backend/tests/integration/test_api_workflow.py`, `docs/PENDIENTES.md`.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna; la prueba usa `ordenes`, `papelera_ordenes` y `auditoria` en una transacción revertida.
- Tests ejecutados: recorrido API específico de papelera, suite backend completa y build frontend.
- Tests aprobados: 1 específico y 29 de la suite backend; build frontend aprobado.
- Pendientes: exponer la papelera en la interfaz y sustituir la constante FastAPI obsoleta reportada por la suite.
