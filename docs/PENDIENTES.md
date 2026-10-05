# Pendientes acumulados del LIS

Registro vivo de discrepancias, errores y verificaciones pendientes detectados desde la Fase 0. Agregar las observaciones de fases futuras aquí; no eliminar entradas hasta documentar su resolución y la prueba correspondiente.

**Última actualización:** 2026-10-04.

## Fase 0 — Auditoría y mapa del proyecto

- [ ] Confirmar el historial/respaldo de datos clínicos anteriores a la recreación documentada de `lis_hospital`; Fase 1 no verificó migración de los datos previos.
- [ ] Completar la transición del frontend: el inventario de Fase 0 encontró solamente dos páginas clínicas y carecía de los flujos nuevos de órdenes, selección de estudios, colaboración, versiones, papelera e impresión oficial.
- [ ] Revisar las notas históricas bajo `txt viejos/` cuando se haga la conciliación final; no restaurar ni borrar archivos históricos como parte de correcciones no relacionadas.

## Fase 1 — Base de datos

- [ ] Resolver si los datos previos a la recreación de `lis_hospital` debían conservarse; no hay evidencia documentada de respaldo o migración.
- [ ] Completar el catálogo de estudios, relaciones de panel, parámetros y rangos de referencia a partir del Excel y aprobación del laboratorio.
- [ ] Mantener verificada la correspondencia del esquema en instalaciones existentes: el montaje de `database/init.sql` no se ejecuta de nuevo automáticamente en volúmenes Docker ya inicializados.

## Fase 2 — Persistencia

- [ ] Sincronizar la documentación histórica de Fase 2: sus pendientes de casos de uso, repositorios y rutas quedaron superados parcialmente por el código de las fases posteriores, pero no se actualizó el informe de fase.
- [ ] Verificar que cualquier base de datos desplegada usa las 19 tablas del esquema objetivo antes de ejecutar la API; la documentación histórica registra generaciones de esquema distintas.

## Fase 3 — Dominio y casos de uso

- [ ] Sincronizar el informe de Fase 3 con el código actual: el informe anota como faltantes el adapter SQLAlchemy, el cableado HTTP y el renderer PDF, pero en el repositorio actual existen `SqlAlchemyUnitOfWork`, routers cableados y renderer PDF.
- [ ] Mantener/validar en PostgreSQL la semántica de aceptación de delegación, que se deriva de auditoría y no de una columna `aceptada`.
- [ ] Agregar pruebas de integración SQLAlchemy para transacciones de los casos de uso; la mayoría de reglas de dominio se verifican con dobles en memoria.

## Fase 4 — Cálculos clínicos

- [ ] Obtener validación de laboratorio para precisión/redondeo de bilirrubina indirecta, VLDL/LDL y globulina/relación A/G.
- [ ] Validar con la bioquímica las referencias inválidas documentadas en `QMC-ELEC` y `ELECTROLITOS`; no inferir la celda correcta.
- [ ] Mapear campos, unidades, orden y rangos de referencia de las hojas clínicas restantes y `VN`.
- [ ] No modificar fórmulas ni crear estrategias nuevas sin esos datos y aprobación clínica.

## Fase 5 — API FastAPI (incompleta)

- [x] Implementar `GET /paneles/{id}` (completado durante Fase 7).
- [ ] Acordar si `GET /pacientes` debe listar sin filtro; actualmente requiere `q`.
- [ ] Ampliar pruebas API para cubrir cada endpoint principal y sus errores/autorización relevantes.
- [ ] Incorporar solo estudios/relaciones/definiciones clínicas aprobadas; el estado medido actual es cuatro estudios y paneles sin estudios asociados, frente a catorce hojas clínicas en el Excel.
- [ ] Probar oficialización y PDF exitosos después de configurar y validar parámetros clínicos; conservar el rechazo seguro mientras falte esa configuración.
- Evidencia y detalle: [`FASE_5_API.md`](./FASE_5_API.md).

## Fase 6 — Autenticación y autorización (completada)

- [x] Suite completa backend después de verificar aislamiento de estudios delegados: **26 passed**; build TypeScript/frontend: aprobado.
- [x] PostgreSQL activo contiene exactamente los roles `ADMIN` y `BIOQUIMICO`, y cero usuarios asignados a otros roles.
- [x] Verificados los endpoints de auditoría global y por orden para ADMIN; las rutas clínicas y el cálculo legacy no permiten acceso clínico a ADMIN.
- [x] Listados y lecturas de una orden con delegación parcial limitan la respuesta a los estudios asignados al colaborador.
- [ ] Migrar o retirar las pantallas/endpoints clínicos legacy; `/api/analisis/guardar` sigue respondiendo explícitamente `501` hasta que el frontend use el flujo nuevo de órdenes.
- Evidencia y estado: [`FASE_6_AUTENTICACION_AUTORIZACION.md`](./FASE_6_AUTENTICACION_AUTORIZACION.md).

## Fase 7 — Órdenes, paneles y estudios (implementación técnica; mapeo de paneles bloqueado)

