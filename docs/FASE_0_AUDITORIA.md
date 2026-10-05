# Fase 0: Auditoría y mapa del proyecto

**Fecha de inspección:** 2026-10-01

**Alcance:** backend, frontend, PostgreSQL/Docker, pruebas, configuración y documentación disponible.

Esta fase documenta el estado observado. No se ejecutaron cambios de esquema, migraciones, borrados de datos ni operaciones destructivas. La consulta al PostgreSQL activo fue de solo lectura.

## Resumen ejecutivo

El repositorio no está alineado de extremo a extremo con el modelo relacional actual. `database/init.sql` describe el esquema objetivo de 19 tablas, pero la base PostgreSQL ya inicializada contiene 17 tablas de varias generaciones del prototipo. El ORM y los routers aún dependen de `ordenes_examen`, `resultados_modulo` y `auditoria_enmiendas`; al mismo tiempo, la base viva ya contiene tablas parciales de `ordenes`, paneles y snapshots. No hay migraciones versionadas que expliquen o conviertan esas generaciones.

El frontend sigue presentando los paneles como módulos principales y tiene solo dos páginas clínicas. No existen los flujos de selección de estudios, órdenes persistidas colaborativas, versionado, papelera ni PDF oficial. Hay discrepancias de roles y de `pieza` entre frontend y backend.

Las cuatro estrategias clínicas existentes y sus pruebas son reutilizables. La suite disponible pasa, pero no cubre el modelo de órdenes ni las reglas de colaboración y versionado.

## Mapa actual

### Backend

- `backend/main.py`: crea FastAPI e incluye routers de autenticación, pacientes, análisis y administración. La inclusión de enmiendas es opcional mediante `try/except ImportError`. CORS permite cualquier origen con credenciales.
- `backend/app/domain/calculations/`: contrato de cálculo y estrategias independientes de Hemograma, Hepatograma, Perfil lipídico y Proteinograma. Usan `Decimal` y contienen lógica clínica que debe conservarse sin cambiar fórmulas. Esta ruta refleja una migración local de paquete ya presente en el árbol de trabajo; no se considera parte del inventario original ni se repitió en esta fase.
- `backend/app/domain/models/` y `backend/app/domain/services/`: directorios presentes sin módulos Python de dominio implementados.
- `backend/app/application/`: no existe. No hay casos de uso ni DTO de aplicación.
- `backend/app/ports/`: directorio presente, sin interfaces/repositorios implementados.
- `backend/app/adapters/db/models.py`: ORM monolítico con `RolModel`, `UsuarioModel`, `PacienteModel`, `OrdenExamenModel`, `ResultadoModuloModel` y `AuditoriaEnmiendaModel`. Sus columnas y relaciones no representan las tablas objetivo.
- `backend/app/adapters/db/session.py`: sesión SQLAlchemy; usa `DATABASE_URL` con credenciales de desarrollo como fallback y `echo=True`.
- `backend/app/adapters/security/`: autenticación JWT y dependencias de usuario/rol. Es reutilizable, pero debe adaptarse al modelo de usuario y a las políticas definitivas.
- `backend/app/adapters/pdf/`: directorio vacío; no hay adapter PDF implementado.
- `backend/app/entrypoints/api/`: routers planos para auth, pacientes, análisis, administración y enmiendas; schemas Pydantic compartidos en un archivo.
- `backend/seed.py`: crea cinco roles (`ADMIN`, `BIOQUIMICO`, `INTERNO`, `MEDICO_LECTOR`, `JEFE_AREA`) y usuarios de prueba. Contradice el requisito de dos roles y debe revisarse antes de usarlo con una base limpia.

### Hallazgos de comportamiento backend

- El guardado de análisis crea paciente, orden y resultado en commits separados. No es una operación atómica y crea una orden por un único módulo; no asigna una lista de estudios a una orden.
- El endpoint de guardado recibe `id_usuario_creador` y `rol_usuario` desde el payload, en lugar de derivarlos exclusivamente del usuario autenticado.
- El router de enmiendas modifica los valores de un resultado existente y la delegación cambia el usuario creador de la orden. Ambas conductas contradicen la inmutabilidad de versiones y la autoría permanente.
- La auditoría administrativa consulta `auditoria_enmiendas`, no una bitácora general de actividad.
- El schema backend usa `pieza_cama`; la estrategia correcta del campo `pieza` no está aplicada coherentemente.
- `main.py` tiene CORS abierto; `docker-compose.yml` no define healthcheck y usa credenciales predeterminadas de desarrollo.

