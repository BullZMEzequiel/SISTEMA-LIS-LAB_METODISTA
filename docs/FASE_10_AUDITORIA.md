# Fase 10: Auditoría

**Estado:** completada en backend/API. La visualización avanzada corresponde a las fases de frontend.  
**Fecha:** 2026-10-04.

## Resultado

El LIS mantiene dos bitácoras persistentes y separadas:

- `auditoria`: actividad clínica y operativa vinculable con `id_usuario`, orden, orden-estudio y versión de resultado.
- `auditoria_seguridad`: autenticación, credenciales y eventos de seguridad; no se mezcla con la actividad clínica.

Cada evento conserva actor, acción, entidad o relación clínica, identificadores aplicables y `creado_en` con zona horaria. La API entrega dichos datos mediante `GET /auditoria` y `GET /auditoria/ordenes/{id_orden}`; por tanto, dado un folio se consulta su orden y luego su bitácora para reconstruir quién actuó, qué hizo y cuándo. ADMIN puede leer la auditoría de cualquier orden; BIOQUIMICO accede según las reglas de visibilidad de la orden.

## Cobertura de actividad clínica

Los casos de uso registran, dentro de la misma unidad de trabajo que el cambio de negocio:

| Acción requerida | Evento |
| --- | --- |
| Crear/actualizar paciente | `PACIENTE_CREADO`, `PACIENTE_ACTUALIZADO` |
| Crear orden y agregar/quitar estudio | `ORDEN_CREADA`, `ESTUDIO_AGREGADO`, `ESTUDIO_QUITADO` |
| Actualizar metadatos de borrador | `ORDEN_BORRADOR_ACTUALIZADA` |
| Guardar y calcular estudio | `BORRADOR_GUARDADO`, `ESTUDIO_CALCULADO` |
| Delegar, aceptar y finalizar | `ORDEN_DELEGADA` o `ESTUDIOS_DELEGADOS`, `DELEGACION_ACEPTADA`, `DELEGACION_FINALIZADA` |
| Oficializar orden/corrección | `ORDEN_OFICIALIZADA`, `CORRECCION_OFICIALIZADA` |
| Crear una corrección/versionado | `CORRECCION_CREADA` |
| Mover/restaurar papelera | `ORDEN_A_PAPELERA`, `ORDEN_RESTAURADA` |

La corrección también guarda las diferencias campo a campo en `cambios_resultado`, incluyendo valor anterior/nuevo, motivo, actor y fecha. No existe un sistema paralelo de enmiendas.

## Seguridad

Se verificaron los eventos `LOGIN_EXITOSO`, `LOGIN_FALLIDO`, `LOGOUT`, `TOKEN_INVALIDO`, `CAMBIO_CREDENCIALES` y `USUARIO_DESACTIVADO`. La bitácora de seguridad es consultable solo por ADMIN en `GET /admin/auditoria/seguridad`.

Durante la validación se corrigieron tres problemas que impedían completar ese recorrido:

- Un host no-IP, como el usado por `TestClient`, no es válido para la columna PostgreSQL `INET`. La persistencia ahora normaliza una IP válida y registra `NULL` si el origen no puede verificarse.
- Dos handlers administrativos eliminaban la variable del actor antes de registrar `CAMBIO_CREDENCIALES` o `USUARIO_DESACTIVADO`.
- El test unitario de login no entregaba el `Request` que el endpoint necesita para obtener metadatos de seguridad.

## Verificación

```text
cd backend && venv/bin/python -m pytest -q
29 passed, 4 warnings

cd frontend && npm run build
tsc -b y vite: aprobados

git diff --check
aprobado
```

La prueba específica `test_security_audit_is_separate_and_tracks_authentication_and_admin_changes` verifica por API los seis eventos de seguridad, que todos tengan ID y fecha, su restricción a ADMIN y que la respuesta de auditoría clínica no incluya eventos de seguridad. Las pruebas de flujo de órdenes verifican la consulta por orden y los eventos de delegación; el resto de eventos clínicos se emiten en los casos de uso indicados arriba y se cubren por los recorridos de órdenes, resultados, versionado y papelera de la suite.

Advertencias no bloqueantes: deprecaciones de `crypt`, HarfBuzz, `argon2.__version__` y `HTTP_422_UNPROCESSABLE_ENTITY`.

## Inventario

- Archivos creados: `docs/FASE_10_AUDITORIA.md`, `PROBLEMAS EN FASES.md`.
- Archivos modificados: `backend/app/adapters/persistence/uow.py`, `backend/app/entrypoints/api/admin_router.py`, `backend/tests/unit/test_auth_login.py`, `docs/PENDIENTES.md`.
- Archivos eliminados: ninguno.
- Tablas modificadas: ninguna; se utilizan las tablas existentes `auditoria`, `cambios_resultado` y `auditoria_seguridad`.
- Tests ejecutados: prueba API específica de seguridad, suite backend completa y build frontend.
- Tests aprobados: 1 específica y 29 de la suite backend; build frontend aprobado.
- Pendientes: una interfaz de consulta, filtros y presentación de auditoría conforme a la arquitectura frontend de fases posteriores.
