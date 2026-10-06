-- =============================================================================
-- SEED: Catálogo de los 7 estudios reales de HC-QMC-SEROL-EGO y HC-QMC-SERO-PROT
-- Extraído celda por celda del Excel original 1__FORMATO_CENTRAL_2026.xlsx
--
-- PENDIENTE DE VALIDAR CON LA DOCTORA (no se asumió nada, queda NULL):
--   - GOT/AST y GPT/ALT: rango distinto entre HC-QMC-SEROL-EGO ("hasta 40"
--     ambos) y HC-QMC-SERO-PROT (GOT "hasta 37", GPT "hasta 45"). Se deja en
--     NULL hasta confirmar cuál es el correcto.
--   - Cayados (Hemograma): el Excel no tiene un rango de referencia visible.
-- =============================================================================

SET search_path TO laboratorio, public;

-- -----------------------------------------------------------------------------
-- 1. ESTUDIOS
-- -----------------------------------------------------------------------------
INSERT INTO estudios (codigo, nombre, descripcion, modulo_frontend, estrategia_calculo) VALUES
('HEMOGRAMA',         'Hemograma Completo',  'Serie roja, serie blanca y diferencial leucocitario.', 'hemograma',         'HemogramaStrategy'),
('QUIMICA_SANGUINEA',  'Química Sanguínea',   'Glicemia, función renal y HbA1c. Sin fórmulas, solo validación de rango.', 'quimica-sanguinea', NULL),
('ELECTROLITOS',       'Electrolitos',        'Sodio, Potasio, Cloro, Calcio, Magnesio, Fósforo. Sin fórmulas.', 'electrolitos',      NULL),
('PERFIL_LIPIDICO',    'Perfil Lipídico',     'Colesterol, Triglicéridos, HDL, LDL, VLDL (fórmula de Friedewald).', 'perfil-lipidico',   'PerfilLipidicoStrategy'),
('HEPATOGRAMA',        'Hepatograma',         'Bilirrubinas, GPT/ALT, GOT/AST, Fosfatasa Alcalina.', 'hepatograma',       'HepatogramaStrategy'),
('PROTEINOGRAMA',      'Proteinograma',       'Proteínas Totales, Albúmina, Globulina, Relación A/G.', 'proteinograma',     'ProteinogramaStrategy'),
('EGO',                'Examen General de Orina', 'Análisis físico, químico y microscópico. Mayormente cualitativo.', 'ego',           NULL)
ON CONFLICT (codigo) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 2. VERSIÓN 1 DE CADA ESTUDIO
-- -----------------------------------------------------------------------------
INSERT INTO estudio_versiones (id_estudio, numero_version, descripcion_cambios, configuracion, activa)
SELECT id_estudio, 1, 'Configuración inicial extraída del Excel original.', '{}'::jsonb, TRUE
FROM estudios
WHERE codigo IN ('HEMOGRAMA','QUIMICA_SANGUINEA','ELECTROLITOS','PERFIL_LIPIDICO','HEPATOGRAMA','PROTEINOGRAMA','EGO')
ON CONFLICT (id_estudio, numero_version) DO NOTHING;

-- -----------------------------------------------------------------------------
-- 3. PARAMETROS + RANGOS DE REFERENCIA
--
-- Patrón: función auxiliar inline vía CTE para resolver id_estudio_version,
-- insertar el parámetro, y encadenar el rango de referencia.
-- -----------------------------------------------------------------------------

DO $$
DECLARE
    v_hemograma      BIGINT;
    v_quimica        BIGINT;
    v_electrolitos   BIGINT;
    v_lipidico       BIGINT;
    v_hepatograma    BIGINT;
    v_proteinograma  BIGINT;
    v_ego            BIGINT;
    p_id             BIGINT;
