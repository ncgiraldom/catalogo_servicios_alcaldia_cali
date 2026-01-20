/* MIGRACIÓN: Agregar dim_canal y actualizar fact_servicio
   Versión: 4.1 - Alineación con artefactos
   Fecha: 2026-01-19
*/

SET search_path TO catalogo, public;

-- ==========================================
-- 1. CREAR TABLA DIM_CANAL (FALTANTE)
-- ==========================================

CREATE TABLE IF NOT EXISTS dim_canal (
    id_canal SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre_canal VARCHAR(200) NOT NULL,
    descripcion TEXT
);

COMMENT ON TABLE dim_canal IS 'Catálogo de canales de atención al ciudadano';

-- ==========================================
-- 2. AGREGAR CAMPOS FALTANTES EN DIM_AREA
-- ==========================================

ALTER TABLE dim_area ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;

COMMENT ON COLUMN dim_area.codigo IS 'Código único del área (ej: DATIC-INN)';

-- ==========================================
-- 3. AGREGAR CAMPOS FALTANTES EN DIM_HERRAMIENTA_TIC
-- ==========================================

ALTER TABLE dim_herramienta_tic ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;
ALTER TABLE dim_herramienta_tic ADD COLUMN IF NOT EXISTS descripcion TEXT;
ALTER TABLE dim_herramienta_tic RENAME COLUMN url_acceso TO url;

COMMENT ON COLUMN dim_herramienta_tic.codigo IS 'Código único de la herramienta (ej: LMS)';

-- ==========================================
-- 4. AGREGAR CAMPOS FALTANTES EN DIM_UBICACION
-- ==========================================

ALTER TABLE dim_ubicacion ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;
ALTER TABLE dim_ubicacion ADD COLUMN IF NOT EXISTS telefono VARCHAR(50);
ALTER TABLE dim_ubicacion ADD COLUMN IF NOT EXISTS id_dominio INTEGER REFERENCES dim_dominio(id_dominio);
ALTER TABLE dim_ubicacion ADD COLUMN IF NOT EXISTS estado VARCHAR(50) DEFAULT 'Activo';
ALTER TABLE dim_ubicacion RENAME COLUMN horario TO horario_general;

COMMENT ON COLUMN dim_ubicacion.codigo IS 'Código único de la ubicación (ej: UBI-001)';
COMMENT ON COLUMN dim_ubicacion.id_dominio IS 'Organismo responsable de la sede';

-- ==========================================
-- 5. AGREGAR CAMPOS FALTANTES EN DIM_ESTADO
-- ==========================================

ALTER TABLE dim_estado ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;
ALTER TABLE dim_estado ADD COLUMN IF NOT EXISTS descripcion TEXT;

COMMENT ON COLUMN dim_estado.codigo IS 'Código único del estado (ej: ACT, INA, REV)';

-- ==========================================
-- 6. ACTUALIZAR FACT_SERVICIO CON CAMPO id_canal
-- ==========================================

ALTER TABLE fact_servicio ADD COLUMN IF NOT EXISTS id_canal INTEGER REFERENCES dim_canal(id_canal);

COMMENT ON COLUMN fact_servicio.id_canal IS 'Canal principal de atención para el servicio';

-- ==========================================
-- 7. CREAR ÍNDICES ADICIONALES
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_area_dominio ON dim_area(id_dominio);
CREATE INDEX IF NOT EXISTS idx_ubicacion_dominio ON dim_ubicacion(id_dominio);
CREATE INDEX IF NOT EXISTS idx_servicio_area ON fact_servicio(id_area);
CREATE INDEX IF NOT EXISTS idx_servicio_canal ON fact_servicio(id_canal);

COMMENT ON INDEX idx_area_dominio IS 'Índice para consultas de áreas por organismo';
COMMENT ON INDEX idx_ubicacion_dominio IS 'Índice para consultas de ubicaciones por organismo';
