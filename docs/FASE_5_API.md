# Fase 5: API FastAPI

**Estado:** incompleta frente al criterio de salida.  
**Evaluación:** 2026-10-04.

## Trabajo existente

La API ya está organizada en routers y conecta los endpoints de autenticación, pacientes, catálogo, órdenes/resultados, delegaciones, versiones, auditoría, papelera y PDF con casos de uso y el `UnitOfWork` SQLAlchemy. La integración de persistencia implementa la conversión entre entidades de dominio y los modelos. No se reescribió el proyecto.

La prueba de flujo API cubre login/logout/usuario actual, creación y consulta de paciente, catálogo, borrador, guardado de resultado, delegación completa, auditoría y respuestas seguras ante publicación/PDF sin parámetros clínicos.

## Verificación al evaluar la fase

Con PostgreSQL disponible se ejecutaron:

```text
cd backend && venv/bin/python -m pytest -q tests/integration/test_api_workflow.py
1 passed

cd backend && venv/bin/python -m pytest -q tests/integration/test_api_workflow.py tests/integration/test_persistence_models.py
3 passed
```

Estas pruebas pasan, pero no cubren todos los endpoints enumerados en el contrato.

## Observaciones para completar Fase 5

1. **Resuelto parcialmente en Fase 7:** se agregó `GET /paneles/{id}` y prueba de integración. La consulta de panel todavía no resuelve la composición clínica, porque no hay relaciones aprobadas cargadas.
2. `GET /pacientes` exige actualmente `q`; falta definir e implementar una lista sin filtro o dejar explícito en el contrato que la ruta solo busca.
3. La cobertura de integración no ejercita todos los endpoints principales ni todos sus códigos de error/autorización.
4. La API informa cuatro estudios; el requisito funcional habla de catorce. El Excel registra catorce hojas clínicas, pero los documentos de las fases previas confirman que el catálogo actualmente solo tiene cuatro estudios semilla, sin relaciones de panel, parámetros ni rangos. No deben crearse diez estudios clínicos por inferencia.
5. La prueba confirma que el panel consultado no tiene estudios asociados. La relación panel-estudio debe cargarse después de validar el mapeo clínico.
6. Los endpoints de oficialización y PDF rechazan de forma segura los catálogos incompletos; su flujo exitoso no es verificable hasta cargar y aprobar parámetros/configuración clínica.

## Dictamen

**Fase 5: incompleta.** La estructura y los flujos implementados son reutilizables y las pruebas disponibles pasan. Para declarar la fase completa hay que cerrar las diferencias de contrato, ampliar pruebas API hasta cubrir los endpoints principales y disponer del catálogo clínico validado para verificar los flujos exitosos de los catorce estudios. Los pendientes se mantienen registrados en [`PENDIENTES.md`](./PENDIENTES.md).

## Inventario de esta evaluación

- Archivos creados: `docs/FASE_5_API.md`.
- Archivos modificados: ninguno durante la evaluación inicial.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna.
- Tests ejecutados: `tests/integration/test_api_workflow.py`; además, `tests/integration/test_persistence_models.py`.
- Tests aprobados: 3 en la ejecución conjunta.
- Errores de test: ninguno con PostgreSQL levantado.
- Pendientes: los seis puntos de observación anteriores.
