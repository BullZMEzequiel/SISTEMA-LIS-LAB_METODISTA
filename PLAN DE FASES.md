PLAN DE EJECUCIÓN POR FASES
Reestructuración del LIS — Laboratorio Metodista
REGLA GENERAL PARA TODAS LAS FASES

Trabaja sobre el repositorio existente.

NO reescribas todo desde cero.

En cada fase:

Inspecciona antes de modificar.
Conserva lo que funciona.
Elimina únicamente lo que haya sido reemplazado.
No inventes reglas clínicas.
No cambies fórmulas sin justificación.
No introduzcas otro framework o tecnología principal.
Ejecuta pruebas al finalizar.
Reporta exactamente:
archivos creados;
archivos modificados;
archivos eliminados;
tablas modificadas;
tests ejecutados;
tests aprobados;
errores encontrados;
pendientes.
REGLA DE BLOQUEO

Si una fase falla, DETENTE.

No continúes construyendo encima del error.

FASE 0 — AUDITORÍA Y MAPEO DEL PROYECTO
Objetivo

Comprender exactamente qué existe antes de tocar código.

NO modificar código todavía.

Inspeccionar:

backend/
frontend/
database/
tests/
docker/
configuración
README

Identificar:

Backend
modelos SQLAlchemy;
routers;
schemas;
servicios;
casos de uso;
repositorios;
estrategias de cálculo;
autenticación;
autorización;
auditoría;
versionado;
PDF.
Frontend
páginas;
componentes;
módulos clínicos;
servicios HTTP;
contextos;
hooks;
tipos TypeScript;
rutas;
autenticación;
Dashboard.
Base de datos
tablas;
FK;
índices;
constraints;
triggers;
enums;
relaciones.
Tests

Clasificar:

UNIT
INTEGRATION
API
FRONTEND
E2E
Buscar globalmente
OrdenExamen
ResultadoModulo
AuditoriaEnmienda
Enmienda
INTERNO
pieza_cama
ordenes_examen
resultado_modulo
Clasificar cada elemento

Crear cuatro listas:

CONSERVAR
MIGRAR
ELIMINAR
REVISAR
Entregable

Crear:

docs/FASE_0_AUDITORIA.md

Debe contener el mapa real del proyecto.

Criterio de salida

No modificar arquitectura todavía.

La fase termina cuando existe un inventario suficientemente preciso para ejecutar la migración.

FASE 1 — BASE DE DATOS DEFINITIVA
Objetivo

Convertir PostgreSQL en la base estructural definitiva del LIS.

Usar:

database/init.sql

como fuente de verdad.

Modelo conceptual

Debe existir:

roles
usuarios
pacientes

paneles
panel_estudios

estudios
estudio_versiones
parametros
rangos_referencia

ordenes
orden_estudios

resultado_versiones
resultado_valores

delegaciones
delegacion_estudios

auditoria
cambios_resultado

papelera_ordenes
auditoria_seguridad
Eliminar del modelo anterior

Si todavía existen:

ordenes_examen
resultado_modulo
auditoria_enmiendas

deben desaparecer del modelo definitivo.

Corregir

Reemplazar:

pieza_cama

por:

pieza

tipo:

string
Validar

Comprobar:

PK;
FK;
UNIQUE;
NOT NULL;
índices;
CHECK;
relaciones;
timestamps;
estados;
versionado.
Prueba

Crear una BD limpia.

Ejecutar init.sql.

Debe terminar sin errores.

Entregable
docs/FASE_1_DATABASE.md

Debe contener:

tablas finales;
relaciones;
decisiones;
elementos eliminados;
elementos nuevos.
Criterio de salida

La BD limpia debe crearse correctamente.

FASE 2 — MODELOS SQLALCHEMY Y PERSISTENCIA
Objetivo

Hacer que SQLAlchemy represente exactamente la nueva BD.

Crear/adaptar:

RolModel
UsuarioModel
PacienteModel

PanelModel
PanelEstudioModel

EstudioModel
EstudioVersionModel
ParametroModel
RangoReferenciaModel

OrdenModel
OrdenEstudioModel

ResultadoVersionModel
ResultadoValorModel

DelegacionModel
DelegacionEstudioModel

AuditoriaModel
CambioResultadoModel
PapeleraOrdenModel
AuditoriaSeguridadModel

Los nombres pueden adaptarse a la convención del proyecto.

Eliminar dependencias antiguas

No debe quedar código funcional dependiendo de:

OrdenExamenModel
ResultadoModuloModel
AuditoriaEnmiendaModel

si ya fueron reemplazados.

Crear repositorios

Separar:

PacienteRepository
UsuarioRepository
OrdenRepository
EstudioRepository
ResultadoRepository
DelegacionRepository
AuditoriaRepository
Regla

Los casos de uso no deben hacer consultas SQLAlchemy directamente.

Criterio de salida
Backend importa todos los modelos.
SQLAlchemy puede crear/consultar las entidades.
Relaciones funcionan.
No existen referencias rotas a modelos antiguos.
Tests de persistencia pasan.
FASE 3 — DOMINIO Y CASOS DE USO
Objetivo

Construir el núcleo real del LIS.º

Crear casos de uso:

CrearPaciente
BuscarPaciente
ActualizarPaciente

CrearOrden
AgregarEstudio
QuitarEstudio

GuardarBorrador
CalcularEstudio
OficializarOrden

DelegarOrden
DelegarEstudio
AceptarDelegacion
FinalizarDelegacion

CrearCorreccion
ConsultarVersiones
ConsultarCambios

ConsultarHistorial

MoverOrdenAPapelera
RestaurarOrden

GenerarPDF
Regla

Los casos de uso NO deben depender de:

FastAPI
React
SQLAlchemy
PostgreSQL

Deben depender de interfaces/ports.

Criterio de salida

Debe poder probarse el flujo principal sin utilizar HTTP:

Paciente
→ Orden
→ Estudios
→ Resultado
→ Borrador
→ Oficialización
FASE 4 — MIGRACIÓN DE LOS CÁLCULOS CLÍNICOS
Objetivo

Conservar la lógica clínica que ya funciona y adaptarla al nuevo modelo.FASE 3 — DOMINIO Y CASOS DE USO

Objetivo

Construir el núcleo real del LIS.FASE 3 — DOMINIO Y CASOS DE USO

Objetivo

Construir el núcleo real del LIS.

Revisar especialmente:

Hemograma
Hepatograma
Perfil lipídico
Proteinograma

y los demás estudios existentes.

Regla fundamental

NO modificar una fórmula simplemente porque parezca mejor.

