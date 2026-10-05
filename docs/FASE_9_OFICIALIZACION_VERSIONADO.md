# Fase 9: Oficialización y versionado

**Estado:** recorrido backend/API y persistencia verificados. La revisión/comparación visual queda pendiente de las fases de interfaz.  
**Fecha:** 2026-10-04.

## Cambios y garantías verificadas

- El resultado oficial se guarda como V1 con autor, fecha/hora, fecha/hora de oficialización y snapshot de configuración/valores.
- La corrección crea V2; conserva motivo, usuario corrector y nuevos valores, sin actualizar el contenido de V1.
- La oficialización de V2 cambia V1 a `SUPERADA` como estado de vigencia, no modifica los valores ni el snapshot de V1.
- El adaptador ahora rechaza la escritura de valores/snapshot de una versión oficial/cerrada. Solo permite la transición de estado `OFICIAL` → `SUPERADA`, con el resto del contenido idéntico.
- La persistencia de valores actualiza filas existentes en vez de borrarlas y reinsertarlas; la escritura del borrador y su posterior oficialización ya no compiten con la restricción única `(id_resultado_version, id_parametro)`.
- `GET /ordenes/{id}/cambios` devuelve código del campo, orden-estudio, número de versión, antes/después, motivo, usuario y fecha/hora.
- La respuesta de versiones proporciona creador, motivo, creación/oficialización, estado y valores para consulta previa.

La prueba de recorrido usa un estudio y parámetro genéricos creados dentro de una transacción de integración, que se revierte al terminar. No agrega ni modifica catálogo clínico persistente ni define fórmulas, referencias o reglas clínicas.

## Pruebas y verificaciones

- Prueba API V1 → corrección → V2 → oficialización: verifica datos y valores de V1 en PostgreSQL, rechazo de alteración directa por el adaptador, contenido de V2 y comparación temporal de cambios.
- Suite completa: `cd backend && venv/bin/python -m pytest -q` → **28 passed**.
- Build frontend: `cd frontend && npm run build` → aprobado.
- `git diff --check` → aprobado.
- Advertencias no bloqueantes: deprecaciones de `crypt`, HarfBuzz, `argon2.__version__` y `HTTP_422_UNPROCESSABLE_ENTITY`.

## Límites pendientes

- La composición real de estudios, parámetros y referencias permanece sujeta a aprobación del laboratorio (B-001). La prueba no valida ni pretende validar esos datos.
- No hay interfaz de revisión/confirmación ni visualización comparativa. Los endpoints proveen versiones y cambios; integrar sus pantallas queda relacionado con fases de frontend.
- La visualización de nombre del usuario, en vez de su ID, es trabajo de presentación; el identificador de usuario y la marca temporal están presentes en la comparación.

## Inventario

- Archivos creados: `docs/FASE_9_OFICIALIZACION_VERSIONADO.md`.
- Archivos modificados: `backend/app/domain/entities.py`, `backend/app/adapters/persistence/uow.py`, `backend/app/entrypoints/api/contracts.py`, `backend/app/entrypoints/api/ordenes_router.py`, `backend/tests/integration/test_api_workflow.py`.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna; la prueba usa datos temporales en una transacción revertida.
- Tests ejecutados: prueba específica de versionado y suite backend completa.
- Tests aprobados: **28** en suite completa; prueba específica también aprobada.
- Errores encontrados y corregidos: escritura de resultado generaba conflicto de unicidad al sustituir filas; el adaptador ahora actualiza in-place. La escritura de datos oficiales ahora se rechaza.
- Pendientes: definiciones clínicas aprobadas e interfaz de revisión/comparación.
