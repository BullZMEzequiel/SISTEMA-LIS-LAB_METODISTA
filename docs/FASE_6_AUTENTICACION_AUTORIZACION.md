# Fase 6: Autenticación y autorización

**Estado:** completada.  
**Fecha:** 2026-10-04.

## Cambios realizados

- El backend acepta únicamente `ADMIN` y `BIOQUIMICO` para autenticación/autorización; se deniegan roles heredados y sus intentos de login quedan registrados como evento de seguridad.
- Administración de usuarios, perfiles, estado y credenciales permanece exclusiva de `ADMIN`; el backend rechaza asignar IDs de roles que no correspondan a los dos roles permitidos.
- `BIOQUIMICO` es el único rol que puede acceder a pacientes, catálogo clínico, análisis legacy y endpoints de órdenes/resultados/delegaciones/papelera/PDF.
- `ADMIN` puede consultar auditoría global y por orden, pero no puede leer/modificar pacientes, órdenes o resultados desde los endpoints clínicos ni usar endpoints de cálculo.
- La consulta/guardado/cálculo de un estudio delegado valida acceso al estudio concreto. Las respuestas de orden/listado para una delegación parcial incluyen solo los estudios autorizados.
- El frontend limita las rutas clínicas a `BIOQUIMICO`, retira roles heredados de tipos/opciones y mantiene las pantallas administrativas para `ADMIN`.
- La persistencia de delegaciones ahora traduce IDs de estudio del dominio a IDs de `orden_estudios` para respetar la FK; al leerlas recupera el código/ID de estudio de dominio.

## Pruebas ejecutadas

```text
cd backend && venv/bin/python -m pytest -q \
  tests/integration/test_api_workflow.py \
  tests/integration/test_persistence_models.py \
  tests/unit/test_fase3_enmiendas.py \
  tests/unit/test_application_workflow.py
14 passed
```

Las pruebas verifican 401 sin token, 403 entre roles, funciones administrativas, auditoría para ADMIN, autenticación BIOQUIMICO, aceptación por el colaborador asignado, lectura y escritura solo del estudio delegado, rechazo de oficialización por no autor y rechazo de edición de un resultado oficial. Se observaron cuatro advertencias deprecadas de dependencias/FastAPI; no fallaron pruebas.

Validaciones adicionales:

- Suite completa backend tras los cambios de autorización: `cd backend && venv/bin/python -m pytest -q` → **26 passed**.
- Build frontend: `cd frontend && npm run build` → `tsc -b` y Vite aprobados.
- PostgreSQL `lis_hospital`: roles `ADMIN`, `BIOQUIMICO`; usuarios con otro rol: **0**.
- `git diff --check`: aprobado.
- Búsqueda de roles heredados en código ejecutable/backend y frontend: sin resultados.

## Incidencias encontradas y corregidas

- La persistencia de delegaciones trataba IDs de estudio como IDs de `orden_estudios`, causando violaciones de FK y permisos parciales incorrectos. Se agregó conversión en escritura y lectura.
- El router resolvía la asignación a través de una consulta de orden completa, que denegaba incluso al colaborador autorizado para un estudio concreto. La consulta/cálculo/guardado ahora autorizan por el estudio explícito.
- Las consultas de orden para una delegación parcial no filtraban los estudios visibles. `ConsultarOrden` y el listado del colaborador ahora devuelven una copia acotada al conjunto delegado; se cubren GET individual, listado y GET de estudios.
- El test de login eliminaba su usuario antes de borrar el evento de auditoría de seguridad ligado por FK. Se corrigió su limpieza de fixture.

## Pendientes relacionados fuera del criterio de Fase 6

- La ruta de guardado legacy continúa contestando `501`; retirar/migrar pantallas legacy está pendiente de conectar el frontend al flujo de órdenes de Fase 5.
- Completar las discrepancias y pruebas de Fase 5 indicadas en [`FASE_5_API.md`](./FASE_5_API.md); la autorización no implica que el catálogo clínico esté completo.

## Inventario de esta implementación

- Archivos creados: `docs/FASE_6_AUTENTICACION_AUTORIZACION.md`, junto con `docs/FASE_5_API.md` y `docs/PENDIENTES.md`.
- Archivos modificados: dependencias/auth/admin/pacientes/catálogo/órdenes/análisis en la API; puertos, UOW y casos de uso; tests API/auth/autorización/aplicación; App, Dashboard, Hemograma, modal de usuario y tipos de frontend.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna; no se borraron roles ni usuarios.