Comparar:

Excel
+
código actual
+
tests actuales

Si existe discrepancia:

DOCUMENTAR

y no inventar una solución.

Cada estrategia debe recibir datos y devolver resultados.

No debe hacer directamente:

db.query(...)
Resultado

Cada estudio debe poder ejecutar:

entrada
→ validación
→ cálculo
→ resultado
→ advertencias
Tests

Conservar/adaptar:

test_hemograma
test_hepatograma
test_perfil_lipidico
test_proteinograma
Criterio de salida

Todos los cálculos existentes funcionan y sus tests pasan.

FASE 5 — API FASTAPI
Objetivo

Reconstruir la API alrededor del nuevo dominio.

Auth
POST /auth/login
POST /auth/logout
GET /auth/me
Pacientes
POST /pacientes
GET /pacientes
GET /pacientes/{id}
GET /pacientes/buscar
PUT /pacientes/{id}
Estudios
GET /estudios
GET /estudios/{id}
GET /paneles
GET /paneles/{id}/estudios
Órdenes
POST /ordenes
GET /ordenes
GET /ordenes/{id}
PUT /ordenes/{id}/borrador
POST /ordenes/{id}/oficializar
Resultados
GET /ordenes/{id}/estudios
GET /ordenes/{id}/estudios/{id_estudio}
POST /ordenes/{id}/estudios/{id_estudio}/calcular
PUT /ordenes/{id}/estudios/{id_estudio}/resultado
Delegación
POST /ordenes/{id}/delegaciones
POST /delegaciones/{id}/aceptar
POST /delegaciones/{id}/finalizar
Versionado
GET /ordenes/{id}/versiones
GET /ordenes/{id}/cambios
POST /ordenes/{id}/correcciones
Auditoría
GET /auditoria
GET /auditoria/ordenes/{id}
Papelera
POST /ordenes/{id}/papelera
GET /papelera
POST /papelera/{id}/restaurar
PDF
GET /ordenes/{id}/pdf
Regla

Los routers deben ser delgados.

HTTP
 ↓
Caso de uso
 ↓
Dominio
 ↓
Repository
Criterio de salida

Todos los endpoints principales funcionan mediante pruebas API. la logica correcta para el sistema LIS que comprende de 14 estudio o analisis, # REGLA GENERAL PARA TODAS LAS FASES

Trabaja sobre el repositorio existente.

NO reescribas todo desde cero. la logica correcta para el sistema LIS que comprende de 14 estudio o analisis, # REGLA GENERAL PARA TODAS LAS FASES

Trabaja sobre el repositorio existente.

NO reescribas todo desde cero.

FASE 6 — AUTENTICACIÓN Y AUTORIZACIÓN
Objetivo

Garantizar que el sistema no dependa de ocultar botones del frontend.

Roles definitivos:

ADMIN
BIOQUIMICO

Eliminar completamente:

INTERNO
Reglas
BIOQUIMICO

Puede:

crear paciente;
crear orden;
agregar estudios;
calcular;
guardar pendiente;
delegar;
aceptar delegación;
trabajar;
consultar historial;
oficializar sus órdenes;
corregir sus órdenes oficiales.
ADMIN

Puede:

gestionar usuarios;
gestionar perfiles;
activar/desactivar;
gestionar credenciales;
consultar auditoría.
Regla crítica

ADMIN no debe modificar silenciosamente resultados clínicos oficiales.

Criterio de salida

Crear tests para:

401
403
roles
autor
colaborador
estudio delegado
orden oficial
FASE 7 — ORDEN, PANELES Y ESTUDIOS
Objetivo

Implementar correctamente el flujo central del laboratorio.

Flujo
Paciente
 ↓
Seleccionar estudios
 ↓
Seleccionar panel opcional
 ↓
Panel selecciona estudios automáticamente
 ↓
Revisar selección
 ↓
Crear orden
 ↓
Generar folio
Importante

No crear folio solamente al crear paciente.

Debe existir:

Paciente
+
al menos un estudio
=
Orden
+
Folio
Paneles

Implementar:

HC-QMC-SEROL-EGO
HC-QMC-SERO-PROT

como agrupadores.

No como estudios clínicos.

Criterio de salida

Probar:

selección de panel
selección automática
selección manual
evitar duplicados
creación de orden
generación de folio
FASE 8 — PENDIENTES, COLABORACIÓN Y DELEGACIÓN
Objetivo

Implementar el trabajo colaborativo.

Estados conceptuales
PENDIENTE
OFICIAL
EN_CORRECCION
PAPELERA

Los nombres exactos pueden ajustarse al esquema.

Pendiente

Debe estar en PostgreSQL.

NO utilizar únicamente:

localStorage
Delegación completa
A
 ↓
B

B puede trabajar toda la orden.

Delegación por estudio
Hemograma → A
Hepatograma → A
Proteinograma → B

B solo puede trabajar Proteinograma.

Regla

Máximo:

1 autor
+
1 colaborador
Criterio de salida

Probar:

delegación;
aceptación;
acceso;
edición;
permisos;
finalización;
auditoría.
FASE 9 — OFICIALIZACIÓN Y VERSIONADO
Objetivo

Construir la parte más importante de trazabilidad clínica.

Flujo
Borrador
 ↓
Calcular
 ↓
Revisar
 ↓
Vista previa
 ↓
Confirmar
 ↓
OFICIAL
Una vez oficial

La versión es:

INMUTABLE
Corrección

Nunca:

UPDATE V1

Siempre:

V1
 ↓
V2
V2 debe guardar:
autor original
usuario que corrigió
fecha
hora
motivo
valores anteriores
valores nuevos
Comparación

Debe poder visualizarse:

CAMPO
ANTES
DESPUÉS
USUARIO
FECHA
MOTIVO
Criterio de salida

Crear pruebas:

V1 oficial
→ corrección
→ V2

V1 permanece intacta
V2 contiene cambios
auditoría existe
motivo existe
autor original permanece
FASE 10 — AUDITORÍA
Objetivo

Registrar todas las acciones importantes.

Registrar:

crear paciente
crear orden
agregar estudio
guardar borrador
calcular
delegar
aceptar delegación
modificar
oficializar
corregir
crear versión
mover a papelera
restaurar

Cada evento debe poder identificar:

usuario
acción
entidad
entidad_id
fecha
hora
Seguridad

Separar eventos de:

actividad clínica

y:

seguridad

Seguridad:

LOGIN_EXITOSO
LOGIN_FALLIDO
LOGOUT
TOKEN_INVALIDO
CAMBIO_CREDENCIALES
USUARIO_DESACTIVADO
Criterio de salida

