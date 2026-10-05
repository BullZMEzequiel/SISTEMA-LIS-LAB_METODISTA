# Fase 1: Base de datos definitiva

**Fecha:** 2026-10-01

**Fuente de esquema:** `database/init.sql`

**Motor probado:** PostgreSQL 16, servicio Docker `lis_postgres`.

## Resultado de ejecución

El `init.sql` se ejecutó con `ON_ERROR_STOP=1` en una base vacía llamada `lis_hospital_fase1_verificada`; el script terminó sin errores. Entre fases se recreó la base de aplicación `lis_hospital`; la verificación posterior confirmó que ahora también tiene el esquema nuevo. Al revisar conexiones había dos sesiones idle de DBeaver contra `lis_hospital`; no se terminaron conexiones del usuario. No se recreó el volumen Docker durante esta validación.

Durante la prueba se detectó que `generar_folio_lis()` no resolvía la secuencia desde una sesión estándar: el `search_path` de la sesión que ejecuta el script no permanece en conexiones posteriores. Se corrigió la referencia a `laboratorio.seq_folio_lis`, se volvió a crear la base desde cero y la llamada independiente produjo `LIS-00000001`.

La base limpia aislada verificó el DDL y el folio. La consulta posterior a la recreación de `lis_hospital` encontró allí las 19 tablas requeridas, 2 vistas y 35 FK; no aparecieron `ordenes_examen`, `resultados_modulo` ni `auditoria_enmiendas`. La aplicación puede volver a usar su nombre de base habitual. No se verificó ni se afirma que los datos anteriores hayan sido migrados; la recreación sustituye el contenido del volumen/base anterior.

## Tablas finales y responsabilidades

| Tabla | Responsabilidad y claves principales |
| --- | --- |
| `roles` | Catálogo de roles; PK `id_rol`, nombre único y obligatorio. |
| `usuarios` | Usuarios, rol, CI, hash y estado; PK `id_usuario`; FK a `roles`; CI único, correo único nullable. |
| `pacientes` | Paciente independiente de órdenes; PK `id_paciente`; CI único; creador opcional ligado a usuario. |
| `paneles` | Agrupadores; PK `id_panel`, código único. |
| `estudios` | Catálogo de estudios independientes; PK `id_estudio`, código único. |
| `panel_estudios` | Relación N:M panel/estudio y orden visual; PK compuesta; panel cascada al borrar, estudio restringido. |
| `estudio_versiones` | Versiones de configuración por estudio; PK `id_estudio_version`; UNIQUE `(id_estudio, numero_version)`. |
| `parametros` | Campos/valores clínicos definidos por versión de estudio; FK a `estudio_versiones`; UNIQUE `(id_estudio_version, codigo)`. |
| `rangos_referencia` | Referencias por parámetro, sexo/edad y unidad; FK a `parametros`; checks para límites de edad y valores. |
| `ordenes` | Folio, paciente, autor inmutable, pieza y estado; FK a paciente/autor/eliminador. |
| `orden_estudios` | Estudios asignados a una orden; FK a orden/estudio/configuración; UNIQUE `(id_orden, id_estudio)`. |
| `resultado_versiones` | Borrador, resultado oficial o corrección versionada; FK a orden-estudio, versión de configuración y creador; UNIQUE `(id_orden_estudio, numero_version)`. |
| `resultado_valores` | Valores tipados, unidad y referencia congeladas por versión; FK a versión/parámetro; UNIQUE `(id_resultado_version, id_parametro)`. |
| `delegaciones` | Autor, único colaborador activo y modalidad; FK a orden y usuarios; índice UNIQUE parcial permite una delegación activa por orden. |
| `delegacion_estudios` | Estudios autorizados para delegación por estudio; PK compuesta; FK a delegación y orden-estudio. |
| `auditoria` | Trazabilidad operativa enlazada opcionalmente a usuario, orden, estudio y versión; datos anteriores/nuevos JSONB. |
| `cambios_resultado` | Diferencias de resultado con usuario, parámetro, valores y comentario obligatorio; FK a versión/usuario. |
| `papelera_ordenes` | Retiro/restauración lógica; UNIQUE por orden, autor del retiro, motivo y metadatos de restauración. |
| `auditoria_seguridad` | Eventos de autenticación/seguridad independientes de la auditoría clínica. |

