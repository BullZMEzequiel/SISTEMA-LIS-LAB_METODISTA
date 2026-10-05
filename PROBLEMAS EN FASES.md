# Problemas en fases

Registro de dificultades que interrumpen o retrasan una fase, con su tratamiento y estado. No sustituye los pendientes funcionales de `docs/PENDIENTES.md`.

## P-001 — Fase 10: persistencia de auditoría de seguridad con origen no IP

- **Fecha:** 2026-10-04.
- **Proceso:** prueba de integración de autenticación y auditoría de seguridad.
- **Problema:** `TestClient` presenta el host `testclient`; PostgreSQL rechazaba ese texto al insertarlo en las columnas `INET` de `auditoria_seguridad`.
- **Impacto:** el login de la prueba fallaba antes de completar el recorrido de auditoría.
- **Cómo se abordó:** se validó y normalizó `ip_origen` en el adaptador de persistencia y en el helper administrativo. Si el origen no es una IP válida, se conserva como `NULL`, sin inventar una dirección. También se corrigieron handlers que descartaban el actor antes de registrar cambios de credenciales o desactivación.
- **Resultado:** la prueba específica de seguridad pasa y la suite backend termina con **29 passed**.
- **Estado:** resuelto.