Dado un folio, debe ser posible reconstruir quién hizo qué y cuándo.

FASE 11 — PAPELERA Y RESTAURACIÓN
Objetivo

Evitar borrado destructivo de información clínica.

No usar:

DELETE

para eliminar definitivamente una orden oficial.

Utilizar:

papelera_ordenes

Registrar:

eliminado_por
fecha
hora
motivo
estado_anterior

Restauración:

restaurado_por
restaurado_en
Criterio de salida

Probar:

OFICIAL
 ↓
PAPELERA
 ↓
RESTAURAR

y verificar auditoría completa.

FASE 12 — FRONTEND: NUEVA ARQUITECTURA
Objetivo

Dejar de utilizar el Dashboard como simple selector de módulos clínicos.

La navegación debe girar alrededor del trabajo del laboratorio.

Crear:

Inicio
Pacientes
Nueva orden
Historial
Mis órdenes
Pendientes
Órdenes colaborativas
Cambios
Papelera
Perfil

ADMIN:

Usuarios
Auditoría
Estructura conceptual
features/
    auth/
    pacientes/
    ordenes/
    historial/
    delegaciones/
    auditoria/
    usuarios/

modules/
    hemograma/
    hepatograma/
    perfil-lipidico/
    proteinograma/
    ...
Criterio de salida

El usuario puede navegar el sistema sin entrar directamente a un estudio desde el Dashboard.

FASE 13 — FRONTEND: PACIENTES Y ÓRDENES
Objetivo

Implementar el flujo completo de creación.

Pantalla
Nueva orden
Paso 1

Buscar paciente:

CI
Nombre
Paso 2

Si no existe:

Crear paciente
Paso 3

Seleccionar estudios/paneles.

Paso 4

Confirmar.

Paso 5

Crear orden.

Paso 6

Mostrar:

Folio
Paciente
Autor
Estado
Estudios
Criterio de salida

Un bioquímico puede crear una orden completa desde el frontend.

FASE 14 — FRONTEND: MÓDULOS CLÍNICOS
Objetivo

Convertir los formularios del Excel en módulos web.

Cada estudio debe tener:

Formulario
Validación
Cálculo
Resultado
Advertencias
Vista previa

No crear un formulario gigante.

Utilizar componentes compartidos para:

Input
Select
Campo numérico
Tabla
Resultado
Sección
Botones

pero mantener la lógica clínica separada.

Criterio de salida

Cada módulo existente puede:

abrir
ingresar datos
calcular
guardar
mostrar resultado
FASE 15 — FRONTEND: PENDIENTES Y COLABORACIÓN
Objetivo

Permitir continuar trabajos entre bioquímicos.

Mostrar:

Mis pendientes
Órdenes colaborativas

Cada orden debe indicar:

Autor
Colaborador
Estado
Estudios pendientes
Última modificación
Acciones

Según permisos:

Continuar
Guardar
Calcular
Delegar
Finalizar
Criterio de salida

Simular:

Usuario A crea orden
Usuario A guarda
Usuario A delega a B
Usuario B inicia sesión
Usuario B ve el trabajo
Usuario B continúa
Usuario A ve cambios
FASE 16 — FRONTEND: HISTORIAL Y BÚSQUEDA
Objetivo

Crear el historial oficial.

Filtros:

CI
Nombre
Folio
Fecha inicial
Fecha final
Estudio
Usuario
Estado

Debe poder buscarse:

todos los Hemogramas

o:

todos los análisis de Juan Pérez

o:

todos los análisis realizados por Carlos durante septiembre
Importante

El historial oficial NO debe mezclar borradores.

Criterio de salida

Las búsquedas y filtros funcionan desde backend, no solamente filtrando grandes cantidades de datos en React.

FASE 17 — FRONTEND: VERSIONES Y CAMBIOS
Objetivo

Crear visualización clara del historial de modificaciones.

Ejemplo:

Folio LIS-000123

Versión 1
Oficial
30/09/2026
Carlos

Versión 2
Corrección
01/10/2026
Carlos

Botón:

Ver cambios

Mostrar:

Campo
Antes
Después
Motivo
Usuario
Fecha
Criterio de salida

Un usuario autorizado puede reconstruir qué cambió entre V1 y V2.

FASE 18 — PDF OFICIAL
Objetivo

Generar el informe final del laboratorio.

El PDF debe incluir:

Laboratorio
Paciente
CI
Fecha
Folio
Estudio
Resultados
Unidades
Referencias
Observaciones

Según corresponda.

NO incluir
auditoría interna
delegaciones
valores anteriores
motivos internos
información de seguridad
Regla

El PDF oficial debe generarse a partir de una versión oficial concreta.

Criterio de salida

Generar PDF de una orden oficial y verificar que coincide con la versión almacenada.

FASE 19 — ADMINISTRACIÓN Y PERFIL
Perfil

Permitir:

nombre
apellido
foto
credenciales

según las reglas definidas.

Administración

ADMIN puede:

crear usuario
editar usuario
activar
desactivar
gestionar credenciales

Mostrar:

BIOQUIMICO
ADMIN

No:

INTERNO
Criterio de salida

Crear/desactivar usuarios y comprobar que un usuario desactivado no puede iniciar sesión.

FASE 20 — LIMPIEZA FINAL

Realizar búsqueda global de:

OrdenExamen
ResultadoModulo
AuditoriaEnmienda
Enmienda
INTERNO
pieza_cama
ordenes_examen
resultado_modulo

Cada aparición debe:

eliminarse
migrarse
o justificarse explícitamente

Eliminar:

imports muertos;
routers antiguos;
schemas antiguos;
tipos TypeScript antiguos;
componentes sin uso;
endpoints duplicados;
servicios duplicados.
Criterio de salida

No existen restos funcionales de la arquitectura anterior.

FASE 21 — PRUEBAS INTEGRALES

Ejecutar:

backend unit tests
backend integration tests
API tests
frontend build
TypeScript compiler
Flujo E2E mínimo

Simular:

1. Login
2. Crear paciente
3. Crear orden
4. Seleccionar panel
5. Generar estudios
6. Abrir estudio
7. Introducir datos
8. Calcular
9. Guardar pendiente
10. Delegar
11. Otro usuario acepta
12. Otro usuario modifica
13. Autor revisa
14. Oficializa
15. Generar PDF
16. Buscar en historial
17. Crear corrección
18. Generar V2
19. Ver cambios
20. Mover a papelera
21. Restaurar
FASE 22 — SEGURIDAD FINAL

Probar explícitamente:

