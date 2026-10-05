# Fase 2: Modelos SQLAlchemy y persistencia

**Fecha:** 2026-10-01

**Base validada:** PostgreSQL `lis_hospital`, esquema `laboratorio`.

## Resultado

SQLAlchemy ahora declara las 19 tablas del `database/init.sql` bajo `backend/app/adapters/persistence/models/`. Las clases se agrupan en identidad, catálogo, órdenes, resultados, colaboración y auditoría; `Base.metadata` registra exactamente 19 tablas, incluyendo `OrdenModel` con `pieza` (`VARCHAR(100)`) y sin `pieza_cama`.

Se añadieron `backend/app/adapters/persistence/session.py` y repositorios para pacientes, usuarios, órdenes, estudios, resultados, delegaciones y auditoría. Las rutas de autenticación, pacientes y administración usan estos repositorios para consultar entidades; no hay casos de uso implementados todavía. Ningún caso de uso contiene consultas SQLAlchemy directas porque esa capa aún no existe.

## Correspondencia validada

La prueba de integración compara el metadata con el catálogo actual y valida columnas, nullability, PK, FK, UNIQUE, CHECK e índices nombrados:

- 19 tablas y 19 PK.
- 35 FK.
- 13 constraints UNIQUE.
- 12 CHECK.
- 44 índices explícitos nombrados, incluido el UNIQUE parcial para una delegación activa por orden.
- Nombres y nullability de columnas iguales a PostgreSQL.

Una segunda prueba inserta un grafo relacionado en una transacción reversible y consulta sus entidades mediante los repositorios. Cubre usuario/rol, paciente, panel-estudio, configuración, parámetro/rango, orden-estudio, versión/valores, delegación, papelera y auditoría. La transacción se revierte y no deja datos de prueba.

## Migración de consumidores

- Auth, dependencias de seguridad, pacientes y administración usan los modelos nuevos y nombres/apellidos separados según la base.
- `seed.py` solo contempla `ADMIN` y `BIOQUIMICO` y crea usuarios con la estructura nueva.
- `main.py` importa routers explícitamente; se eliminó la importación opcional del router de enmiendas.
- Se retiraron `adapters/db/models.py`, `adapters/db/session.py` y `enmiendas_router.py`. No quedan referencias de código activo a `OrdenExamenModel`, `ResultadoModuloModel`, `AuditoriaEnmiendaModel`, ni consultas `db.query()` en `app/`.
- Las estrategias de cálculo permanecen disponibles y sin cambios de fórmula.

## Endpoints transitorios

Se conservan los endpoints de cálculo. El endpoint heredado `POST /api/analisis/guardar` responde `501` de forma explícita hasta que exista el caso de uso de órdenes/resultados normalizados y el catálogo de parámetros correspondiente. El router antiguo `/enmiendas/*` fue retirado porque editaba resultados en sitio y reasignaba la autoría. Las APIs nuevas de orden, delegación y corrección versionada corresponden a sus fases de aplicación/entrypoints; no se simula una migración clínica incompleta.

## Excel clínico

`1. FORMATO CENTRAL 2026.xlsx` está localizado. Se confirmó que contiene 14 hojas clínicas, cuatro vacías y `VN`; sus fórmulas existentes coinciden con las estrategias actuales de Hemograma, Perfil lipídico y Proteinograma en los cálculos revisados. No se importaron parámetros, relaciones de panel ni referencias en esta fase; el mapeo completo y su validación clínica siguen para la fase de catálogo/cálculos.

## Archivos y pruebas

- **Creados:** paquete de modelos, sesión, siete repositorios y `tests/integration/test_persistence_models.py`.
- **Modificados:** routers auth/pacientes/admin/análisis, dependencias de seguridad, schemas, `seed.py`, `main.py` y tests que usaban modelos antiguos.
- **Eliminados:** modelos/sesión bajo `adapters/db` y `enmiendas_router.py`.
- **Base de datos:** no se modificó el esquema ni se borraron datos durante Fase 2.
- **Prueba de integración:** `tests/integration/test_persistence_models.py` → 2 aprobadas.
- **Suite backend:** `./venv/bin/pytest -q` → 17 aprobadas, dos advertencias deprecadas de Passlib/Argon2.
- **Import/registry:** FastAPI importa 12 rutas y SQLAlchemy configura 19 tablas.
- **Referencias antiguas:** búsqueda en `backend/app` sin resultados para clases/tablas/modelo de pieza antiguos ni consultas ORM directas.
- **Lint:** Ruff no está instalado en el entorno virtual; no se reporta como aprobado.

## Pendientes

- Crear casos de uso/puertos de aplicación y mover la coordinación transaccional fuera de routers.
- Implementar el guardado de órdenes y resultados normalizados, oficialización y correcciones V2.
- Implementar APIs nuevas de colaboración, auditoría y consulta de versiones.
- Cargar parámetros, fórmulas y referencias del Excel en configuración versionada y relaciones de panel, previa validación clínica.
- Actualizar el frontend al nuevo contrato; esta fase fue limitada al backend.