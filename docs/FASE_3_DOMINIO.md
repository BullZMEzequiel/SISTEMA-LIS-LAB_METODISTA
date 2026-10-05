# Fase 3: Dominio y casos de uso

**Fecha:** 2026-10-01

## Resultado

Se añadieron entidades puras y enums de estado en `backend/app/domain/entities.py`, errores de negocio en `domain/exceptions.py`, servicios de cálculo y ports de aplicación en `backend/app/application/ports.py`. Las implementaciones de casos de uso reciben `UnitOfWork`, `CalculationPort`, `Clock` o `PdfPort` por constructor; no importan FastAPI, React, SQLAlchemy ni PostgreSQL.

El motor `CalculationEngine` reutiliza las cuatro estrategias clínicas existentes. No contiene fórmulas nuevas: convierte entradas a `Decimal`, enruta por identificador de estrategia y transforma parámetros ausentes, valores no finitos y errores clínicos en errores de dominio/validación.

## Casos implementados

| Caso | Regla relevante |
| --- | --- |
| `CrearPaciente` | CI única, campos requeridos, fecha/sexo válidos, usuario bioquímico activo y auditoría. |
| `BuscarPaciente` | Búsqueda por CI o texto, límite acotado y usuario autorizado. |
| `ActualizarPaciente` | Lista blanca de campos, CI sin duplicados y auditoría anterior/nueva. |
| `CrearOrden` | Paciente y autor válidos; requiere estudios antes de solicitar folio; deduplica selección. |
| `AgregarEstudio` | Solo borrador con permiso; estudio activo; no duplica asignación. |
| `QuitarEstudio` | Solo borrador con permiso; no permite dejar la orden vacía ni retirar estudios con resultados. |
| `GuardarBorrador` | Persistencia mediante port, no oficializa y registra evento. |
| `CalcularEstudio` | Recalcula mediante `CalculationPort` con la configuración asignada y guarda advertencias. |
| `OficializarOrden` | Solo autor; exige resultado y campos configurados, vuelve a calcular, congela configuración/valores/referencias y registra auditoría transaccional. |
| `DelegarOrden` / `DelegarEstudio` | Solo autor sobre orden pendiente, un colaborador activo y conjunto de estudios perteneciente a la orden. |
| `AceptarDelegacion` / `FinalizarDelegacion` | Solo participantes autorizados; registran actividad y usan `Clock` cuando se inyecta. |
| `CrearCorreccion` | Solo autor de orden oficial; motivo mínimo; crea Vn+1 sin mutar valores de Vn y registra diferencias por código/id de parámetro. |
| `ConsultarVersiones` / `ConsultarCambios` | Restringen borradores por permiso; las órdenes oficiales requieren bioquímico autorizado. |
| `ConsultarHistorial` | Solo bioquímicos activos; usa port de historial oficial, no incluye borradores por contrato. |
| `MoverOrdenAPapelera` / `RestaurarOrden` | Solo autor; requiere motivo al retirar; conserva estado anterior y actor/fecha de restauración. |
| `GenerarPDF` | Solo permite render de orden oficial y delega la salida a `PdfPort`. |

Los nombres públicos están exportados desde `app.application.use_cases`.

## Flujo probado sin HTTP

`backend/tests/unit/test_application_workflow.py` usa un `UnitOfWork` y repositorios en memoria:

1. Crear, buscar y actualizar paciente.
2. Rechazar orden vacía sin consumir folio; deduplicar estudios seleccionados.
3. Guardar borrador, ejecutar estrategia, congelar V1 y oficializar.
4. Crear V2 con motivo y cambios; comprobar que V1 conserva sus entradas.
5. Reoficializar V2, consultar historial/cambios/versiones y generar PDF oficial.
6. Mover/restaurar papelera; negar PDF de orden pendiente.
7. Delegar por estudio, exigir aceptación y rechazar escritura en otro estudio.
8. Agregar/quitar estudio sin permitir una orden vacía.
9. Rechazar oficialización por no autor, corrección sin motivo, entradas ausentes/no finitas y comprobar imports libres de infraestructura.

La prueba no usa TestClient, HTTP, conexión a PostgreSQL ni SQLAlchemy dentro del dominio/aplicación.

## Decisiones y límites

- La lógica de negocio y los contratos están desacoplados, pero falta el adapter de `UnitOfWork` que convierta entre entidades de dominio y modelos SQLAlchemy. Los repositorios existentes de persistencia todavía devuelven ORM; no se conectan directamente a estos casos.
- Los catálogos tienen dos paneles y cuatro estudios semilla, pero `panel_estudios`, parámetros y rangos siguen vacíos. `StudyDefinition` lleva campos requeridos, unidades, referencias e imagen de configuración; el adapter deberá leerlos de la versión clínica correspondiente. El Excel está disponible y debe alimentar ese catálogo tras la validación de laboratorio.
- El aceptación de delegación se representa en la entidad/port y debe persistirse/auditarse por el adapter; la tabla actual no posee una columna `aceptada` explícita. El adapter debe derivarla de eventos auditados o proponerse una migración SQL en la fase adecuada, no guardarla solo en memoria.
- La generación PDF está definida como caso de uso/port, pero no existe renderer PDF. No se entrega un archivo PDF hasta implementar su adapter.
- Los casos todavía no están conectados a routers HTTP. El endpoint heredado de guardado sigue respondiendo `501` y el router antiguo de enmiendas fue retirado; el cableado HTTP debe consumir estos casos en la siguiente fase.
- La oficialización rechaza estudios sin parámetros obligatorios configurados. Esto evita publicar datos con catálogo incompleto, pero impide publicar estudios mientras no se cargue la definición del Excel.
- Las implementaciones de `UnitOfWork` deberán hacer commit/rollback atómico. Los tests usan dobles reversibles; todavía no hay prueba de integración SQLAlchemy ejecutando casos de aplicación.

## Verificación

- Suite backend: `cd backend && ./venv/bin/pytest -q` → **23 passed**, dos advertencias deprecadas de Passlib/Argon2.
- Casos públicos importables: 20.
- `Base.metadata`: 19 tablas y relaciones configuradas.
- Comprobación estática de imports: `domain/` y `application/` no importan FastAPI, SQLAlchemy, PostgreSQL ni React.
- `git diff --check`: sin errores.
- Ruff no está disponible en el entorno virtual; lint no se declara aprobado.