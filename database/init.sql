-- =============================================================================
-- SISTEMA LIS - HOSPITAL METODISTA
-- Esquema de Base de Datos PostgreSQL — v1.1
-- MVP Fase 1: paneles HC-QMC-SEROL-EGO y HC-QMC-SERO-PROT
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS laboratorio;
SET search_path TO laboratorio, public;

-- Función utilitaria: mantiene "actualizado_en" al día en cada UPDATE
CREATE OR REPLACE FUNCTION set_actualizado_en()
RETURNS TRIGGER AS $$
BEGIN
    NEW.actualizado_en = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 1. ROLES Y PERMISOS DE USUARIO (RBAC)
CREATE TABLE roles (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(50) UNIQUE NOT NULL, -- ADMIN, BIOQUIMICO, INTERNO, MEDICO_LECTOR, JEFE_AREA
    descripcion TEXT,
    permisos JSONB NOT NULL DEFAULT '{}'::jsonb
);

INSERT INTO roles (nombre, descripcion) VALUES
('ADMIN', 'Administrador total del sistema'),
('BIOQUIMICO', 'Captura, calcula y firma resultados oficialmente'),
('INTERNO', 'Captura borradores pendientes de validacion'),
('MEDICO_LECTOR', 'Consulta resultados en modo solo lectura'),
('JEFE_AREA', 'Supervisa y aprueba enmiendas clinicas');

-- 2. USUARIOS DEL SISTEMA (Incluye foto_perfil_url)
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    id_rol INT NOT NULL REFERENCES roles(id_rol),
    ci VARCHAR(20) UNIQUE NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    hash_password VARCHAR(255) NOT NULL,
    foto_perfil_url VARCHAR(255) DEFAULT NULL, -- Campo para la imagen de perfil
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_activo BOOLEAN NOT NULL DEFAULT FALSE,
    intentos_fallidos_login INT NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    ultimo_ingreso TIMESTAMPTZ,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    eliminado_en TIMESTAMPTZ
);
CREATE TRIGGER trg_usuarios_actualizado
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
CREATE INDEX idx_usuarios_rol ON usuarios(id_rol);

-- 3. REGISTRO DE PACIENTES
CREATE TABLE pacientes (
    id_paciente SERIAL PRIMARY KEY,
    ci VARCHAR(20) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    sexo CHAR(1) NOT NULL CHECK (sexo IN ('M', 'F')),
    telefono VARCHAR(20),
    correo VARCHAR(100),
    direccion TEXT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    eliminado_en TIMESTAMPTZ
);
CREATE TRIGGER trg_pacientes_actualizado
    BEFORE UPDATE ON pacientes
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
CREATE INDEX idx_pacientes_ci ON pacientes(ci);

-- 4. CATÁLOGO DE PANELES Y PARÁMETROS DE LABORATORIO
CREATE TABLE paneles (
    id_panel SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL, -- Ej: HC-QMC-SEROL-EGO, HC-QMC-SERO-PROT
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE
);

CREATE TABLE parametros (
    id_parametro SERIAL PRIMARY KEY,
    id_panel INT NOT NULL REFERENCES paneles(id_panel),
    codigo VARCHAR(30) NOT NULL, -- Ej: HEMATOCRITO, GLOB_ROJOS, VLDL
    nombre VARCHAR(100) NOT NULL,
    unidad_medida VARCHAR(20),
    tipo_campo VARCHAR(20) NOT NULL CHECK (tipo_campo IN ('ENTRADA_MANUAL', 'CALCULADO_AUTOMATICO', 'TEXTO_LIBRE')),
    formula_referencia TEXT,
    orden_visualizacion INT NOT NULL DEFAULT 1,
    UNIQUE (id_panel, codigo)
);
CREATE INDEX idx_parametros_panel ON parametros(id_panel);

-- 5. VALORES NORMALES / RANGOS DE REFERENCIA VERSIONADOS
CREATE TABLE rangos_referencia (
    id_rango SERIAL PRIMARY KEY,
    id_parametro INT NOT NULL REFERENCES parametros(id_parametro),
    sexo CHAR(1) CHECK (sexo IN ('M', 'F', 'AMBOS')),
    edad_min_dias INT DEFAULT 0,
    edad_max_dias INT DEFAULT 36500,
    valor_min NUMERIC(12,4),
    valor_max NUMERIC(12,4),
    texto_referencia VARCHAR(150),
    vigente_desde TIMESTAMPTZ DEFAULT now(),
    vigente_hasta TIMESTAMPTZ
);
CREATE INDEX idx_rangos_parametro ON rangos_referencia(id_parametro);

-- 6. ÓRDENES DE TRABAJO Y RECEPCIÓN DE MUESTRAS
CREATE TABLE ordenes (
    id_orden SERIAL PRIMARY KEY,
    codigo_orden VARCHAR(30) UNIQUE NOT NULL,
    id_paciente INT NOT NULL REFERENCES pacientes(id_paciente),
    id_usuario_creador INT NOT NULL REFERENCES usuarios(id_usuario),
    medico_solicitante VARCHAR(150),
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now()
);
CREATE TRIGGER trg_ordenes_actualizado
    BEFORE UPDATE ON ordenes
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
CREATE INDEX idx_ordenes_paciente ON ordenes(id_paciente);

