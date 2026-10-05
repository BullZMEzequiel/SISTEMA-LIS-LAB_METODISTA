-- =============================================================================
-- SISTEMA LIS - LABORATORIO METODISTA
-- BASE DE DATOS PRINCIPAL
-- PostgreSQL
--
-- Modelo:
--   usuarios
--   pacientes
--   ordenes / folios
--   paneles -> estudios
--   versiones de configuración de estudios
--   parámetros
--   rangos de referencia
--   resultados pendientes/oficiales
--   versiones inmutables de resultados
--   delegaciones
--   auditoría
--   papelera
--
-- IMPORTANTE:
-- Los paneles HC-QMC-SEROL-EGO y HC-QMC-SERO-PROT son agrupadores de estudios.
-- NO son estudios clínicos independientes.
-- =============================================================================


-- =============================================================================
-- 0. EXTENSIONES Y ESQUEMA
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS laboratorio;

SET search_path TO laboratorio, public;


-- =============================================================================
-- 1. FUNCIONES GENERALES
-- =============================================================================

CREATE OR REPLACE FUNCTION set_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- 2. ROLES
-- =============================================================================

CREATE TABLE roles (
    id_rol          SMALLSERIAL PRIMARY KEY,
    nombre          VARCHAR(30) NOT NULL UNIQUE,
    descripcion     TEXT,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO roles (nombre, descripcion)
VALUES
    ('ADMIN', 'Administrador del sistema'),
    ('BIOQUIMICO', 'Usuario bioquímico que trabaja con pacientes y análisis');


-- =============================================================================
-- 3. USUARIOS
-- =============================================================================

CREATE TABLE usuarios (
    id_usuario              BIGSERIAL PRIMARY KEY,

    id_rol                  SMALLINT NOT NULL
                            REFERENCES roles(id_rol),

    ci                      VARCHAR(20) NOT NULL UNIQUE,

    nombres                 VARCHAR(100) NOT NULL,
    apellido_paterno        VARCHAR(100) NOT NULL,
    apellido_materno        VARCHAR(100),

    correo                  VARCHAR(150) UNIQUE,

    hash_password           VARCHAR(255) NOT NULL,

    foto_perfil_url         TEXT,

    activo                  BOOLEAN NOT NULL DEFAULT TRUE,

    ultimo_ingreso          TIMESTAMPTZ,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    eliminado_en            TIMESTAMPTZ
);

CREATE INDEX idx_usuarios_rol
    ON usuarios(id_rol);

CREATE INDEX idx_usuarios_activo
    ON usuarios(activo);

CREATE TRIGGER trg_usuarios_actualizado
BEFORE UPDATE ON usuarios
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();


-- =============================================================================
-- 4. PACIENTES
-- =============================================================================

CREATE TABLE pacientes (
    id_paciente             BIGSERIAL PRIMARY KEY,

    ci                      VARCHAR(30) NOT NULL UNIQUE,

    nombres                 VARCHAR(100) NOT NULL,
    apellido_paterno        VARCHAR(100) NOT NULL,
    apellido_materno        VARCHAR(100),

    fecha_nacimiento        DATE NOT NULL,

    sexo                    CHAR(1) NOT NULL
                            CHECK (sexo IN ('M', 'F')),

    telefono                VARCHAR(30),
    correo                  VARCHAR(150),

    creado_por              BIGINT
                            REFERENCES usuarios(id_usuario),

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    eliminado_en            TIMESTAMPTZ
);

CREATE INDEX idx_pacientes_ci
    ON pacientes(ci);

CREATE INDEX idx_pacientes_nombre
    ON pacientes(apellido_paterno, apellido_materno, nombres);

CREATE INDEX idx_pacientes_fecha_nacimiento
    ON pacientes(fecha_nacimiento);

CREATE TRIGGER trg_pacientes_actualizado
BEFORE UPDATE ON pacientes
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();


-- =============================================================================
-- 5. PANELES
--
-- Un panel es una agrupación predeterminada de estudios.
--
-- Ejemplo:
--
-- HC-QMC-SEROL-EGO
--      ├── Hemograma
--      ├── Química sanguínea
--      ├── Perfil lipídico
--      └── ...
--
-- HC-QMC-SERO-PROT
--      ├── Hemograma
--      ├── Química sanguínea
--      ├── Proteinograma
--      └── ...
--
-- Los paneles NO almacenan resultados clínicos.
-- =============================================================================

CREATE TABLE paneles (
    id_panel                BIGSERIAL PRIMARY KEY,

    codigo                  VARCHAR(50) NOT NULL UNIQUE,

    nombre                  VARCHAR(150) NOT NULL,

    descripcion             TEXT,

    activo                  BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_paneles_actualizado
BEFORE UPDATE ON paneles
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();


-- =============================================================================
-- 6. ESTUDIOS
--
-- Cada estudio representa un módulo clínico independiente.
-- =============================================================================

CREATE TABLE estudios (
    id_estudio              BIGSERIAL PRIMARY KEY,

    codigo                  VARCHAR(60) NOT NULL UNIQUE,

    nombre                  VARCHAR(150) NOT NULL,

    descripcion             TEXT,

    modulo_frontend         VARCHAR(100),

    estrategia_calculo      VARCHAR(100),

    activo                  BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_estudios_activo
    ON estudios(activo);

CREATE TRIGGER trg_estudios_actualizado
BEFORE UPDATE ON estudios
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();


-- =============================================================================
-- 7. RELACIÓN PANEL <-> ESTUDIO
--
-- Un panel puede contener varios estudios.
-- Un estudio puede pertenecer a varios paneles.
-- =============================================================================

CREATE TABLE panel_estudios (
    id_panel                BIGINT NOT NULL
                            REFERENCES paneles(id_panel)
                            ON DELETE CASCADE,

    id_estudio              BIGINT NOT NULL
                            REFERENCES estudios(id_estudio)
                            ON DELETE RESTRICT,

    orden_visualizacion     INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (id_panel, id_estudio)
);

CREATE INDEX idx_panel_estudios_estudio
    ON panel_estudios(id_estudio);


-- =============================================================================
-- 8. VERSIONES DE CONFIGURACIÓN DE ESTUDIOS
--
-- Permite modificar fórmulas, parámetros o estructura en el futuro
-- sin alterar la configuración utilizada por resultados antiguos.
-- =============================================================================

CREATE TABLE estudio_versiones (
    id_estudio_version      BIGSERIAL PRIMARY KEY,

    id_estudio              BIGINT NOT NULL
                            REFERENCES estudios(id_estudio)
                            ON DELETE RESTRICT,

    numero_version          INTEGER NOT NULL,

    descripcion_cambios     TEXT,

    configuracion           JSONB NOT NULL DEFAULT '{}'::jsonb,

    activa                  BOOLEAN NOT NULL DEFAULT TRUE,

    creado_por              BIGINT
                            REFERENCES usuarios(id_usuario),

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (id_estudio, numero_version)
);

CREATE INDEX idx_estudio_versiones_estudio
    ON estudio_versiones(id_estudio);

CREATE INDEX idx_estudio_versiones_activa
    ON estudio_versiones(activa);


-- =============================================================================
-- 9. PARÁMETROS DE CADA ESTUDIO
--
-- Cada estudio tiene su propia estructura.
--
-- tipo_campo:
--   ENTRADA_MANUAL
--   CALCULADO_AUTOMATICO
--   TEXTO
--   BOOLEANO
--   SELECCION
-- =============================================================================

CREATE TABLE parametros (
    id_parametro            BIGSERIAL PRIMARY KEY,

    id_estudio_version      BIGINT NOT NULL
                            REFERENCES estudio_versiones(id_estudio_version)
                            ON DELETE RESTRICT,

    codigo                  VARCHAR(80) NOT NULL,

    nombre                  VARCHAR(150) NOT NULL,

    tipo_campo              VARCHAR(30) NOT NULL
                            CHECK (
                                tipo_campo IN (
                                    'ENTRADA_MANUAL',
                                    'CALCULADO_AUTOMATICO',
                                    'TEXTO',
                                    'BOOLEANO',
                                    'SELECCION'
                                )
                            ),

    tipo_dato               VARCHAR(30) NOT NULL DEFAULT 'DECIMAL'
                            CHECK (
                                tipo_dato IN (
                                    'DECIMAL',
                                    'ENTERO',
                                    'TEXTO',
                                    'BOOLEANO',
                                    'FECHA'
                                )
                            ),

    unidad_medida           VARCHAR(50),

    formula_codigo          TEXT,

    orden_visualizacion     INTEGER NOT NULL DEFAULT 1,

    obligatorio             BOOLEAN NOT NULL DEFAULT FALSE,

    activo                  BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (id_estudio_version, codigo)
);

CREATE INDEX idx_parametros_estudio_version
    ON parametros(id_estudio_version);


-- =============================================================================
-- 10. RANGOS / VALORES DE REFERENCIA
--
-- Corresponde a la información de referencia de la pestaña VN.
--
-- No se almacena como un único campo "VN".
-- Cada parámetro puede tener varios rangos dependiendo de:
--   sexo
--   edad
--   condición
-- etc.
-- =============================================================================

CREATE TABLE rangos_referencia (
    id_rango_referencia     BIGSERIAL PRIMARY KEY,

    id_parametro            BIGINT NOT NULL
                            REFERENCES parametros(id_parametro)
                            ON DELETE RESTRICT,

    sexo                    CHAR(1)
                            CHECK (sexo IN ('M', 'F') OR sexo IS NULL),

    edad_minima             NUMERIC(6,2),

    edad_maxima             NUMERIC(6,2),

    unidad                  VARCHAR(50),

    limite_inferior         NUMERIC(18,6),

    limite_superior         NUMERIC(18,6),

    referencia_texto        TEXT,

    observaciones           TEXT,

    activo                  BOOLEAN NOT NULL DEFAULT TRUE,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        edad_minima IS NULL
        OR edad_maxima IS NULL
        OR edad_minima <= edad_maxima
    ),

    CHECK (
        limite_inferior IS NULL
        OR limite_superior IS NULL
        OR limite_inferior <= limite_superior
    )
);

CREATE INDEX idx_rangos_referencia_parametro
    ON rangos_referencia(id_parametro);

CREATE INDEX idx_rangos_referencia_sexo
    ON rangos_referencia(sexo);


-- =============================================================================
-- 11. ÓRDENES / FOLIOS
--
-- Un paciente puede tener muchas órdenes.
--
-- El folio solamente se genera cuando existe al menos un estudio asignado.
--
-- estados:
--
-- BORRADOR
--   Trabajo guardado pero todavía no oficial.
--
-- OFICIAL
--   Trabajo confirmado y visible en el historial oficial.
--
-- PAPELERA
--   Orden retirada por su autor.
-- =============================================================================

CREATE SEQUENCE seq_folio_lis
START WITH 1
INCREMENT BY 1;

CREATE TABLE ordenes (
    id_orden                BIGSERIAL PRIMARY KEY,

    folio                   VARCHAR(30) UNIQUE,

    id_paciente             BIGINT NOT NULL
                            REFERENCES pacientes(id_paciente)
                            ON DELETE RESTRICT,

    id_usuario_autor        BIGINT NOT NULL
                            REFERENCES usuarios(id_usuario)
                            ON DELETE RESTRICT,

    pieza                   VARCHAR(100),

    estado                  VARCHAR(20) NOT NULL DEFAULT 'BORRADOR'
                            CHECK (
                                estado IN (
                                    'BORRADOR',
                                    'OFICIAL',
                                    'PAPELERA'
                                )
                            ),

    comentario_general      TEXT,

    motivo_papelera         TEXT,

    eliminado_por           BIGINT
                            REFERENCES usuarios(id_usuario),

    eliminado_en            TIMESTAMPTZ,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    oficializado_en         TIMESTAMPTZ
);

CREATE INDEX idx_ordenes_paciente
    ON ordenes(id_paciente);

CREATE INDEX idx_ordenes_autor
    ON ordenes(id_usuario_autor);

CREATE INDEX idx_ordenes_estado
    ON ordenes(estado);

CREATE INDEX idx_ordenes_creado
    ON ordenes(creado_en);

CREATE INDEX idx_ordenes_oficializado
    ON ordenes(oficializado_en);

CREATE INDEX idx_ordenes_paciente_fecha
    ON ordenes(id_paciente, creado_en);

CREATE TRIGGER trg_ordenes_actualizado
BEFORE UPDATE ON ordenes
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();


-- =============================================================================
-- 12. FUNCIÓN PARA GENERAR FOLIO
-- =============================================================================

CREATE OR REPLACE FUNCTION generar_folio_lis()
RETURNS VARCHAR
AS $$
DECLARE
    numero BIGINT;
BEGIN
    numero := nextval('laboratorio.seq_folio_lis');

    RETURN 'LIS-' || LPAD(numero::TEXT, 8, '0');
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- 13. ESTUDIOS ASIGNADOS A UNA ORDEN
--
-- Una orden puede contener muchos estudios.
--
-- Ejemplo:
--
-- ORDEN LIS-00000001
--      ├── Hemograma
--      ├── Hepatograma
--      ├── Perfil lipídico
--      └── Proteinograma
-- =============================================================================

CREATE TABLE orden_estudios (
    id_orden_estudio        BIGSERIAL PRIMARY KEY,

    id_orden                BIGINT NOT NULL
                            REFERENCES ordenes(id_orden)
                            ON DELETE RESTRICT,

    id_estudio              BIGINT NOT NULL
                            REFERENCES estudios(id_estudio)
                            ON DELETE RESTRICT,

    id_estudio_version      BIGINT
                            REFERENCES estudio_versiones(id_estudio_version)
                            ON DELETE RESTRICT,

    estado                  VARCHAR(20) NOT NULL DEFAULT 'BORRADOR'
                            CHECK (
                                estado IN (
                                    'BORRADOR',
                                    'OFICIAL',
                                    'ANULADO'
                                )
                            ),

    observaciones           TEXT,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (id_orden, id_estudio)
);

CREATE INDEX idx_orden_estudios_orden
    ON orden_estudios(id_orden);

CREATE INDEX idx_orden_estudios_estudio
    ON orden_estudios(id_estudio);

CREATE INDEX idx_orden_estudios_estado
    ON orden_estudios(estado);

CREATE TRIGGER trg_orden_estudios_actualizado
BEFORE UPDATE ON orden_estudios
FOR EACH ROW
EXECUTE FUNCTION set_actualizado_en();


-- =============================================================================
-- 14. VERSIONES DE RESULTADOS
--
-- Cada estudio de una orden posee versiones.
--
-- V1 = resultado original
-- V2 = primera corrección
-- V3 = segunda corrección
--
-- Una versión oficial nunca se modifica.
--
-- snapshot_completo conserva una copia íntegra de la información utilizada
-- para generar esa versión.
-- =============================================================================

CREATE TABLE resultado_versiones (
    id_resultado_version    BIGSERIAL PRIMARY KEY,

    id_orden_estudio        BIGINT NOT NULL
                            REFERENCES orden_estudios(id_orden_estudio)
                            ON DELETE RESTRICT,

    numero_version          INTEGER NOT NULL,

    id_estudio_version      BIGINT NOT NULL
                            REFERENCES estudio_versiones(id_estudio_version)
                            ON DELETE RESTRICT,

    creado_por              BIGINT NOT NULL
                            REFERENCES usuarios(id_usuario)
                            ON DELETE RESTRICT,

    estado                  VARCHAR(20) NOT NULL DEFAULT 'BORRADOR'
                            CHECK (
                                estado IN (
                                    'BORRADOR',
                                    'OFICIAL',
                                    'SUPERADA',
                                    'ANULADA'
                                )
                            ),

    motivo_correccion       TEXT,

    comentario_estudio      TEXT,

    snapshot_completo      JSONB NOT NULL DEFAULT '{}'::jsonb,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    oficializado_en         TIMESTAMPTZ,

    UNIQUE (id_orden_estudio, numero_version),

    CHECK (
        numero_version = 1
        OR motivo_correccion IS NOT NULL
    )
);

CREATE INDEX idx_resultado_versiones_orden_estudio
    ON resultado_versiones(id_orden_estudio);

CREATE INDEX idx_resultado_versiones_estado
    ON resultado_versiones(estado);

CREATE INDEX idx_resultado_versiones_creado_por
    ON resultado_versiones(creado_por);


-- =============================================================================
-- 15. VALORES DE LOS RESULTADOS
--
-- Guarda cada parámetro individual de una versión.
-- =============================================================================

CREATE TABLE resultado_valores (
    id_resultado_valor     BIGSERIAL PRIMARY KEY,

    id_resultado_version   BIGINT NOT NULL
                           REFERENCES resultado_versiones(id_resultado_version)
                           ON DELETE RESTRICT,

    id_parametro           BIGINT NOT NULL
                           REFERENCES parametros(id_parametro)
                           ON DELETE RESTRICT,

    valor_numerico         NUMERIC(18,6),

    valor_texto            TEXT,

    valor_booleano         BOOLEAN,

    unidad_utilizada       VARCHAR(50),

    referencia_utilizada   TEXT,

    fuera_de_rango         BOOLEAN,

    valor_calculado        BOOLEAN NOT NULL DEFAULT FALSE,

    orden_visualizacion    INTEGER NOT NULL DEFAULT 1,

    UNIQUE (id_resultado_version, id_parametro)
);

CREATE INDEX idx_resultado_valores_version
    ON resultado_valores(id_resultado_version);

CREATE INDEX idx_resultado_valores_parametro
    ON resultado_valores(id_parametro);


-- =============================================================================
-- 16. DELEGACIONES
--
-- Máximo un colaborador por orden.
--
-- modalidad:
--
-- TRABAJO_COMPLETO
--     El colaborador puede trabajar toda la orden.
--
-- POR_ESTUDIO
--     El colaborador puede trabajar únicamente estudios específicos.
-- =============================================================================

CREATE TABLE delegaciones (
    id_delegacion           BIGSERIAL PRIMARY KEY,

    id_orden                BIGINT NOT NULL
                            REFERENCES ordenes(id_orden)
                            ON DELETE RESTRICT,

    id_usuario_autor        BIGINT NOT NULL
                            REFERENCES usuarios(id_usuario)
                            ON DELETE RESTRICT,

    id_usuario_colaborador  BIGINT NOT NULL
                            REFERENCES usuarios(id_usuario)
                            ON DELETE RESTRICT,

    modalidad               VARCHAR(30) NOT NULL
                            CHECK (
                                modalidad IN (
                                    'TRABAJO_COMPLETO',
                                    'POR_ESTUDIO'
                                )
                            ),

    comentario              TEXT,

    activa                  BOOLEAN NOT NULL DEFAULT TRUE,

    creada_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizada_en           TIMESTAMPTZ,

    CHECK (
        id_usuario_autor <> id_usuario_colaborador
    )
);

CREATE INDEX idx_delegaciones_orden
    ON delegaciones(id_orden);

CREATE INDEX idx_delegaciones_autor
    ON delegaciones(id_usuario_autor);

CREATE INDEX idx_delegaciones_colaborador
    ON delegaciones(id_usuario_colaborador);

CREATE UNIQUE INDEX uq_delegacion_activa_por_orden
    ON delegaciones(id_orden)
    WHERE activa = TRUE;


-- =============================================================================
-- 17. DELEGACIÓN POR ESTUDIO
--
-- Solo se utiliza cuando modalidad = POR_ESTUDIO.
-- =============================================================================

CREATE TABLE delegacion_estudios (
    id_delegacion           BIGINT NOT NULL
                            REFERENCES delegaciones(id_delegacion)
                            ON DELETE CASCADE,

    id_orden_estudio        BIGINT NOT NULL
                            REFERENCES orden_estudios(id_orden_estudio)
                            ON DELETE RESTRICT,

    PRIMARY KEY (id_delegacion, id_orden_estudio)
);


-- =============================================================================
-- 18. HISTORIAL DE CAMBIOS
--
-- Registra quién hizo qué y cuándo.
--
-- Esto es independiente de las versiones clínicas.
-- =============================================================================

CREATE TABLE auditoria (
    id_auditoria            BIGSERIAL PRIMARY KEY,

    id_usuario              BIGINT
                            REFERENCES usuarios(id_usuario),

    id_orden                BIGINT
                            REFERENCES ordenes(id_orden),

    id_orden_estudio        BIGINT
                            REFERENCES orden_estudios(id_orden_estudio),

    id_resultado_version    BIGINT
                            REFERENCES resultado_versiones(id_resultado_version),

    accion                  VARCHAR(50) NOT NULL,

    entidad                 VARCHAR(50),

    descripcion             TEXT,

    datos_anteriores        JSONB,

    datos_nuevos            JSONB,

    ip_origen               INET,

    user_agent              TEXT,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_auditoria_usuario
    ON auditoria(id_usuario);

CREATE INDEX idx_auditoria_orden
    ON auditoria(id_orden);

CREATE INDEX idx_auditoria_orden_estudio
    ON auditoria(id_orden_estudio);

CREATE INDEX idx_auditoria_fecha
    ON auditoria(creado_en);

CREATE INDEX idx_auditoria_accion
    ON auditoria(accion);


-- =============================================================================
-- 19. CAMBIOS DETALLADOS DE RESULTADOS
--
-- Permite mostrar:
--
-- Parámetro       Antes       Después       Usuario       Fecha
-- Hemoglobina     14.2        14.8          Usuario B     ...
-- =============================================================================

CREATE TABLE cambios_resultado (
    id_cambio               BIGSERIAL PRIMARY KEY,

    id_resultado_version    BIGINT NOT NULL
                            REFERENCES resultado_versiones(id_resultado_version)
                            ON DELETE RESTRICT,

    id_parametro            BIGINT
                            REFERENCES parametros(id_parametro)
                            ON DELETE RESTRICT,

    id_usuario              BIGINT NOT NULL
                            REFERENCES usuarios(id_usuario)
                            ON DELETE RESTRICT,

    valor_anterior          TEXT,

    valor_nuevo             TEXT,

    comentario              TEXT NOT NULL,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_cambios_resultado_version
    ON cambios_resultado(id_resultado_version);

CREATE INDEX idx_cambios_resultado_usuario
    ON cambios_resultado(id_usuario);

CREATE INDEX idx_cambios_resultado_parametro
    ON cambios_resultado(id_parametro);


-- =============================================================================
-- 20. PAPELERA
--
-- No se elimina físicamente una orden oficial.
-- =============================================================================

CREATE TABLE papelera_ordenes (
    id_papelera             BIGSERIAL PRIMARY KEY,

    id_orden                BIGINT NOT NULL UNIQUE
                            REFERENCES ordenes(id_orden)
                            ON DELETE RESTRICT,

    eliminado_por           BIGINT NOT NULL
                            REFERENCES usuarios(id_usuario),

    estado_anterior         VARCHAR(20) NOT NULL,

    motivo                  TEXT NOT NULL,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    restaurado              BOOLEAN NOT NULL DEFAULT FALSE,

    restaurado_por          BIGINT
                            REFERENCES usuarios(id_usuario),

    restaurado_en           TIMESTAMPTZ
);

CREATE INDEX idx_papelera_eliminado_por
    ON papelera_ordenes(eliminado_por);

CREATE INDEX idx_papelera_fecha
    ON papelera_ordenes(creado_en);

CREATE INDEX idx_papelera_restaurado
    ON papelera_ordenes(restaurado);


-- =============================================================================
-- 21. HISTORIAL DE SESIONES / SEGURIDAD
-- =============================================================================

CREATE TABLE auditoria_seguridad (
    id_evento               BIGSERIAL PRIMARY KEY,

    id_usuario              BIGINT
                            REFERENCES usuarios(id_usuario),

    evento                  VARCHAR(50) NOT NULL,

    ip_origen               INET,

    user_agent              TEXT,

    detalles                JSONB,

    creado_en               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_seguridad_usuario
    ON auditoria_seguridad(id_usuario);

CREATE INDEX idx_seguridad_evento
    ON auditoria_seguridad(evento);

CREATE INDEX idx_seguridad_fecha
    ON auditoria_seguridad(creado_en);


-- =============================================================================
-- 22. VISTAS PARA CONSULTAS FRECUENTES
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 22.1 Historial oficial
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_historial_oficial AS
SELECT
    o.id_orden,
    o.folio,

    p.id_paciente,
    p.ci AS paciente_ci,

    CONCAT_WS(
        ' ',
        p.nombres,
        p.apellido_paterno,
        p.apellido_materno
    ) AS paciente_nombre,

    o.id_usuario_autor,

    CONCAT_WS(
        ' ',
        u.nombres,
        u.apellido_paterno,
        u.apellido_materno
    ) AS autor_nombre,

    o.pieza,

    o.creado_en,
    o.oficializado_en,

    o.estado

FROM ordenes o
INNER JOIN pacientes p
    ON p.id_paciente = o.id_paciente

INNER JOIN usuarios u
    ON u.id_usuario = o.id_usuario_autor

WHERE o.estado = 'OFICIAL';


-- -----------------------------------------------------------------------------
-- 22.2 Pendientes del usuario
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_ordenes_pendientes AS
SELECT
    o.id_orden,
    o.folio,
    o.id_paciente,

    CONCAT_WS(
        ' ',
        p.nombres,
        p.apellido_paterno,
        p.apellido_materno
    ) AS paciente_nombre,

    o.id_usuario_autor,

    o.estado,

    o.creado_en,
    o.actualizado_en

FROM ordenes o
INNER JOIN pacientes p
    ON p.id_paciente = o.id_paciente

WHERE o.estado = 'BORRADOR';


-- =============================================================================
-- 23. PANELES INICIALES
--
-- Los paneles existen como agrupadores.
-- La relación exacta con los 14 estudios debe completarse utilizando
-- la estructura definitiva del Excel.
-- =============================================================================

INSERT INTO paneles (
    codigo,
    nombre,
    descripcion
)
VALUES
(
    'HC-QMC-SEROL-EGO',
    'HC-QMC-SEROL-EGO',
    'Panel principal que agrupa los estudios correspondientes al formulario HC-QMC-SEROL-EGO.'
),
(
    'HC-QMC-SERO-PROT',
    'HC-QMC-SERO-PROT',
    'Panel principal que agrupa los estudios correspondientes al formulario HC-QMC-SERO-PROT.'
);


-- =============================================================================
-- 24. ESTUDIOS CONOCIDOS DEL SISTEMA ACTUAL
--
-- Se registran como módulos independientes.
-- =============================================================================

INSERT INTO estudios (
    codigo,
    nombre,
    descripcion,
    modulo_frontend,
    estrategia_calculo
)
VALUES
(
    'HEMOGRAMA',
    'Hemograma',
    'Estudio hematológico con parámetros hematológicos y diferencial.',
    'hemograma',
    'HemogramaStrategy'
),
(
    'HEPATOGRAMA',
    'Hepatograma',
    'Estudio de parámetros hepáticos y bilirrubinas.',
    'hepatograma',
    'HepatogramaStrategy'
),
(
    'PERFIL_LIPIDICO',
    'Perfil Lipídico',
    'Estudio de colesterol, triglicéridos, HDL, LDL y VLDL.',
    'perfil-lipidico',
    'PerfilLipidicoStrategy'
),
(
    'PROTEINOGRAMA',
    'Proteinograma',
    'Estudio de proteínas totales, albúmina, globulina y relación A/G.',
    'proteinograma',
    'ProteinogramaStrategy'
);


-- =============================================================================
-- 25. VERSION 1 DE CONFIGURACIÓN PARA LOS ESTUDIOS CONOCIDOS
-- =============================================================================

INSERT INTO estudio_versiones (
    id_estudio,
    numero_version,
    descripcion_cambios,
    configuracion,
    activa
)
SELECT
    id_estudio,
    1,
    'Configuración inicial del estudio.',
    '{}'::jsonb,
    TRUE
FROM estudios
WHERE codigo IN (
    'HEMOGRAMA',
    'HEPATOGRAMA',
    'PERFIL_LIPIDICO',
    'PROTEINOGRAMA'
);


-- =============================================================================
-- FIN DEL SCRIPT
-- =============================================================================