# Fase 7: Órdenes, paneles y estudios

**Estado:** implementación técnica disponible; cierre funcional condicionado a validar/cargar las relaciones clínicas de paneles.  
**Fecha:** 2026-10-04.

## Trabajo realizado

- Se agregó `GET /paneles/{id}` y su caso de consulta, completando la lectura individual del panel.
- Se agregó una pantalla `Nueva orden` para buscar o registrar paciente, cargar estudios/paneles, agregar estudios automáticamente desde el panel, modificar manualmente la selección, revisar el conjunto y crear la orden.
- La creación manda IDs únicos de estudio a `POST /ordenes`; el backend valida paciente y catálogo y crea folio dentro del caso `CrearOrden`. Una selección vacía se rechaza antes de generar folio.
- Se añadieron servicios HTTP para catálogo y órdenes y rutas proxy Vite para las rutas del API modular.
- La prueba de integración crea una relación panel-estudio únicamente dentro de su transacción reversible, verifica carga automática, agrega una selección manual, introduce un duplicado, y comprueba que la orden termina con estudios únicos y folio `LIS-*`.
- La interfaz deja visible cuando un panel no tiene estudios asociados; no asigna una composición clínica por inferencia.

## Validación

```text
cd backend && venv/bin/python -m pytest -q \
  tests/integration/test_api_workflow.py \
  tests/integration/test_persistence_models.py \
  tests/unit/test_application_workflow.py
11 passed

cd frontend && npm run build
tsc -b y Vite aprobados

git diff --check
aprobado
```

La base consultada sigue teniendo cuatro estudios activos y los paneles existentes no tienen asociaciones clínicas de producción. La relación temporal de la prueba se revierte y no se conserva en PostgreSQL.

## Observaciones y dictamen

La mecánica de selección manual/automática, deduplicación, validación y folio está implementada y probada. Sin embargo, los paneles requeridos `HC-QMC-SEROL-EGO` y `HC-QMC-SERO-PROT` no seleccionan estudios en la base actual porque `panel_estudios` no contiene sus relaciones. Las fuentes de Fases 0–4 prohíben inferir esa relación sin mapeo aprobado por el laboratorio.

**Fase 7: avance técnico, cierre de aceptación condicionado.** Se difiere el mapeo clínico y se continúa con Fase 8 porque la persistencia y colaboración se pueden verificar con órdenes de selección manual. La dependencia diferida y la decisión de avance están en [`ERRORES.md`](./ERRORES.md).

## Inventario

- Archivos creados: `docs/FASE_7_ORDENES_PANELES_ESTUDIOS.md`, `frontend/src/services/catalogoService.ts`, `frontend/src/services/ordenesService.ts`, `frontend/src/pages/Ordenes/NuevaOrdenPage.tsx`.
- Archivos modificados: caso de consulta de panel, router de catálogo, test de integración API, rutas frontend, Dashboard, Layout, estilos y configuración proxy Vite.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna. La fila panel-estudio temporal de la prueba se revierte con la transacción del test.
- Tests ejecutados: integración API, persistencia y flujo unitario; build frontend; `git diff --check`.
- Tests aprobados: 11 tests Python; build y diff check aprobados.
- Errores de test: ninguno. El catálogo clínico real no pudo validar selección de estudios para los paneles; se documenta como bloqueo de datos, no se simula en producción.
- Pendiente: aprobación de composición clínica y carga de `panel_estudios`/estudios validados.