- [x] Pantalla para buscar/registrar paciente, seleccionar manualmente estudios, aplicar estudios de un panel y revisar antes de crear orden.
- [x] Crear orden solo con paciente y al menos un estudio; selección sin duplicados y folio generado por la orden.
- [x] `GET /paneles/{id}` y prueba de selección automática usando una relación temporal que se revierte.
- [ ] Validar y cargar relaciones reales de los paneles `HC-QMC-SEROL-EGO` y `HC-QMC-SERO-PROT`; no inferirlas del nombre ni crear estudios por hoja sin confirmación clínica.
- [ ] Confirmar catálogo de catorce estudios, parámetros y rangos de referencia.
- Decisión de avance y bloqueo: [`ERRORES.md`](./ERRORES.md), B-001.
- Evidencia: [`FASE_7_ORDENES_PANELES_ESTUDIOS.md`](./FASE_7_ORDENES_PANELES_ESTUDIOS.md).

## Fase 8 — Pendientes, colaboración y delegación (backend/API verificada)

- [x] Persistencia de borradores en PostgreSQL; delegación completa y por estudio.
- [x] Aceptación, acceso de colaborador, edición limitada al estudio autorizado, finalización y auditoría probados por API/casos.
- [x] Verificación de una única delegación activa por orden.
- [ ] Añadir flujo/pantalla de trabajo colaborativo en frontend si se exige operación completa desde UI; los endpoints existen, pero la interfaz actual no expone aceptación/seguimiento/edición colaborativa.
- [x] Suite completa backend al cerrar la fase: **27 passed**; build frontend aprobado.
- [ ] Integrar en frontend listado de órdenes, aceptación/finalización de delegaciones y espacio de trabajo; esperar definiciones clínicas para los controles dinámicos de resultados.
- Evidencia: [`FASE_8_COLABORACION_DELEGACION.md`](./FASE_8_COLABORACION_DELEGACION.md).

## Correlación transversal frontend/API

- [ ] Migrar los consumidores legacy de `pacientesService`: usan `/api/pacientes/...`, mientras el API modular implementa `/pacientes` y `/pacientes/buscar?ci=...`. El flujo nuevo de creación de orden ya usa rutas modulares con proxy; las pantallas legacy no quedaron migradas.

## Fase 9 — Oficialización y versionado (backend/API verificada)

- [x] Recorrido PostgreSQL/API V1 → corrección → V2 → oficialización; contenido de V1 permanece igual y la V1 pasa a `SUPERADA`.
- [x] Adaptador impide reescribir datos/snapshot de una versión oficial o cerrada.
- [x] Comparación expone campo, valores anteriores/nuevos, motivo, usuario, fecha/hora y versión.
- [ ] Validar la oficialización de los estudios reales cuando el laboratorio apruebe y se cargue el catálogo (véase B-001).
- [ ] Implementar pantalla de revisión/confirmación y comparación; coordinar con fases frontend.
- Evidencia: [`FASE_9_OFICIALIZACION_VERSIONADO.md`](./FASE_9_OFICIALIZACION_VERSIONADO.md).

## Fase 10 — Auditoría (backend/API completada)

- [x] Auditoría clínica separada de la de seguridad; la consulta por orden permite reconstruir la actividad vinculada a un folio.
- [x] Registrados y verificados por API los eventos de seguridad requeridos: login exitoso/fallido, token inválido, logout, cambio de credenciales y usuario desactivado.
- [x] Corregido el registro de origen no IP y de actor administrativo durante la prueba de la fase; detalle en [`PROBLEMAS EN FASES.md`](../PROBLEMAS%20EN%20FASES.md).
- [ ] Incorporar en la arquitectura frontend posterior una vista de auditoría con filtros y presentación clínica; los endpoints de consulta ya existen.
- [ ] Sustituir la constante FastAPI obsoleta `HTTP_422_UNPROCESSABLE_ENTITY`, observada como advertencia de la suite.
- Evidencia: [`FASE_10_AUDITORIA.md`](./FASE_10_AUDITORIA.md).

## Fase 11 — Papelera y restauración (backend/API completada)

- [x] Una orden oficial pasa a `PAPELERA` sin borrado físico, con motivo, actor, fecha y estado anterior persistidos en `papelera_ordenes`.
- [x] Restauración por el autor probada por API: la orden vuelve a `OFICIAL`, se conservan los metadatos de restauración y la auditoría registra ambos eventos.
- [x] Rechazado por API el retiro de una orden oficial por un colaborador no autor.
- [ ] Integrar `GET /papelera`, retiro y restauración en la interfaz dentro de las fases frontend; los endpoints ya están disponibles.
- Evidencia: [`FASE_11_PAPELERA_RESTAURACION.md`](./FASE_11_PAPELERA_RESTAURACION.md).

## Regla de actualización

Al cerrar cada fase, registrar aquí las observaciones no resueltas, enlazar su informe de fase y marcar una entrada resuelta únicamente cuando exista verificación reproducible. No completar datos clínicos por conjetura ni introducir cambios de esquema destructivos como “limpieza”.