### Frontend

- Stack: React, TypeScript, Vite, React Router, Axios y Tailwind configurado.
- `frontend/src/App.tsx` registra login, dashboard, Hemograma, Perfil Proteico, administración de usuarios y auditoría. No hay rutas para pacientes, órdenes, estudios, historial, colaboración, papelera, cambios o perfil.
- `DashboardPage.tsx` presenta `HC-QMC-SEROL-EGO` y `HC-QMC-SERO-PROT` como módulos/tarjetas, no como paneles que agrupan estudios.
- Módulos existentes: `HemogramaPage.tsx` y `PerfilProteicoPage.tsx`. El segundo agrupa más de una lógica clínica en una sola página y calcula también resultados localmente; su acción de firma declara que falta integración.
- Servicios existentes: API Axios, auth, administración, análisis y pacientes. No hay servicios para órdenes, estudios, resultados/versiones, delegación, historial, auditoría clínica, papelera o PDF.
- `types/index.ts` define los roles `ADMIN`, `BIOQUIMICO`, `INTERNO` y `MEDICO_LECTOR`; también conserva `pieza_cama` y contratos de orden heredados.
- `AuthContext.tsx` persiste JWT y usuario en `localStorage`. Esto es estado de sesión, no hay persistencia de trabajo pendiente en frontend ni backend conforme al flujo objetivo.
- No se encontraron tests de frontend ni scripts de test en `frontend/package.json`.

### Excel fuente 2026

El archivo `1. FORMATO CENTRAL 2026.xlsx` fue localizado en la raíz del repositorio. El libro tiene 19 pestañas: 14 clínicas con contenido, cuatro vacías (`Hoja1`, `Hoja2`, `Hoja4`, `Hoja3`) y `VN` (88 celdas no vacías, sin fórmulas). Las 14 pestañas clínicas son `HC-QMC`, `HC-QMC-SEROL-EGO. `, `HC-QMC-SERO-PROT`, `QMC-ELEC`, `ELECTROLITOS`, `COAGULACION`, `ORINA`, `TEST EMBARAZO`, `COPROLOGICO `, `PANEL TOXICLOGICO`, `P.R HEPATITIS`, `SEROLOGIA`, `P.R. Ag NASAL` y `CURV TOLERANCIA`.

Se contaron 42 fórmulas: 11 en `HC-QMC`, 11 en `HC-QMC-SEROL-EGO. `, 9 en `HC-QMC-SERO-PROT`, 4 en `QMC-ELEC`, 4 en `ELECTROLITOS` y una en cada una de `ORINA`, `COPROLOGICO ` y `P.R. Ag NASAL`. Ejemplos observados: `107000*C12`, `0.32*C12`, multiplicaciones del diferencial por leucocitos, `K39-K41-K43`, `K40/5`, globulina `G42-G44` y relación albúmina/globulina `G44/G46`. Estas expresiones respaldan la conservación de las estrategias existentes; su mapeo campo por campo sigue pendiente de la fase clínica y validación del laboratorio.

### Base de datos y Docker

#### Esquema objetivo en `database/init.sql`

El archivo define 19 tablas:

`roles`, `usuarios`, `pacientes`, `paneles`, `estudios`, `panel_estudios`, `estudio_versiones`, `parametros`, `rangos_referencia`, `ordenes`, `orden_estudios`, `resultado_versiones`, `resultado_valores`, `delegaciones`, `delegacion_estudios`, `auditoria`, `cambios_resultado`, `papelera_ordenes`, `auditoria_seguridad`.

También define 44 índices explícitos, 6 triggers, 2 funciones y 2 vistas; usa `pgcrypto`. No define tipos enum. El modelo expresa paneles separados de estudios, órdenes con estudios, configuración versionada, valores de resultados normalizados, delegaciones, auditoría y papelera.

#### Base activa observada

El servicio `lis_postgres` (PostgreSQL 16) estaba activo en el puerto 5432. La consulta de solo lectura encontró 17 tablas en el esquema `laboratorio`:

`auditoria_enmiendas`, `bitacora_auditoria_clinica`, `bitacora_seguridad`, `muestras`, `orden_paneles`, `ordenes`, `ordenes_examen`, `pacientes`, `paneles`, `parametros`, `rangos_referencia`, `resultado_versiones_snapshot`, `resultados_cabecera`, `resultados_detalle`, `resultados_modulo`, `roles`, `usuarios`.

La base activa no coincide ni con el ORM completo ni con `init.sql`: mezcla tablas antiguas y de una generación intermedia, y no contiene varias tablas del SQL objetivo. `database/migrations/` está vacío. Aunque Alembic aparece en las dependencias, no se encontró `alembic.ini` ni configuración/migraciones operativas.

`docker-compose.yml` monta `database/init.sql` en el directorio de inicialización de PostgreSQL y conserva el volumen `postgres_data`. PostgreSQL solo ejecuta esa inicialización sobre un directorio de datos nuevo; editar el SQL no actualiza este volumen. No se borró ni recreó el volumen.

### Tests

- **UNIT:** siete archivos bajo `backend/tests/unit/`: cálculos de Hemograma, Hepatograma, Perfil lipídico y Proteinograma; login; administración de usuarios; validaciones de schemas/roles para enmiendas y delegación.
- Los tests de login y usuario crean/eliminan registros directamente en PostgreSQL y llaman funciones/router directamente; no son pruebas API aisladas y dependen de una base disponible.
- **INTEGRATION:** `backend/tests/integration/` existe, pero está vacío.
- **API:** no hay suite dedicada con cliente HTTP ni pruebas de contratos/autorización de órdenes.
- **FRONTEND/E2E:** no se encontraron pruebas ni configuración de Playwright/Vitest.
- Verificación disponible durante la inspección: `cd backend && ./venv/bin/pytest -q` → **16 passed**, con dos advertencias deprecadas de dependencias.

## Búsqueda global de identificadores heredados

La búsqueda se hizo sobre fuentes del backend, tests, frontend, SQL y documentación; se excluyeron dependencias, cachés y el bundle generado para distinguir las causas editables. El bundle `frontend/dist` es un artefacto compilado y deberá regenerarse cuando cambien las fuentes.

| Identificador | Ubicación activa | Clasificación inicial |
| --- | --- | --- |
| `OrdenExamen`, `ordenes_examen` | ORM, análisis y enmiendas | Migrar al agregado `Orden`/`OrdenEstudio`; retirar referencias solo al completar la migración. |
| `ResultadoModulo`, `resultado_modulo` | ORM, análisis y enmiendas (`resultados_modulo` es el nombre físico actual) | Migrar a `ResultadoVersion`/`ResultadoValor`. |
| `AuditoriaEnmienda`, `Enmienda` | ORM, administración, router y schemas; test de Fase 3 | Sustituir el versionado/enmiendas duplicado por versiones inmutables, cambios y auditoría. |
| `INTERNO` | Backend, seed, tests, tipos, páginas y opciones de rol frontend | Retirar del modelo definitivo; mantener pruebas negativas con roles permitidos, no conservar el rol. |
| `pieza_cama` | Modelo/schema/router backend y tipo/página frontend | Migrar coordinadamente a `pieza` (string). |
| `ordenes_examen`, `resultado_modulo` | ORM y routers; además tablas físicas activas con nombres de prototipo | Eliminar del esquema solo mediante la migración planificada, no por borrado aislado. |

Las notas históricas de las fases anteriores fueron movidas en el árbol de trabajo a `txt viejos/`; no son referencias de runtime y no deben borrarse automáticamente. `frontend/dist` contiene JavaScript compilado con nombres/código heredados; no debe editarse manualmente.

## Clasificación

### CONSERVAR

- Las cuatro estrategias y sus pruebas clínicas, preservando fórmulas, validaciones y resultados esperados.
- JWT, hashing de contraseñas, dependencias de autenticación y administración de usuarios, tras adaptación al esquema.
- PostgreSQL, Docker, React, TypeScript, Vite y SQLAlchemy.
- Componentes frontend reutilizables de alertas, rutas protegidas y layout cuando sigan encajando en el nuevo flujo.
- `database/init.sql` como fuente declarada del esquema objetivo, sujeto a revisión de constraints/índices durante la fase de modelos.

### MIGRAR