CREATE TABLE muestras (
    id_muestra SERIAL PRIMARY KEY,
    id_orden INT NOT NULL REFERENCES ordenes(id_orden),
    tipo_muestra VARCHAR(50) NOT NULL,
    estado_muestra VARCHAR(30) DEFAULT 'ACEPTADA' CHECK (estado_muestra IN ('ACEPTADA', 'RECHAZADA', 'HEMOLIZADA')),
    observaciones TEXT,
    fecha_recepcion TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_muestras_orden ON muestras(id_orden);

-- 6b. PANELES SOLICITADOS POR ORDEN (Relación 1 Orden : N Paneles)
CREATE TABLE orden_paneles (
    id_orden_panel SERIAL PRIMARY KEY,
    id_orden INT NOT NULL REFERENCES ordenes(id_orden),
    id_panel INT NOT NULL REFERENCES paneles(id_panel),
    estado VARCHAR(30) NOT NULL DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'PENDIENTE_APROBACION', 'OFICIAL', 'ANULADO')),
    id_resultado_cabecera_actual INT,
    creado_en TIMESTAMPTZ DEFAULT now(),
    actualizado_en TIMESTAMPTZ DEFAULT now(),
    UNIQUE (id_orden, id_panel)
);
CREATE TRIGGER trg_orden_paneles_actualizado
    BEFORE UPDATE ON orden_paneles
    FOR EACH ROW EXECUTE FUNCTION set_actualizado_en();
CREATE INDEX idx_orden_paneles_orden ON orden_paneles(id_orden);
CREATE INDEX idx_orden_paneles_panel ON orden_paneles(id_panel);
CREATE INDEX idx_orden_paneles_estado ON orden_paneles(estado);

-- 7. VERSIONES FIRMADAS DE RESULTADOS POR PANEL
CREATE TABLE resultados_cabecera (
    id_resultado_cabecera SERIAL PRIMARY KEY,
    id_orden_panel INT NOT NULL REFERENCES orden_paneles(id_orden_panel),
    version_numero INT NOT NULL DEFAULT 1,
    id_usuario_firma INT NOT NULL REFERENCES usuarios(id_usuario),
    motivo_enmienda TEXT,
    fecha_firma TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_panel_version UNIQUE (id_orden_panel, version_numero),
    CONSTRAINT motivo_obligatorio_en_enmienda
        CHECK (version_numero = 1 OR motivo_enmienda IS NOT NULL)
);
CREATE INDEX idx_resultados_cabecera_orden_panel ON resultados_cabecera(id_orden_panel);

ALTER TABLE orden_paneles
    ADD CONSTRAINT fk_orden_paneles_resultado_actual
    FOREIGN KEY (id_resultado_cabecera_actual)
    REFERENCES resultados_cabecera(id_resultado_cabecera);

CREATE TABLE resultados_detalle (
    id_resultado_detalle BIGSERIAL PRIMARY KEY,
    id_resultado_cabecera INT NOT NULL REFERENCES resultados_cabecera(id_resultado_cabecera),
    id_parametro INT NOT NULL REFERENCES parametros(id_parametro),
    valor_ingresado NUMERIC(12,4),
    valor_calculado NUMERIC(12,4),
    valor_texto TEXT,
    fuera_de_rango BOOLEAN DEFAULT FALSE,
    UNIQUE (id_resultado_cabecera, id_parametro)
);
CREATE INDEX idx_resultados_detalle_cabecera ON resultados_detalle(id_resultado_cabecera);
CREATE INDEX idx_resultados_detalle_parametro ON resultados_detalle(id_parametro);

-- 8. SNAPSHOT JSONB PARA HISTORIAL INMUTABLE
CREATE TABLE resultado_versiones_snapshot (
    id_snapshot BIGSERIAL PRIMARY KEY,
    id_orden_panel INT NOT NULL REFERENCES orden_paneles(id_orden_panel),
    version_numero INT NOT NULL,
    id_usuario_autor INT NOT NULL REFERENCES usuarios(id_usuario),
    snapshot_completo JSONB NOT NULL,
    motivo_cambio TEXT,
    fecha_registro TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_snapshot_orden_panel ON resultado_versiones_snapshot(id_orden_panel);

-- 9. AUDITORÍA SEPARADA (CLÍNICA Y SEGURIDAD)
CREATE TABLE bitacora_auditoria_clinica (
    id_log BIGSERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuarios(id_usuario),
    accion VARCHAR(50) NOT NULL,
    id_orden INT REFERENCES ordenes(id_orden),
    valor_anterior JSONB,
    valor_nuevo JSONB,
    fecha_hora TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_auditoria_clinica_usuario ON bitacora_auditoria_clinica(id_usuario);
CREATE INDEX idx_auditoria_clinica_orden ON bitacora_auditoria_clinica(id_orden);
CREATE INDEX idx_auditoria_clinica_fecha ON bitacora_auditoria_clinica(fecha_hora);

CREATE TABLE bitacora_seguridad (
    id_log BIGSERIAL PRIMARY KEY,
    id_usuario INT REFERENCES usuarios(id_usuario),
    evento VARCHAR(50) NOT NULL,
    ip_origen VARCHAR(45) NOT NULL,
    user_agent TEXT,
    fecha_hora TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_seguridad_usuario ON bitacora_seguridad(id_usuario);
CREATE INDEX idx_seguridad_fecha ON bitacora_seguridad(fecha_hora);

-- DATOS INICIALES DE EJEMPLO
INSERT INTO paneles (codigo, nombre) VALUES
('HC-QMC-SEROL-EGO', 'Hemograma Completo + Química Sanguínea + Serología + EGO'),
('HC-QMC-SERO-PROT', 'Hemograma Completo + Química Sanguínea + Serología + Proteinograma');