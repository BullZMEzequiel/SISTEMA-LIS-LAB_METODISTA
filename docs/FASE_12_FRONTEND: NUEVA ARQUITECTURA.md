# Fase 12 — Frontend: Nueva Arquitectura

**Estado:** ✅ Completada
**Fecha de cierre:** 2026-10-06

## Objetivo

Dejar de usar el Dashboard como selector directo de módulos clínicos. La
navegación debe girar alrededor del trabajo del laboratorio (pacientes,
órdenes, historial), no alrededor de los estudios individuales.

## Resultado

La estructura de navegación (`features/`, `modules/`, `Layout.tsx`, `App.tsx`)
ya existía en el código heredado de fases previas y se verificó en caliente
durante el cierre de esta fase. Adicionalmente, se detectaron y corrigieron
2 defectos reales que bloqueaban el CRUD de usuarios (ver sección
"Correcciones durante esta fase"), sin los cuales el criterio de salida no
se podía verificar de punta a punta.

## Recorrido verificado

- [x] Nav lateral expone: Inicio, Pacientes, Nueva orden, Mis órdenes,
      Pendientes, Colaborativas, Historial, Cambios, Papelera, Perfil
- [x] Sección ADMIN expone: Usuarios, Auditoría
- [x] Dashboard ya no enlaza directo a ningún estudio clínico (Hemograma,
      Perfil Proteico) — el texto del propio Dashboard lo confirma
- [x] Login funcional exclusivamente por CI (correo retirado como método
      de ingreso — decisión de negocio del 2026-10-05)
- [x] CRUD de usuarios operativo de punta a punta desde la interfaz de
      ADMIN: creación, edición, listado
- [x] Contraseña ingresada en texto plano por el ADMIN se transforma a
      hash Argon2 antes de persistir — verificado en DBeaver
      (`hash_password` nunca queda en texto plano)
- [x] Login de prueba exitoso con usuarios creados por la interfaz,
      cargando el dashboard correspondiente a cada rol (ADMIN / BIOQUIMICO)

## Correcciones durante esta fase

| # | Archivo | Bug | Síntoma | Fix |
|---|---|---|---|---|
| 1 | `app/entrypoints/api/schemas.py` + `admin_router.py` | `correo` exigido como obligatorio en `AdminUsuarioCreate`, contradiciendo la decisión de login solo por CI | `400 Bad Request` al crear usuario sin correo | `correo: Optional[str] = None` en `AdminUsuarioCreate` y `AdminUsuarioResponse`; validación de campos obligatorios ajustada a solo `ci` + `nombre_completo` |
| 2 | `app/adapters/persistence/repositories/usuario.py` | `get_by_identifier` aceptaba CI, correo o nombre | Login seguía aceptando correo pese a la decisión de negocio | Restringido a `UsuarioModel.ci == identifier` únicamente |
| 3 | `app/entrypoints/api/admin_router.py` → `crear_usuario` | `del usuario_actual` ejecutado antes de que esa misma variable se usara para `registrar_auditoria(...)` | `500 Internal Server Error` — `UnboundLocalError` | Se eliminó la línea `del usuario_actual` (bug preexistente, nunca antes ejercitado porque el CRUD de usuarios no se había probado de punta a punta) |

## Verificación

```bash
cd backend && venv/bin/python -m pytest -q
cd frontend && npm run build
git diff --check
```

## Pendientes para fases posteriores

- `NuevaOrdenPage` sigue fuera de `features/ordenes/` (ver Fase 13)
- Catálogo clínico de los 14 estudios (B-001) sigue sin validar con el
  laboratorio — bloquea el auto-marcado de paneles en Nueva Orden