BEGIN
    SELECT ev.id_estudio_version INTO v_hemograma     FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='HEMOGRAMA' AND ev.numero_version=1;
    SELECT ev.id_estudio_version INTO v_quimica       FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='QUIMICA_SANGUINEA' AND ev.numero_version=1;
    SELECT ev.id_estudio_version INTO v_electrolitos  FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='ELECTROLITOS' AND ev.numero_version=1;
    SELECT ev.id_estudio_version INTO v_lipidico      FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='PERFIL_LIPIDICO' AND ev.numero_version=1;
    SELECT ev.id_estudio_version INTO v_hepatograma   FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='HEPATOGRAMA' AND ev.numero_version=1;
    SELECT ev.id_estudio_version INTO v_proteinograma FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='PROTEINOGRAMA' AND ev.numero_version=1;
    SELECT ev.id_estudio_version INTO v_ego           FROM estudio_versiones ev JOIN estudios e ON e.id_estudio=ev.id_estudio WHERE e.codigo='EGO' AND ev.numero_version=1;

    -- ===================== HEMOGRAMA =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, unidad_medida, formula_codigo, orden_visualizacion, obligatorio) VALUES
    (v_hemograma, 'GLOBULOS_ROJOS',   'Glóbulos Rojos',   'CALCULADO_AUTOMATICO', 'DECIMAL', 'mm3',   '107000 * hematocrito', 1, FALSE),
    (v_hemograma, 'GLOBULOS_BLANCOS', 'Glóbulos Blancos', 'ENTRADA_MANUAL',       'DECIMAL', 'mm3',   NULL, 2, TRUE),
    (v_hemograma, 'HEMATOCRITO',      'Hematocrito',      'ENTRADA_MANUAL',       'DECIMAL', '%',     NULL, 3, TRUE),
    (v_hemograma, 'HEMOGLOBINA',      'Hemoglobina',      'CALCULADO_AUTOMATICO', 'DECIMAL', 'g/dL',  '0.32 * hematocrito', 4, FALSE),
    (v_hemograma, 'VES',              'V.E.S.',           'ENTRADA_MANUAL',       'DECIMAL', 'mm/hra',NULL, 5, FALSE),
    (v_hemograma, 'PLAQUETAS',        'Plaquetas',        'ENTRADA_MANUAL',       'DECIMAL', 'xmm3',  NULL, 6, TRUE),
    (v_hemograma, 'SEGMENTADOS',      'Segmentados',      'ENTRADA_MANUAL',       'DECIMAL', '%',     NULL, 7, TRUE),
    (v_hemograma, 'LINFOCITOS',       'Linfocitos',       'ENTRADA_MANUAL',       'DECIMAL', '%',     NULL, 8, TRUE),
    (v_hemograma, 'EOSINOFILOS',      'Eosinófilos',      'ENTRADA_MANUAL',       'DECIMAL', '%',     NULL, 9, TRUE),
    (v_hemograma, 'MONOCITOS',        'Monocitos',        'ENTRADA_MANUAL',       'DECIMAL', '%',     NULL, 10, TRUE),
    (v_hemograma, 'CAYADOS',          'Cayados',          'ENTRADA_MANUAL',       'DECIMAL', '%',     NULL, 11, TRUE),
    (v_hemograma, 'SEGMENTADOS_ABS',  'Segmentados (absoluto)', 'CALCULADO_AUTOMATICO', 'DECIMAL', 'mm3', 'segmentados * globulos_blancos', 12, FALSE),
    (v_hemograma, 'LINFOCITOS_ABS',   'Linfocitos (absoluto)',  'CALCULADO_AUTOMATICO', 'DECIMAL', 'mm3', 'linfocitos * globulos_blancos', 13, FALSE),
    (v_hemograma, 'EOSINOFILOS_ABS',  'Eosinófilos (absoluto)', 'CALCULADO_AUTOMATICO', 'DECIMAL', 'mm3', 'eosinofilos * globulos_blancos', 14, FALSE),
    (v_hemograma, 'MONOCITOS_ABS',    'Monocitos (absoluto)',   'CALCULADO_AUTOMATICO', 'DECIMAL', 'mm3', 'monocitos * globulos_blancos', 15, FALSE),
    (v_hemograma, 'CAYADOS_ABS',      'Cayados (absoluto)',     'CALCULADO_AUTOMATICO', 'DECIMAL', 'mm3', 'cayados * globulos_blancos', 16, FALSE);

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='GLOBULOS_ROJOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad, referencia_texto) VALUES
    (p_id, 'M', 5400000, 6300000, 'mm3', '5,4 - 6,3 x 10^6'), (p_id, 'F', 4900000, 5700000, 'mm3', '4,9 - 5,7 x 10^6');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='GLOBULOS_BLANCOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES (p_id, NULL, 5000, 10000, 'mm3');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='HEMATOCRITO';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES
    (p_id, 'M', 48, 58, '%'), (p_id, 'F', 44, 54, '%');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='HEMOGLOBINA';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES
    (p_id, 'M', 16, 18, 'g/dL'), (p_id, 'F', 14, 16, 'g/dL');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='VES';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES
    (p_id, 'M', 2, 7, 'mm/hra'), (p_id, 'F', 3, 10, 'mm/hra');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='PLAQUETAS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES (p_id, NULL, 150000, 400000, 'xmm3');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='SEGMENTADOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES (p_id, NULL, 0.55, 0.70, '%');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='LINFOCITOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES (p_id, NULL, 0.25, 0.40, '%');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='EOSINOFILOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES (p_id, NULL, 0.00, 0.04, '%');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='MONOCITOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad) VALUES (p_id, NULL, 0.02, 0.08, '%');

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hemograma AND codigo='CAYADOS';
    INSERT INTO rangos_referencia (id_parametro, sexo, limite_inferior, limite_superior, unidad, observaciones)
    VALUES (p_id, NULL, NULL, NULL, '%', 'PENDIENTE: el Excel no tiene un rango visible para Cayados. Confirmar con la doctora.');

    -- ===================== QUIMICA SANGUINEA =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, unidad_medida, orden_visualizacion, obligatorio) VALUES
    (v_quimica, 'GLICEMIA',     'Glicemia',     'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 1, TRUE),
    (v_quimica, 'CREATININA',   'Creatinina',   'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 2, TRUE),
    (v_quimica, 'NUS',          'NUS',          'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 3, TRUE),
    (v_quimica, 'UREA',         'Urea',         'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 4, TRUE),
    (v_quimica, 'ACIDO_URICO',  'Ácido Úrico',  'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 5, TRUE),
    (v_quimica, 'HBA1C',        'HbA1c',        'ENTRADA_MANUAL', 'DECIMAL', '%',     6, TRUE);

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_quimica AND codigo='GLICEMIA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 70, 110, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_quimica AND codigo='CREATININA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 0.7, 1.4, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_quimica AND codigo='NUS';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 7.0, 18, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_quimica AND codigo='UREA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 17, 42, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_quimica AND codigo='ACIDO_URICO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 2.5, 7.0, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_quimica AND codigo='HBA1C';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 6.0, 8.3, '%');

    -- ===================== ELECTROLITOS =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, unidad_medida, orden_visualizacion, obligatorio) VALUES
    (v_electrolitos, 'SODIO',     'Sodio',     'ENTRADA_MANUAL', 'DECIMAL', 'mEq/L', 1, TRUE),
    (v_electrolitos, 'POTASIO',   'Potasio',   'ENTRADA_MANUAL', 'DECIMAL', 'mEq/L', 2, TRUE),
    (v_electrolitos, 'CLORO',     'Cloro',     'ENTRADA_MANUAL', 'DECIMAL', 'mEq/L', 3, TRUE),
    (v_electrolitos, 'CALCIO',    'Calcio',    'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 4, TRUE),
    (v_electrolitos, 'MAGNESIO',  'Magnesio',  'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 5, TRUE),
    (v_electrolitos, 'FOSFORO',   'Fósforo',   'ENTRADA_MANUAL', 'DECIMAL', 'mg/dl', 6, TRUE);

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_electrolitos AND codigo='SODIO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 135, 155, 'mEq/L');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_electrolitos AND codigo='POTASIO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 3.5, 5.3, 'mEq/L');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_electrolitos AND codigo='CLORO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 98, 106, 'mEq/L');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_electrolitos AND codigo='CALCIO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 8.5, 10.5, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_electrolitos AND codigo='MAGNESIO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 1.7, 2.5, 'mg/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_electrolitos AND codigo='FOSFORO';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 2.5, 5.0, 'mg/dl');

    -- ===================== PERFIL LIPIDICO =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, unidad_medida, formula_codigo, orden_visualizacion, obligatorio) VALUES
    (v_lipidico, 'COLESTEROL',    'Colesterol',    'ENTRADA_MANUAL',       'DECIMAL', 'mg/dl', NULL, 1, TRUE),
    (v_lipidico, 'TRIGLICERIDOS', 'Triglicéridos', 'ENTRADA_MANUAL',       'DECIMAL', 'mg/dl', NULL, 2, TRUE),
    (v_lipidico, 'HDL',           'HDL',           'ENTRADA_MANUAL',       'DECIMAL', 'mg/dl', NULL, 3, TRUE),
    (v_lipidico, 'VLDL',          'VLDL',          'CALCULADO_AUTOMATICO', 'DECIMAL', 'mg/dl', 'trigliceridos / 5', 4, FALSE),
    (v_lipidico, 'LDL',           'LDL',           'CALCULADO_AUTOMATICO', 'DECIMAL', 'mg/dl', 'colesterol - hdl - vldl', 5, FALSE);

    -- ===================== HEPATOGRAMA =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, unidad_medida, formula_codigo, orden_visualizacion, obligatorio) VALUES
    (v_hepatograma, 'BILIRRUBINA_TOTAL',     'Bilirrubina Total',     'ENTRADA_MANUAL',       'DECIMAL', 'mg/dL', NULL, 1, TRUE),
    (v_hepatograma, 'BILIRRUBINA_DIRECTA',   'Bilirrubina Directa',   'ENTRADA_MANUAL',       'DECIMAL', 'mg/dL', NULL, 2, TRUE),
    (v_hepatograma, 'BILIRRUBINA_INDIRECTA', 'Bilirrubina Indirecta', 'CALCULADO_AUTOMATICO', 'DECIMAL', 'mg/dL', 'bilirrubina_total - bilirrubina_directa', 3, FALSE),
    (v_hepatograma, 'GPT_ALT',               'GPT (ALT)',             'ENTRADA_MANUAL',       'DECIMAL', 'UI/L',  NULL, 4, TRUE),
    (v_hepatograma, 'GOT_AST',               'GOT (AST)',             'ENTRADA_MANUAL',       'DECIMAL', 'UI/L',  NULL, 5, TRUE),
    (v_hepatograma, 'F_ALCALINA',            'Fosfatasa Alcalina',    'ENTRADA_MANUAL',       'DECIMAL', 'U/L',   NULL, 6, FALSE);

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hepatograma AND codigo='BILIRRUBINA_TOTAL';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad, referencia_texto) VALUES (p_id, NULL, 1.1, 'mg/dL', 'Hasta 1,1');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hepatograma AND codigo='BILIRRUBINA_DIRECTA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad, referencia_texto) VALUES (p_id, NULL, 0.3, 'mg/dL', 'Hasta 0,3');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hepatograma AND codigo='BILIRRUBINA_INDIRECTA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad, referencia_texto) VALUES (p_id, NULL, 0.8, 'mg/dL', 'Hasta 0,8');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hepatograma AND codigo='GPT_ALT';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad, observaciones)
    VALUES (p_id, NULL, NULL, 'UI/L', 'PENDIENTE: HC-QMC-SEROL-EGO dice "hasta 40", HC-QMC-SERO-PROT dice "hasta 45". Confirmar con la doctora.');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hepatograma AND codigo='GOT_AST';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad, observaciones)
    VALUES (p_id, NULL, NULL, 'UI/L', 'PENDIENTE: HC-QMC-SEROL-EGO dice "hasta 40", HC-QMC-SERO-PROT dice "hasta 37". Confirmar con la doctora.');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_hepatograma AND codigo='F_ALCALINA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 98, 279, 'U/L');

    -- ===================== PROTEINOGRAMA =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, unidad_medida, formula_codigo, orden_visualizacion, obligatorio) VALUES
    (v_proteinograma, 'PROTEINAS_TOTALES', 'Proteínas Totales', 'ENTRADA_MANUAL',       'DECIMAL', 'g/dl', NULL, 1, TRUE),
    (v_proteinograma, 'ALBUMINA',          'Albúmina',          'ENTRADA_MANUAL',       'DECIMAL', 'g/dl', NULL, 2, TRUE),
    (v_proteinograma, 'GLOBULINA',         'Globulina',         'CALCULADO_AUTOMATICO', 'DECIMAL', 'g/dl', 'proteinas_totales - albumina', 3, FALSE),
    (v_proteinograma, 'RELACION_AG',       'Relación A/G',      'CALCULADO_AUTOMATICO', 'DECIMAL', NULL,   'albumina / globulina', 4, FALSE);

    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_proteinograma AND codigo='PROTEINAS_TOTALES';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 6.2, 8.5, 'g/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_proteinograma AND codigo='ALBUMINA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 3.5, 5.3, 'g/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_proteinograma AND codigo='GLOBULINA';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 2.0, 3.5, 'g/dl');
    SELECT id_parametro INTO p_id FROM parametros WHERE id_estudio_version=v_proteinograma AND codigo='RELACION_AG';
    INSERT INTO rangos_referencia (id_parametro, limite_inferior, limite_superior, unidad) VALUES (p_id, 1.2, 2.2, NULL);

    -- ===================== EGO (cualitativo, sin rangos numéricos) =====================
    INSERT INTO parametros (id_estudio_version, codigo, nombre, tipo_campo, tipo_dato, orden_visualizacion, obligatorio) VALUES
    (v_ego, 'CANTIDAD',    'Cantidad',             'TEXTO',     'TEXTO', 1, FALSE),
    (v_ego, 'COLOR',       'Color',                'TEXTO',     'TEXTO', 2, FALSE),
    (v_ego, 'ASPECTO',     'Aspecto',              'TEXTO',     'TEXTO', 3, FALSE),
    (v_ego, 'ESPUMA',      'Espuma',               'TEXTO',     'TEXTO', 4, FALSE),
    (v_ego, 'PROTEINAS',   'Proteínas',            'SELECCION', 'TEXTO', 5, FALSE),
    (v_ego, 'GLUCOSA',     'Glucosa',              'SELECCION', 'TEXTO', 6, FALSE),
    (v_ego, 'CETONAS',     'Cetonas',              'SELECCION', 'TEXTO', 7, FALSE),
    (v_ego, 'ESTERASA',    'Esterasa Leucocitaria','SELECCION', 'TEXTO', 8, FALSE),
    (v_ego, 'NITRITOS',    'Nitritos',             'SELECCION', 'TEXTO', 9, FALSE),
    (v_ego, 'PIGM_BILIRRUBINA', 'Pigm. Bilirrubina','SELECCION','TEXTO', 10, FALSE),
    (v_ego, 'UROBILINOGENO','Urobilinógeno',       'SELECCION', 'TEXTO', 11, FALSE),
    (v_ego, 'SANGRE',      'Sangre',               'SELECCION', 'TEXTO', 12, FALSE),
    (v_ego, 'HEMATIES',    'Hematíes',             'ENTRADA_MANUAL', 'TEXTO', 13, FALSE),
    (v_ego, 'LEUCOCITOS',  'Leucocitos',           'ENTRADA_MANUAL', 'TEXTO', 14, FALSE),
    (v_ego, 'C_EPITELIALES','Células Epiteliales', 'ENTRADA_MANUAL', 'TEXTO', 15, FALSE),
    (v_ego, 'CRISTALES',   'Cristales',            'TEXTO',     'TEXTO', 16, FALSE),
    (v_ego, 'BACTERIAS',   'Bacterias',            'TEXTO',     'TEXTO', 17, FALSE),
    (v_ego, 'CILINDROS',   'Cilindros',            'TEXTO',     'TEXTO', 18, FALSE),
    (v_ego, 'OTROS',       'Otros',                'TEXTO',     'TEXTO', 19, FALSE);