- ORM monolítico y sesión DB a `adapters/persistence/models`, repositorios y sesión.
- Routers y schemas planos hacia la estructura de entrypoints propuesta y casos de uso/ports.
- Pacientes y autenticación existentes a las columnas reales del SQL objetivo.
- Guardado de análisis a órdenes no vacías con varios `orden_estudios` y persistencia normalizada.
- Enmiendas/delegación/auditoría existentes al único sistema de versiones, colaboración y trazabilidad.
- Tipos, servicios, navegación y páginas frontend al modelo `Paciente`, `Orden`, `Estudio`, `Panel` y `ResultadoVersion`.
- `pieza_cama` a `pieza`; roles al conjunto `ADMIN` y `BIOQUIMICO`.

### ELIMINAR (SOLO CUANDO EL REEMPLAZO ESTÉ VALIDADO)

- Modelos/tablas y rutas antiguas `OrdenExamen`, `ResultadoModulo`, `AuditoriaEnmienda` y el sistema de enmiendas que edita versiones oficiales en sitio.
- Roles y permisos ajenos al conjunto definitivo (`INTERNO`, `MEDICO_LECTOR`, `JEFE_AREA`) de seed, UI y catálogo.
- Referencias de runtime a `pieza_cama`.
- Imports opcionales que oculten routers obligatorios una vez que los endpoints sustitutos existan.

No se recomienda borrar físicamente datos clínicos de la base activa como parte de una limpieza de código. La sustitución de tablas debe tener un plan explícito de reinicialización/migración y respaldo, aunque se confirme que los datos son solo de desarrollo.

### REVISAR

- Cambios locales pendientes en `database/init.sql`, que estaba modificado antes de esta auditoría; debe tratarse como fuente de trabajo del usuario y revisarse antes de editarlo.
- La composición exacta de ambos paneles y la correspondencia campo/celda/parámetro. El Excel ya está disponible; debe procesarse con revisión de las 14 hojas clínicas y la hoja `VN`. Los nombres o rangos no deben inferirse desde el frontend actual.
- El volumen PostgreSQL existente y el destino autorizado para reinicializarlo; la base activa presenta tablas heredadas y puede contener datos.
- `seed.py`, credenciales predeterminadas, `DATABASE_URL`, `echo=True`, CORS y healthcheck Docker.
- Reglas de auditoría y seguridad: el admin no debe poder alterar resultados oficiales silenciosamente.
- El módulo Perfil Proteico, que calcula en React y mezcla Perfil lipídico/Proteinograma; no modificar sus fórmulas hasta validar el contrato clínico.
- PDF, que aún no tiene implementación ni adapter.
- Documentación: `README.md` está vacío, `backend/.env.example` está vacío y `docs/` no tenía documentación antes de este archivo.
- Estado local de Git observado durante la auditoría: `CAMBIOS_FASE_2.txt` a `CAMBIOS_FASE_6.txt` y `NGROK_PROXIED_FIX.txt` aparecen movidos a `txt viejos/`; no se restauraron ni modificaron. También hay cambios locales en `database/init.sql` y en el paquete `domain/calculations` ya migrado.

## Riesgos y dependencias para la siguiente fase

1. No modelar SQLAlchemy contra la base viva antigua ni contra nombres inferidos: usar como contrato las 19 tablas del `init.sql` revisado.
2. Antes de cualquier recreación de la base, comprobar el destino y hacer respaldo si la información requiere conservación. El volumen actual impide asumir que el nuevo init se aplicó.
3. Construir modelos y validar sus tablas/constraints frente al SQL antes de adaptar routers; no desplegar el ORM antiguo contra el SQL nuevo.
4. Mantener el dominio independiente de FastAPI/SQLAlchemy. Tras los modelos, migrar repositorios/puertos, casos de uso, autorización, routers y tests en ese orden.
5. El libro fuente ya está localizado. La infraestructura de persistencia puede prepararse; las relaciones panel-estudio, parámetros y rangos se deben cargar en la fase clínica a partir de las celdas del Excel y validar con el laboratorio, sin inventar datos.

## Criterio de salida de Fase 0

El inventario y la clasificación quedan documentados aquí. La fase siguiente puede comenzar con la revisión aprobada del `init.sql` y la alineación del esquema/modelos; no se ha aplicado ningún cambio de DB durante esta auditoría.