B edita orden oficial de A
→ DENEGADO

B elimina orden oficial de A
→ DENEGADO

B modifica estudio no delegado
→ DENEGADO

Usuario no autorizado abre pendiente ajeno
→ DENEGADO

Usuario desactivado intenta login
→ DENEGADO

V1 intenta modificarse
→ DENEGADO

PDF de pendiente
→ DENEGADO como PDF oficial

Historial muestra pendiente
→ DENEGADO
FASE 23 — DOCUMENTACIÓN

Crear/actualizar:

README.md
docs/ARQUITECTURA.md
docs/BASE_DE_DATOS.md
docs/API.md
docs/AUDITORIA.md
docs/VERSIONADO.md
docs/DELEGACIONES.md
docs/DESARROLLO.md

Documentar:

arquitectura;
instalación;
Docker;
variables de entorno;
BD;
endpoints;
autenticación;
permisos;
versionado;
auditoría;
delegación;
PDF;
tests.


FASE 24 — AUDITORÍA FINAL DEL PROYECTO

Antes de declarar terminado:

BD
[ ] Esquema limpio
[ ] FK correctas
[ ] Índices
[ ] Constraints
[ ] Versionado
[ ] Auditoría
[ ] Delegación
[ ] Papelera
Backend
[ ] Arquitectura limpia
[ ] Sin modelos antiguos
[ ] Casos de uso
[ ] Repositorios
[ ] Auth
[ ] Permisos
[ ] Cálculos
[ ] Versionado
[ ] Auditoría
[ ] PDF
Frontend
[ ] Dashboard
[ ] Pacientes
[ ] Nueva orden
[ ] Paneles
[ ] Estudios
[ ] Pendientes
[ ] Colaboración
[ ] Historial
[ ] Versiones
[ ] Papelera
[ ] Perfil
[ ] Admin
Seguridad
[ ] Autor protegido
[ ] Colaborador limitado
[ ] Pendientes protegidos
[ ] Oficiales inmutables
[ ] Correcciones versionadas
[ ] Auditoría
Calidad
[ ] Tests backend
[ ] Tests frontend
[ ] TypeScript
[ ] Build
[ ] Docker
[ ] README

AL final de todo preparas los archivos pertinentes para dockerizar el proyecto

LIS-LABORATORIO-HOSPITAL_METODISTA/
│
├── docker-compose.yml          ← Ya lo tenemos - Actualizarlo de ser necesario 
├── .dockerignore               ← RECOMENDADO
├── .gitignore                  ← OBLIGATORIO
├── .env.example                ← RECOMENDADO
├── README.md                   ← RECOMENDADO
│
├── backend/
│   ├── Dockerfile              ← OBLIGATORIO
│   ├── requirements.txt        ← OBLIGATORIO
│   ├── .env.example            ← RECOMENDADO
│   └── ... código FastAPI
│
├── frontend/
│   ├── Dockerfile              ← OBLIGATORIO
│   ├── package.json            ← OBLIGATORIO
│   ├── package-lock.json       ← RECOMENDADO
│   └── ... código React/Vite
│
└── database/
    └── init.sql                ← Ya lo tenemos 
    
Es normal que algunos archivos como .env.example esten vacios ya que aun no se completa el desarrollo todo esto solo es preparacion

SEGUIR LA SUGERENCIA PARA ORDENAR EL PROYECTO Y DIRECTORIOS 
LIS
│
├── Backend
│   └── app/
│       ├── domain/
│       │   ├── entities/
│       │   ├── services/
│       │   ├── calculations/
│       │   │   ├── hemograma/
│       │   │   ├── hepatograma/
│       │   │   ├── perfil_lipidico/
│       │   │   ├── proteinograma/
│       │   │   └── ...
│       │   └── exceptions/
│       │
│       ├── application/
│       │   ├── use_cases/
│       │   ├── dto/
│       │   └── ports/
│       │
│       ├── adapters/
│       │   ├── persistence/
│       │   │   ├── models/
│       │   │   ├── repositories/
│       │   │   └── session.py
│       │   ├── pdf/
│       │   └── security/
│       │
│       └── entrypoints/
│           └── api/
│               ├── auth/
│               ├── pacientes/
│               ├── ordenes/
│               ├── estudios/
│               ├── resultados/
│               ├── delegaciones/
│               ├── historial/
│               ├── auditoria/
│               └── papelera/
│
└── Frontend
    └── src/
        ├── app/
        ├── features/
        │   ├── auth/
        │   ├── pacientes/
        │   ├── ordenes/
        │   ├── historial/
        │   ├── delegaciones/
        │   ├── auditoria/
        │   └── usuarios/
        │
        ├── modules/
        │   ├── hemograma/
        │   ├── quimica_sanguinea/
        │   ├── electrolitos/
        │   ├── hepatograma/
        │   ├── perfil_lipidico/
        │   ├── proteinograma/
        │   └── ...14 estudios
        │
        ├── components/
        ├── pages/
        ├── services/
        ├── types/
        ├── hooks/
        └── utils/

## SISTEMA LIS — LABORATORIO METODISTA

Necesito que trabajes exclusivamente en la **reestructuración arquitectónica, organización y limpieza del código existente** del proyecto.

El objetivo de esta tarea NO es desarrollar nuevas funcionalidades clínicas.

El objetivo es dejar el proyecto preparado para continuar desarrollando correctamente los 14 estudios/análisis del LIS sin volver a caer en código spaghetti.

El proyecto utiliza:

```text
Backend:
Python
FastAPI
SQLAlchemy
PostgreSQL

Frontend:
React
TypeScript
Vite
Tailwind

Infraestructura:
Docker

Autenticación:
JWT
```

Existe código funcional que debe conservarse cuando sea correcto.

Existe código desorganizado, duplicado y partes que actualmente NO respetan realmente una arquitectura hexagonal.

---

# 1. OBJETIVO PRINCIPAL

Debes transformar el proyecto actual desde una estructura aproximadamente:

```text
routers
services
models
schemas
components
pages
```

mezclados y con responsabilidades cruzadas, hacia una arquitectura claramente separada.

La meta es que cualquier programador pueda responder fácilmente:

> ¿Dónde está la lógica clínica?

> ¿Dónde está la lógica de negocio?

> ¿Dónde está la persistencia?

> ¿Dónde está la API?

> ¿Dónde está cada estudio?

> ¿Dónde está cada pantalla?

> ¿Dónde está cada llamada HTTP?

> ¿Dónde están los componentes reutilizables?

Si una pieza de código no tiene una responsabilidad clara, debe revisarse.

