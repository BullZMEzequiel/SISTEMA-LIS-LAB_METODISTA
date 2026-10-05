# Fase 8: Pendientes, colaboración y delegación

**Estado:** backend/API completada; integración completa del flujo colaborativo en la interfaz queda pendiente.  
**Fecha:** 2026-10-04.

## Capacidades y persistencia verificadas

- Las órdenes y sus resultados pendientes se persisten en PostgreSQL; el trabajo no depende únicamente de `localStorage`.
- Se soportan delegación completa y delegación de uno o más estudios.
- La aceptación requiere al colaborador asignado; antes de aceptar no obtiene acceso de trabajo.
- El acceso parcial se limita a estudios delegados en listado, lectura, cálculo y guardado.
- El autor original conserva la oficialización y corrección; un colaborador no puede oficializar la orden.
- La finalización retira el acceso de colaboración.
- La base permite una sola delegación activa por orden mediante el índice único parcial `uq_delegacion_activa_por_orden`; se rechaza la segunda delegación activa con HTTP 409.
- Los eventos de creación, aceptación y finalización se consultan en auditoría de la orden.

Los estados persistidos siguen los valores del esquema (`BORRADOR`, `OFICIAL`, `PAPELERA` y estados de resultado); `PENDIENTE` es el concepto de trabajo borrador del plan, no se introduce un estado nuevo sin migración.

## Pruebas

La suite completa ejecutada después de los cambios de Fases 7–8:

```text
cd backend && venv/bin/python -m pytest -q
27 passed
```

El test de integración API cubre persistencia del borrador, delegación completa, rechazo de una delegación activa duplicada, aceptación y finalización; el test por estudio verifica denegación previa a aceptación, visibilidad/escritura del estudio permitido, denegación de otro estudio y auditoría. Las pruebas de aplicación cubren el contrato con repositorios en memoria.

Verificaciones relacionadas:

- `cd frontend && npm run build` → compilación TypeScript/Vite aprobada.
- `git diff --check` → aprobado.
- Cuatro advertencias deprecadas de dependencias/FastAPI; ninguna prueba falló.

## Pendiente de integración de interfaz

La API expone las acciones necesarias, pero la interfaz actual aún no tiene un espacio de trabajo para listar órdenes, aceptar/finalizar delegaciones y trabajar resultados. La pantalla de creación de órdenes sí está disponible; no se construyeron campos de captura clínica genéricos porque el catálogo aprobado, tipos, unidades y parámetros de los catorce estudios todavía no están definidos. Este pendiente se enlaza con el catálogo clínico de Fases 1/4 y no se resuelve inventando controles clínicos.

**Dictamen:** criterio backend/API de Fase 8 verificado. La fase como experiencia operativa completa tiene pendiente la interfaz, a cerrar cuando el catálogo dinámico esté aprobado.

## Inventario

- Archivos creados: `docs/FASE_8_COLABORACION_DELEGACION.md`.
- Archivos modificados durante la validación de Fase 8: `backend/tests/integration/test_api_workflow.py`.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna.
- Tests ejecutados: suite completa de backend.
- Tests aprobados: 27.
- Errores encontrados: ninguno en la ejecución final.
- Pendientes: interfaz de trabajo colaborativo y captura dinámica cuando se apruebe la definición de parámetros.