## Relaciones verificadas

- `roles` 1:N `usuarios`; `usuarios` 1:N pacientes creados, órdenes propias, versiones creadas y eventos.
- `paneles` N:M `estudios` a través de `panel_estudios`.
- `estudios` 1:N `estudio_versiones`; una versión 1:N `parametros`; un parámetro 1:N `rangos_referencia`.
- `pacientes` 1:N `ordenes`; `usuarios` (autor) 1:N `ordenes`; `ordenes` 1:N `orden_estudios`.
- `estudios` 1:N `orden_estudios`; cada orden-estudio puede referenciar la versión de configuración usada.
- `orden_estudios` 1:N `resultado_versiones`; cada resultado-version referencia configuración y creador.
- `resultado_versiones` 1:N `resultado_valores`; valores enlazan al parámetro y guardan `unidad_utilizada` y `referencia_utilizada`.
- `ordenes` 1:N `delegaciones`; las delegaciones enlazan autor y colaborador; `delegacion_estudios` restringe la selección por estudio.
- `auditoria`, `cambios_resultado`, `papelera_ordenes` y `auditoria_seguridad` conservan sus respectivas relaciones con usuarios/órdenes/resultados.

PostgreSQL creó y registró las 35 FK. Se inspeccionaron sus destinos y acciones `ON DELETE`; la creación valida que las relaciones referenciadas existan. El catálogo muestra 107 columnas `NOT NULL` en las tablas base, además de las PK. El correo de usuario y varias referencias de auditoría son opcionales por diseño.

## Validación del catálogo instalado

| Objeto | Resultado |
| --- | ---: |
| Tablas requeridas | 19/19 presentes |
| Vistas | 2 |
| Índices totales PostgreSQL | 76 |
| Índices declarados explícitamente por el script | 44 |
| Primary keys | 19 |
| Foreign keys | 35 |
| UNIQUE constraints | 13 |
| CHECK constraints | 12 |
| Triggers de `actualizado_en` | 6 |
| Funciones | 2 |

Los índices incluyen PK/UNIQUE y el índice parcial `uq_delegacion_activa_por_orden`; por eso el total de catálogo es mayor que los 44 `CREATE INDEX` del archivo.

`ordenes.pieza` quedó como `VARCHAR(100)` nullable; no existe ninguna columna `pieza_cama` en la base limpia. Los timestamps de creación usan `TIMESTAMPTZ` con `NOW()` según tabla. `actualizado_en` tiene default y trigger de actualización en usuarios, pacientes, paneles, estudios, órdenes y orden-estudios.

Los checks de estado aceptan:

- Orden: `BORRADOR`, `OFICIAL`, `PAPELERA`.
- Orden-estudio: `BORRADOR`, `OFICIAL`, `ANULADO`.
- Versión de resultado: `BORRADOR`, `OFICIAL`, `SUPERADA`, `ANULADA`.
- Delegación: `TRABAJO_COMPLETO`, `POR_ESTUDIO`; autor distinto de colaborador.
- Tipos de campo/dato y sexo restringidos; rangos revisan orden de edad y límites.
- Corrección: versión distinta de V1 requiere `motivo_correccion`.

También se comprobó la unicidad de folio, CI de usuario/paciente, códigos de panel/estudio, versiones, parámetros y valores por versión, y una delegación activa por orden.

## Semillas

El script inserta exactamente los roles `ADMIN` y `BIOQUIMICO`, los paneles `HC-QMC-SEROL-EGO` y `HC-QMC-SERO-PROT`, cuatro estudios existentes (`HEMOGRAMA`, `HEPATOGRAMA`, `PERFIL_LIPIDICO`, `PROTEINOGRAMA`) y una V1 de configuración para cada uno.