END $$;

-- -----------------------------------------------------------------------------
-- 4. PANEL -> ESTUDIOS (lo que hace que al elegir la plantilla se marquen solos)
-- -----------------------------------------------------------------------------
INSERT INTO panel_estudios (id_panel, id_estudio, orden_visualizacion)
SELECT pan.id_panel, est.id_estudio, datos.orden
FROM (VALUES
    ('HC-QMC-SEROL-EGO', 'HEMOGRAMA', 1),
    ('HC-QMC-SEROL-EGO', 'QUIMICA_SANGUINEA', 2),
    ('HC-QMC-SEROL-EGO', 'ELECTROLITOS', 3),
    ('HC-QMC-SEROL-EGO', 'PERFIL_LIPIDICO', 4),
    ('HC-QMC-SEROL-EGO', 'HEPATOGRAMA', 5),
    ('HC-QMC-SEROL-EGO', 'EGO', 6),
    ('HC-QMC-SERO-PROT', 'HEMOGRAMA', 1),
    ('HC-QMC-SERO-PROT', 'QUIMICA_SANGUINEA', 2),
    ('HC-QMC-SERO-PROT', 'ELECTROLITOS', 3),
    ('HC-QMC-SERO-PROT', 'HEPATOGRAMA', 4),
    ('HC-QMC-SERO-PROT', 'PROTEINOGRAMA', 5)
) AS datos(codigo_panel, codigo_estudio, orden)
JOIN paneles pan ON pan.codigo = datos.codigo_panel
JOIN estudios est ON est.codigo = datos.codigo_estudio
ON CONFLICT (id_panel, id_estudio) DO NOTHING;