---

# 2. REGLA FUNDAMENTAL

## NO REESCRIBIR EL PROYECTO DESDE CERO

Antes de mover o eliminar cualquier archivo:

1. inspeccionar el repositorio;
2. identificar dependencias;
3. identificar código funcional;
4. identificar duplicaciones;
5. identificar código muerto;
6. identificar responsabilidades mezcladas;
7. identificar referencias antiguas;
8. determinar qué debe conservarse;
9. determinar qué debe moverse;
10. determinar qué debe eliminarse.

No quiero una reorganización puramente estética.

Mover archivos de una carpeta a otra sin corregir sus responsabilidades NO constituye una arquitectura limpia.

---

# 3. NO INVENTAR UNA NUEVA ARQUITECTURA DISTINTA

La arquitectura objetivo será una **arquitectura hexagonal/principios de Ports & Adapters**, adaptada al tamaño real del LIS.

No se pretende implementar una arquitectura académica excesivamente compleja.

La separación fundamental será:

```text
DOMAIN
APPLICATION
ADAPTERS
ENTRYPOINTS
```

Conceptualmente:

```text
                 ┌─────────────────────┐
                 │      FRONTEND       │
                 └──────────┬──────────┘
                            │ HTTP
                            ▼
                 ┌─────────────────────┐
                 │     ENTRYPOINTS     │
                 │      FastAPI        │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │    APPLICATION      │
                 │    Use Cases        │
                 │    Ports            │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │       DOMAIN        │
                 │ reglas + clínica    │
                 └──────────┬──────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
       ┌─────────────────┐     ┌─────────────────┐
       │   DB ADAPTER    │     │   PDF/SECURITY  │
       │ SQLAlchemy      │     │    ADAPTERS     │
       └─────────────────┘     └─────────────────┘
```

---

# 4. REGLA DE DEPENDENCIAS

Las dependencias deben apuntar hacia el núcleo.

La regla conceptual es:

```text
entrypoints
      ↓
application
      ↓
domain
```

y:

```text
adapters → implementan ports
```

El dominio NO debe depender de infraestructura.

Por tanto, dentro de:

```text
domain/
```

NO debe aparecer:

```python
from fastapi import ...
```

ni:

```python
from sqlalchemy import ...
```

ni:

```python
from sqlalchemy.orm import ...
```

ni acceso directo a PostgreSQL.

---

# 5. ESTRUCTURA OBJETIVO DEL BACKEND

La estructura recomendada será:

```text
backend/
└── app/
    │
    ├── domain/
    │   ├── entities/
    │   ├── value_objects/
    │   ├── services/
    │   ├── calculations/
    │   └── exceptions/
    │
    ├── application/
    │   ├── use_cases/
    │   ├── dto/
    │   └── ports/
    │
    ├── adapters/
    │   ├── persistence/
    │   │   ├── models/
    │   │   ├── repositories/
    │   │   └── session.py
    │   │
    │   ├── pdf/
    │   └── security/
    │
    └── entrypoints/
        └── api/
            ├── auth/
            ├── usuarios/
            ├── pacientes/
            ├── paneles/
            ├── estudios/
            ├── ordenes/
            ├── resultados/
            ├── delegaciones/
            ├── historial/
            ├── auditoria/
            └── papelera/
```

NO es obligatorio copiar literalmente estos nombres si el proyecto ya utiliza convenciones razonables.

Lo obligatorio es mantener las responsabilidades separadas.

---

# 6. ¿DÓNDE VAN LOS 14 ESTUDIOS?

Esta es una decisión fundamental.

Los 14 estudios NO deben convertirse en 14 routers, 14 repositorios y 14 modelos SQLAlchemy independientes si no lo necesitan.

Los 14 estudios son principalmente **dominio clínico**.

Por tanto, su lógica clínica debe vivir dentro de:

```text
domain/calculations/
```

Por ejemplo:

```text
domain/
└── calculations/
    ├── hemograma/
    │   ├── strategy.py
    │   ├── rules.py
    │   ├── types.py
    │   └── __init__.py
    │
    ├── quimica_sanguinea/
    │   ├── strategy.py
    │   ├── rules.py
    │   ├── types.py
    │   └── __init__.py
    │
    ├── electrolitos/
    ├── hepatograma/
    ├── perfil_lipidico/
    ├── proteinograma/
    └── ...
```

Los otros estudios deben seguir exactamente el mismo principio.

---

# 7. NO CREAR ESTO

No quiero:

```text
app/modules/
    hemograma_router.py
    hemograma_model.py
    hemograma_schema.py
    hemograma_service.py
    hemograma_repository.py
    hemograma_database.py
```

para cada estudio solamente por repetir la misma arquitectura.

Eso generaría una duplicación enorme.

Los estudios deben encapsular principalmente:

```text
reglas clínicas
cálculos
validaciones
tipos de entrada/salida clínicos
```

La persistencia es una responsabilidad común del sistema.

---

# 8. ¿ENTONCES PARA QUÉ EXISTE `modules/`?

Si actualmente el proyecto ya tiene:

```text
app/modules/
```

NO la elimines automáticamente.

Primero inspecciona su contenido.

Si esa carpeta mezcla:

```text
router
model
schema
service
calculation
database
```

entonces está mezclando responsabilidades y debe ser desmontada/reorganizada.

Si se considera útil conservar una carpeta `modules`, puede utilizarse para una organización **por feature**, pero NO debe romper la separación hexagonal.

La prioridad es la responsabilidad, no el nombre de la carpeta.

---

# 9. LOS DOS PANELES

Los siguientes conceptos:

```text
HC-QMC-SEROL-EGO
HC-QMC-SERO-PROT
```

SÍ deben existir.

Pero NO son estudios clínicos.

Son:

```text
PANELES
```

o agrupadores de estudios.

Su relación será:

```text
Panel
   ↓
PanelEstudio
   ↓
Estudio
```

Ejemplo:

```text
HC-QMC-SERO-PROT
        │
        ├── Estudio A
        ├── Estudio B
        ├── Estudio C
        └── Estudio D
```

Los nombres y composición exacta deben tomarse del Excel definido para el proyecto.

No inventar la composición.

---

# 10. PANEL ≠ ESTUDIO

Nunca implementar:

```text
HC-QMC-SERO-PROT
```

como si fuera un cálculo clínico.

No debe existir:

```text
ProteinPanelStrategy
```

para calcular el panel.

El panel únicamente sirve para:

```text
agrupar
seleccionar
mostrar
```

Los cálculos pertenecen a cada estudio individual.

---