No se insertan relaciones en `panel_estudios`, parámetros ni rangos de referencia. Es deliberado: el Excel con la composición de los paneles y los 14 estudios no está disponible en el workspace. No se deben completar esas relaciones/catálogos por inferencia.

## Elementos eliminados y nuevos

En la base limpia no existen `ordenes_examen`, `resultados_modulo`/`resultado_modulo` ni `auditoria_enmiendas`. Sus responsabilidades se sustituyen por `ordenes` + `orden_estudios`, `resultado_versiones` + `resultado_valores`, y `auditoria` + `cambios_resultado`. Esto no significa que las tablas antiguas hayan sido borradas de la base activa `lis_hospital`.

Elementos nuevos del modelo definitivo: `panel_estudios`, `estudio_versiones`, `rangos_referencia`, `orden_estudios`, `resultado_versiones`, `resultado_valores`, `delegaciones`, `delegacion_estudios`, `auditoria`, `cambios_resultado`, `papelera_ordenes` y `auditoria_seguridad`, más funciones/triggers y vistas de consulta.

## Decisiones y límites detectados

- `generar_folio_lis()` existe y ya funciona desde una sesión normal. `ordenes.folio` no tiene `DEFAULT` ni trigger: el caso de uso debe generar el folio dentro de la transacción de creación de la orden, una vez seleccionados estudios.
- El DDL no puede garantizar por sí solo que una orden tenga al menos un `orden_estudios`; debe imponerse en el caso de uso/transacción antes de insertar/confirmar la orden.
- El esquema no impide `UPDATE` de una versión `OFICIAL`. La inmutabilidad requiere autorización y lógica transaccional de aplicación; no declarar validada una política que la base aún no fuerza.
- `orden_estudios.id_estudio_version` es nullable y las FKs separadas no prueban que la versión corresponda al mismo estudio asignado. La aplicación debe validar esa correspondencia; se debe decidir si conviene reforzarla con FK compuesta en una revisión estructural.
- `delegacion_estudios` relaciona una delegación con un orden-estudio, pero el DDL no demuestra que ambos pertenezcan a la misma orden. Validar esa pertenencia al crear la delegación.
- `vw_ordenes_pendientes` selecciona todos los borradores y no aplica filtro de autor/delegación. No es una frontera de autorización; no exponerla sin filtro de acceso en la aplicación.
- Las 2 vistas creadas son `vw_historial_oficial` y `vw_ordenes_pendientes`.
- El SQL no define tipos enum; los estados son `VARCHAR` con `CHECK`.
- `docker-compose.yml` monta el SQL para inicialización de volumen nuevo. Un volumen ya inicializado no vuelve a ejecutar el archivo automáticamente.

## Archivos y pruebas de esta fase

- Modificado: `database/init.sql` (calificación de la secuencia del folio).
- Creado: `docs/FASE_1_DATABASE.md`.
- Corregido: `docs/FASE_0_AUDITORIA.md` (ahora registra las 2 vistas).
- Eliminados: ninguno.
- Tablas creadas inicialmente en `lis_hospital_fase1_verificada`: 19, desde una base vacía.
- Tablas verificadas después en la base activa `lis_hospital`: 19; recreación realizada entre fases, no por esta validación.
- Prueba ejecutada: `psql -v ON_ERROR_STOP=1 ... < database/init.sql`; terminó sin errores.
- Prueba de folio: llamada posterior desde conexión normal → `LIS-00000001`.
- Tests Python: no se repitieron en esta fase; no se modificó lógica Python.

## Estado de salida

**Esquema limpio creado y validado.** La consulta actual confirma el nuevo esquema en `lis_hospital` y el backend mantiene su nombre de conexión habitual. La recreación de esa base pudo descartar su contenido anterior; no se comprobó respaldo ni migración de datos clínicos.