# 11. ESTUDIO ≠ ORDEN

Mantener claramente:

```text
Paciente
   ↓
Orden
   ↓
OrdenEstudio
   ↓
Estudio
   ↓
Resultado
```

Una orden puede contener varios estudios.

Por tanto, no crear una arquitectura donde cada estudio cree su propia orden.

La orden es responsabilidad transversal del LIS.

---

# 12. DOMAIN

La carpeta:

```text
domain/
```

debe contener reglas que representan el negocio real del laboratorio.

Puede contener:

```text
entities/
value_objects/
services/
calculations/
exceptions/
```

Ejemplos:

```text
Paciente
Orden
Estudio
Resultado
Version
Delegacion
```

Pero no deben ser simples copias de modelos SQLAlchemy.

---

# 13. SQLALCHEMY NO ES EL DOMAIN

Esto es importante.

No hacer:

```python
class Orden(Base):
```

dentro de:

```text
domain/entities/
```

si esa clase depende de SQLAlchemy.

Los modelos SQLAlchemy deben estar en:

```text
adapters/persistence/models/
```

El dominio debe permanecer independiente.

---

# 14. APPLICATION

La carpeta:

```text
application/
```

representa lo que el sistema hace.

Aquí deben existir casos de uso como:

```text
crear_paciente
buscar_paciente

crear_orden
agregar_estudio
quitar_estudio

guardar_borrador
calcular_estudio
oficializar_orden

delegar_orden
delegar_estudio
aceptar_delegacion

crear_correccion
consultar_versiones
consultar_cambios

consultar_historial

mover_a_papelera
restaurar

generar_pdf
```

El caso de uso coordina.

No debe contener directamente SQL.

---

# 15. PORTS

Dentro de:

```text
application/ports/
```

crear interfaces para las dependencias externas.

Por ejemplo:

```text
PacienteRepository
OrdenRepository
EstudioRepository
ResultadoRepository
UsuarioRepository
DelegacionRepository
AuditoriaRepository
PdfGenerator
PasswordHasher
TokenProvider
```

La aplicación conoce estas interfaces.

No conoce:

```text
SQLAlchemy
PostgreSQL
```

---

# 16. ADAPTERS/PERSISTENCE

Aquí vive SQLAlchemy.

Por ejemplo:

```text
adapters/
└── persistence/
    ├── models/
    ├── repositories/
    └── session.py
```

Los repositorios implementan los ports definidos por application.

Ejemplo conceptual:

```text
application/ports/orden_repository.py
                 ↑
                 │ implementa
                 │
adapters/persistence/repositories/sqlalchemy_orden_repository.py
```

---

# 17. ENTRYPOINTS

FastAPI pertenece a:

```text
entrypoints/api/
```

Los routers solamente deben:

```text
recibir HTTP
validar request
obtener usuario autenticado
llamar caso de uso
transformar respuesta
```

No deben contener reglas clínicas.

---

# 18. PROHIBIDO EN UN ROUTER

No quiero routers de 300–500 líneas que hagan:

```text
consulta SQL
validación
cálculo
autorización
auditoría
persistencia
respuesta
```

todo dentro de una función.

Si encontramos esto:

```python
@router.post(...)
def crear_orden(...):
    # 200 líneas
```

debe ser dividido.

---

# 19. CÁLCULOS CLÍNICOS

Las estrategias existentes como:

```text
hemograma.py
hepatograma.py
perfil_lipidico.py
proteinograma.py
```

deben conservarse si contienen lógica válida.

Su ubicación final debe ser equivalente a:

```text
domain/calculations/
```

La estrategia debe recibir datos y producir resultados.

Ejemplo:

```python
result = strategy.calculate(input_data)
```

No:

```python
strategy.calculate(db)
```

---

# 20. LOS CÁLCULOS NO DEBEN CONOCER POSTGRESQL

Una estrategia clínica NO debe hacer:

```python
db.query(...)
```

ni:

```python
session.add(...)
```

ni:

```python
session.commit(...)
```

Su responsabilidad es exclusivamente:

```text
entrada clínica
↓
validación
↓
cálculo
↓
resultado clínico
↓
advertencias
```

---

# 21. FRONTEND — PROBLEMA ACTUAL

El frontend debe ser tratado como una segunda arquitectura que necesita limpieza.

No quiero una estructura donde:

```text
pages/
components/
services/
```

contengan código mezclado sin criterio.

Especialmente evitar:

```text
Dashboard.tsx
```

con cientos de líneas que:

* consulta API;
* calcula;
* transforma datos;
* controla permisos;
* renderiza formularios;
* decide navegación;
* contiene lógica de cada estudio.

Eso es spaghetti frontend.

---

# 22. ESTRUCTURA OBJETIVO DEL FRONTEND

Crear/adaptar:

```text
frontend/
└── src/
    ├── app/
    │
    ├── features/
    │   ├── auth/
    │   ├── pacientes/
    │   ├── ordenes/
    │   ├── historial/
    │   ├── delegaciones/
    │   ├── auditoria/
    │   └── usuarios/
    │
    ├── modules/
    │   ├── hemograma/
    │   ├── quimica-sanguinea/
    │   ├── electrolitos/
    │   ├── hepatograma/
    │   ├── perfil-lipidico/
    │   ├── proteinograma/
    │   └── ...14 estudios
    │
    ├── components/
    ├── pages/
    ├── services/
    ├── hooks/
    ├── types/
    └── utils/
```

---

# 23. `features/` VS `modules/`

Esta distinción es importante.

## `features/`

Representa funcionalidades del sistema:

```text
pacientes
ordenes
historial
delegaciones
auditoria
usuarios
```

## `modules/`

Representa los estudios clínicos:

```text
hemograma
hepatograma
proteinograma
...
```

No mezclar ambos conceptos.

---

# 24. EJEMPLO DE UN MÓDULO CLÍNICO FRONTEND

Por ejemplo:

```text
modules/
└── hemograma/
    ├── HemogramaForm.tsx
    ├── HemogramaResult.tsx
    ├── hemograma.types.ts
    ├── hemograma.validation.ts
    └── index.ts
```

Puede ampliarse si realmente lo necesita.

Pero NO crear:

```text
HemogramaPage
HemogramaRouter
HemogramaRepository
HemogramaDatabase
```

en frontend.

---

# 25. COMPONENTES REUTILIZABLES

Los componentes genéricos deben permanecer fuera de los módulos.

Ejemplo:

```text
components/
├── forms/
│   ├── NumericField.tsx
│   ├── TextField.tsx
│   └── SelectField.tsx
│
├── results/
│   ├── ResultTable.tsx
│   ├── ReferenceRange.tsx
│   └── WarningMessage.tsx
│
├── layout/
│   ├── Sidebar.tsx
│   ├── Header.tsx
│   └── PageContainer.tsx
│
└── ui/
```

Los módulos utilizan estos componentes.

---

# 26. NO CREAR UN MEGAFORMULARIO

Prohibido construir:

```text
StudyForm.tsx
```

con cientos de:

```text
if studyType === ...
```

Ejemplo incorrecto:

```typescript
if (study === "hemograma") {
   ...
}

if (study === "hepatograma") {
   ...
}

if (study === "proteinograma") {
   ...
}
```

Eso vuelve a crear spaghetti.

Cada estudio debe tener su propio componente clínico.

---

# 27. SERVICES FRONTEND

No realizar llamadas HTTP directamente desde cada componente.

Crear servicios:

```text
services/
├── auth.service.ts
├── pacientes.service.ts
├── ordenes.service.ts
├── estudios.service.ts
├── resultados.service.ts
├── delegaciones.service.ts
├── historial.service.ts
├── auditoria.service.ts
├── papelera.service.ts
├── usuarios.service.ts
└── pdf.service.ts
```

Los componentes consumen estos servicios.

---

# 28. TYPESCRIPT

Los tipos deben representar el modelo real.

Por ejemplo:

```text
Paciente
Orden
OrdenEstudio
Panel
Estudio
ResultadoVersion
ResultadoValor
Delegacion
CambioResultado
Auditoria
```

Eliminar progresivamente tipos antiguos como:

```text
OrdenExamen
ResultadoModulo
Enmienda
```

si ya no corresponden al modelo definitivo.

NO utilizar:

```typescript
any
```

para ocultar errores de integración.

---

# 29. ESTADO GLOBAL

Revisar el estado actual.

No crear un estado global gigante que contenga:

```text
paciente
orden
hemograma
hepatograma
usuarios
historial
auditoria
...
```

sin separación.

El estado debe corresponder a las necesidades reales de cada feature.

---

# 30. PÁGINAS

Las páginas deben ser principalmente composición.

Ejemplo:

```text
NuevaOrdenPage
```

debería componer:

```text
PatientSearch
StudySelector
PanelSelector
OrderSummary
```

No contener toda la implementación internamente.

---

# 31. DASHBOARD

El Dashboard NO debe presentar los 14 estudios como menú principal.

El sistema gira alrededor del flujo de trabajo:

```text
Inicio
Pacientes
Nueva orden
Mis órdenes
Pendientes
Órdenes colaborativas
Historial
Cambios
Papelera
Perfil
```

Los estudios aparecen después de:

```text
crear/abrir una orden
```

---

# 32. FLUJO FRONTEND CORRECTO

```text
Dashboard
   ↓
Nueva orden
   ↓
Buscar paciente
   ↓
Seleccionar paciente
   ↓
Seleccionar panel/estudios
   ↓
Crear orden
   ↓
Folio
   ↓
Workspace de orden
   ↓
Estudios
   ↓
Formulario clínico
   ↓
Guardar / Calcular
   ↓
Pendiente
   ↓
Revisar
   ↓
Oficializar
```

Esto representa mucho mejor el trabajo diario del laboratorio.

---

# 33. WORKSPACE DE ORDEN

Debe existir conceptualmente una pantalla:

```text
OrderWorkspace
```

que muestre:

```text
Folio
Paciente
CI
Autor
Colaborador
Estado
```

y debajo:

```text
Estudio 1
Estudio 2
Estudio 3
...
```

Cada estudio abre su módulo correspondiente.

---

# 34. NO DUPLICAR INFORMACIÓN DE LA ORDEN

El módulo:

```text
Hemograma
```

NO debe volver a implementar:

```text
Paciente
Autor
Folio
Delegación
Auditoría
```

Eso pertenece a la orden/workspace.

El módulo recibe el contexto necesario.

---

# 35. PANEL EN FRONTEND

Los paneles deben servir para selección.

Ejemplo:

```text
HC-QMC-SERO-PROT
```

selecciona:

```text
☑ Estudio A
☑ Estudio B
☑ Estudio C
```

El usuario puede revisar la selección antes de crear la orden.

No debe abrir directamente un "formulario del panel".

---

# 36. LOS 14 ESTUDIOS

Crear una entrada estructural para cada uno de los 14 estudios definidos por el proyecto.

Pero:

> NO inventar nombres ni lógica clínica que no estén definidos en el Excel/documentación.

Para cada estudio debe existir al menos una estructura preparada:

```text
backend:
domain/calculations/<estudio>/

frontend:
modules/<estudio>/
```

Los estudios que todavía no estén implementados completamente pueden quedar explícitamente marcados como:

```text
TODO / PENDIENTE DE IMPLEMENTACIÓN CLÍNICA
```

pero su arquitectura no debe obligar a modificar otros estudios.

---

# 37. REGLA DE INDEPENDENCIA DE LOS ESTUDIOS

Un estudio puede reutilizar infraestructura genérica.

Por ejemplo:

```text
BaseCalculationStrategy
CalculationResult
ValidationError
```

pero NO debe depender de la implementación interna de otro estudio.

Incorrecto:

```text
Proteinograma
   ↓
importa variables internas
   ↓
Hepatograma
```

Correcto:

```text
Proteinograma
   ↓
infraestructura clínica común
```

---

# 38. BASE DE DATOS

La arquitectura del código debe respetar el modelo definitivo:

```text
roles
usuarios
pacientes

paneles
panel_estudios

estudios
estudio_versiones
parametros
rangos_referencia

ordenes
orden_estudios

resultado_versiones
resultado_valores

delegaciones
delegacion_estudios

auditoria
cambios_resultado

papelera_ordenes
auditoria_seguridad
```

No crear nuevamente:

```text
ordenes_examen
resultado_modulo
auditoria_enmiendas
```

---

# 39. `pieza`

El nombre definitivo debe ser:

```text
pieza
```

No:

```text
pieza_cama
```

Realizar búsqueda global.

Corregir:

```text
BD
SQLAlchemy
Pydantic
TypeScript
formularios
PDF
```

---

# 40. ROLES

Solo:

```text
ADMIN
BIOQUIMICO
```

Eliminar:

```text
INTERNO
```

No dejar referencias antiguas en:

```text
backend
frontend
BD
tests
types
guards
```

---

# 41. AUDITORÍA Y VERSIONADO

No crear un sistema paralelo de "enmiendas".

El sistema debe utilizar:

```text
resultado_versiones
cambios_resultado
auditoria
```

No mantener dos mecanismos para representar la misma corrección.

---

# 42. REGLA SOBRE DATOS CLÍNICOS

Nunca mezclar en una clase/componente:

```text
persistencia
+
cálculo
+
UI
+
auditoría
```

Cada responsabilidad debe tener un lugar.

---

# 43. REGLA SOBRE REUTILIZACIÓN

Reutilizar cuando se trata de infraestructura:

```text
inputs
tablas
validaciones genéricas
manejo de errores
autenticación
layout
repositorios base si realmente corresponde
```

No reutilizar mezclando lógica clínica de dos estudios.

---

# 44. TESTS

Antes y después de mover archivos:

```bash
pytest
```

y en frontend:

```bash
npm run build
```

además del comando de TypeScript existente.

No aceptar:

```text
"funciona"
```

si el proyecto ya no compila.

---

# 45. IMPORTS

Después de cada movimiento:

* corregir imports;
* eliminar imports muertos;
* eliminar referencias circulares;
* verificar dependencias.

No resolver errores mediante imports dinámicos innecesarios.

Evitar:

```python
try:
    from ...
except ImportError:
    pass
```

para ocultar problemas estructurales.

---

# 46. DEPENDENCIAS CIRCULARES

Detectar situaciones como:

```text
router → service → router
```

o:

```text
domain → repository → domain
```

o:

```text
component A → component B → component A
```

Resolverlas estructuralmente.

---

# 47. CONFIGURACIÓN

Centralizar configuración.

No tener:

```text
DATABASE_URL
```

duplicada en cinco archivos.

Utilizar una única fuente de configuración.

---

# 48. MAIN.PY

`main.py` debe ser pequeño.

Debe encargarse principalmente de:

```text
crear aplicación
configurar middleware
registrar routers
configuración general
```

No debe contener lógica clínica.

---

# 49. ROUTER REGISTRATION

Registrar routers explícitamente.

No utilizar imports opcionales para ocultar módulos incompletos.

Incorrecto:

```python
try:
    ...
except ImportError:
    pass
```

Correcto:

```text
si un módulo obligatorio falta,
el proyecto debe fallar claramente durante desarrollo.
```

---

# 50. CRITERIOS DE ACEPTACIÓN BACKEND

Al terminar:

```text
[ ] Domain independiente de FastAPI/SQLAlchemy
[ ] Application contiene casos de uso
[ ] Ports definidos
[ ] Adapters implementan ports
[ ] FastAPI solamente entra por entrypoints
[ ] SQLAlchemy aislado
[ ] Cálculos clínicos aislados
[ ] 14 estudios estructurados
[ ] Paneles separados de estudios
[ ] No existen modelos antiguos funcionales
[ ] No existe INTERNO
[ ] No existe pieza_cama
[ ] No existen duplicaciones importantes
[ ] Tests pasan
```

---

# 51. CRITERIOS DE ACEPTACIÓN FRONTEND

```text
[ ] Dashboard orientado al flujo LIS
[ ] features separadas
[ ] módulos clínicos separados
[ ] servicios HTTP centralizados
[ ] tipos TypeScript coherentes
[ ] componentes reutilizables
[ ] páginas delgadas
[ ] ningún MegaFormulario
[ ] ningún componente con lógica de toda la aplicación
[ ] 14 estudios estructurados
[ ] paneles independientes
[ ] build exitoso
```

---

# 52. CRITERIO DE ACEPTACIÓN MÁS IMPORTANTE

Después de la reorganización debe ser posible agregar un nuevo estudio sin modificar:

```text
autenticación
pacientes
órdenes
delegación
auditoría
papelera
```

salvo las configuraciones generales necesarias.

Por ejemplo, si mañana se agrega:

```text
Estudio 15
```

idealmente debe poder incorporarse creando:

```text
domain/calculations/estudio15/
frontend/src/modules/estudio15/
```

y registrándolo en el catálogo/configuración correspondiente.

No debería ser necesario modificar un archivo monstruoso de 2.000 líneas.

---

# 53. NO IMPLEMENTAR NUEVAS FUNCIONALIDADES DURANTE ESTA TAREA

Esta tarea es principalmente:

```text
REESTRUCTURACIÓN
+
LIMPIEZA
+
MIGRACIÓN
```

No aprovecharla para cambiar:

```text
fórmulas
```

o agregar funcionalidades no solicitadas.

Si encuentras un problema funcional que requiere una decisión:

```text
documentarlo
```

en lugar de inventar.

---

# 54. DOCUMENTACIÓN OBLIGATORIA

Crear:

```text
docs/ARQUITECTURA.md
```

Explicar:

```text
Domain
Application
Ports
Adapters
Entrypoints
Frontend features
Frontend modules
```

También incluir un diagrama similar a:

```text
Frontend
   ↓
FastAPI
   ↓
Application
   ↓
Domain
   ↓
Ports
   ↓
Adapters
   ↓
PostgreSQL
```

Y explicar:

```text
Panel
 ↓
PanelEstudio
 ↓
Estudio
```

y:

```text
Orden
 ↓
OrdenEstudio
 ↓
ResultadoVersion
 ↓
ResultadoValor
```

---

# 55. INFORME FINAL

Al terminar NO responder simplemente:

```text
"arquitectura reorganizada"
```

Entregar:

## Estructura anterior

```text
...
```

## Problemas encontrados

```text
...
```

## Estructura nueva

```text
...
```

## Archivos movidos

```text
...
```

## Archivos creados

```text
...
```

## Archivos eliminados

```text
...
```

## Código conservado

```text
...
```

## Código migrado

```text
...
```

## Código eliminado

```text
...
```

## Problemas que no se pudieron resolver

```text
...
```

## Tests

```text
pytest:
...

frontend build:
...

TypeScript:
...
```

---

# 56. REGLA FINAL

No quiero una arquitectura bonita solamente en el árbol de carpetas.

Quiero que las dependencias reales respeten la arquitectura.

Debe poder demostrarse que:

```text
Domain
NO conoce FastAPI.

Domain
NO conoce SQLAlchemy.

Domain
NO conoce React.

Application
NO ejecuta SQL directamente.

Routers
NO contienen lógica clínica.

React components
NO ejecutan directamente consultas SQL ni lógica backend.

Los estudios
NO dependen unos de otros.

Los paneles
NO son estudios.

Las órdenes
NO dependen de un estudio específico.

```

El objetivo final es que el LIS pueda crecer de:

```text
14 estudios
```

a más estudios en el futuro sin convertirse nuevamente en código spaghetti.


