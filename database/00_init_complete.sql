/* ============================================================
   INICIALIZACIÓN COMPLETA - GOBIERNO DE DATOS CALI
   Versión: 5.0 - Consolidado para despliegue automático
   Fecha: 2026-01-20

   Este archivo consolida:
   - Creación del esquema y tablas (01_schema_ddl.sql)
   - Agregado de dim_canal y campos adicionales (02_migration_add_canal.sql)
   - Actualización de dim_requisito (03_migration_update_requisito.sql)

   Se ejecuta automáticamente al iniciar PostgreSQL por primera vez.
============================================================ */

-- ==========================================
-- PASO 1: CREAR ESQUEMA
-- ==========================================

CREATE SCHEMA IF NOT EXISTS catalogo;
SET search_path TO catalogo, public;

-- ==========================================
-- PASO 2: CREAR TABLAS DIMENSIONALES
-- ==========================================

CREATE TABLE IF NOT EXISTS dim_dominio (
    id_dominio SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_dominio VARCHAR(200) NOT NULL,
    sigla VARCHAR(10)
);

COMMENT ON TABLE dim_dominio IS 'Catálogo de organismos de la Alcaldía de Cali';
COMMENT ON COLUMN dim_dominio.codigo IS 'Código único del organismo (ej: DOM-001)';

CREATE TABLE IF NOT EXISTS dim_area (
    id_area SERIAL PRIMARY KEY,
    id_dominio INTEGER REFERENCES dim_dominio(id_dominio),
    codigo VARCHAR(20) UNIQUE,
    nombre_area VARCHAR(200) NOT NULL
);

COMMENT ON TABLE dim_area IS 'Catálogo de áreas y subdirecciones';
COMMENT ON COLUMN dim_area.codigo IS 'Código único del área (ej: DATIC-INN)';

CREATE TABLE IF NOT EXISTS dim_canal (
    id_canal SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre_canal VARCHAR(200) NOT NULL,
    descripcion TEXT
);

COMMENT ON TABLE dim_canal IS 'Catálogo de canales de atención al ciudadano';

CREATE TABLE IF NOT EXISTS dim_herramienta_tic (
    id_herramienta SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_herramienta VARCHAR(100) NOT NULL,
    descripcion TEXT,
    url VARCHAR(500)
);

COMMENT ON TABLE dim_herramienta_tic IS 'Catálogo de herramientas tecnológicas';
COMMENT ON COLUMN dim_herramienta_tic.codigo IS 'Código único de la herramienta (ej: LMS)';

CREATE TABLE IF NOT EXISTS dim_ubicacion (
    id_ubicacion SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_sede VARCHAR(200) NOT NULL,
    direccion VARCHAR(300),
    horario_general VARCHAR(300),
    telefono VARCHAR(50),
    id_dominio INTEGER REFERENCES dim_dominio(id_dominio),
    estado VARCHAR(50) DEFAULT 'Activo'
);

COMMENT ON TABLE dim_ubicacion IS 'Catálogo de sedes y puntos de atención';
COMMENT ON COLUMN dim_ubicacion.codigo IS 'Código único de la ubicación (ej: UBI-001)';
COMMENT ON COLUMN dim_ubicacion.id_dominio IS 'Organismo responsable de la sede';

CREATE TABLE IF NOT EXISTS dim_requisito (
    id_requisito VARCHAR(20) PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_requisito VARCHAR(500) NOT NULL,
    tipo_soporte VARCHAR(50),
    categoria VARCHAR(100)
);

COMMENT ON TABLE dim_requisito IS 'Catálogo maestro de requisitos para servicios';
COMMENT ON COLUMN dim_requisito.codigo IS 'Código único del requisito (ej: R001, R002)';
COMMENT ON COLUMN dim_requisito.categoria IS 'Categoría del requisito (Registro, Información, Legal, etc.)';

CREATE TABLE IF NOT EXISTS dim_estado (
    id_estado SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_estado VARCHAR(50) NOT NULL,
    descripcion TEXT
);

COMMENT ON TABLE dim_estado IS 'Catálogo de estados de servicio';
COMMENT ON COLUMN dim_estado.codigo IS 'Código único del estado (ej: ACT, INA, REV)';

-- ==========================================
-- PASO 3: CREAR TABLA DE HECHOS
-- ==========================================

CREATE TABLE IF NOT EXISTS fact_servicio (
    id_servicio SERIAL PRIMARY KEY,
    codigo_servicio VARCHAR(20) UNIQUE NOT NULL,

    -- Relaciones con dimensiones
    id_dominio INTEGER REFERENCES dim_dominio(id_dominio),
    id_area INTEGER REFERENCES dim_area(id_area),
    id_herramienta_tic INTEGER REFERENCES dim_herramienta_tic(id_herramienta),
    id_estado INTEGER REFERENCES dim_estado(id_estado),
    id_canal INTEGER REFERENCES dim_canal(id_canal),

    -- Atributos del servicio
    nombre_servicio VARCHAR(500) NOT NULL,
    descripcion TEXT,
    proposito TEXT,
    dirigido_a TEXT,
    tiempo_respuesta VARCHAR(100),
    fundamento_legal TEXT,
    informacion_costo TEXT,

    volumen_mensual_promedio INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE fact_servicio IS 'Tabla de hechos - Catálogo de servicios ciudadanos';
COMMENT ON COLUMN fact_servicio.id_canal IS 'Canal principal de atención para el servicio';

-- ==========================================
-- PASO 4: CREAR TABLAS DE RELACIÓN
-- ==========================================

CREATE TABLE IF NOT EXISTS rel_servicio_requisito (
    id_rel SERIAL PRIMARY KEY,
    id_servicio INTEGER NOT NULL REFERENCES fact_servicio(id_servicio) ON DELETE CASCADE,
    id_requisito VARCHAR(20) NOT NULL REFERENCES dim_requisito(id_requisito) ON DELETE RESTRICT,
    codigo_servicio VARCHAR(20),
    codigo_requisito VARCHAR(20),
    es_obligatorio BOOLEAN DEFAULT TRUE,
    observacion TEXT,
    orden_presentacion INTEGER,

    CONSTRAINT uk_servicio_requisito UNIQUE (id_servicio, id_requisito)
);

COMMENT ON TABLE rel_servicio_requisito IS 'Relación N:M entre servicios y requisitos';
COMMENT ON COLUMN rel_servicio_requisito.codigo_servicio IS 'Código desnormalizado para consultas rápidas';
COMMENT ON COLUMN rel_servicio_requisito.codigo_requisito IS 'Código desnormalizado para consultas rápidas';
COMMENT ON COLUMN rel_servicio_requisito.orden_presentacion IS 'Orden en que se debe presentar el requisito';

CREATE TABLE IF NOT EXISTS rel_servicio_ubicacion (
    id_rel SERIAL PRIMARY KEY,
    id_servicio INTEGER NOT NULL REFERENCES fact_servicio(id_servicio) ON DELETE CASCADE,
    id_ubicacion INTEGER NOT NULL REFERENCES dim_ubicacion(id_ubicacion) ON DELETE RESTRICT,
    codigo_servicio VARCHAR(20),
    es_sede_principal BOOLEAN DEFAULT TRUE,

    CONSTRAINT uk_servicio_ubicacion UNIQUE (id_servicio, id_ubicacion)
);

COMMENT ON TABLE rel_servicio_ubicacion IS 'Relación N:M entre servicios y ubicaciones';
COMMENT ON COLUMN rel_servicio_ubicacion.codigo_servicio IS 'Código desnormalizado para consultas rápidas';

-- ==========================================
-- PASO 5: CREAR ÍNDICES
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_servicio_nombre ON fact_servicio(nombre_servicio);
CREATE INDEX IF NOT EXISTS idx_servicio_area ON fact_servicio(id_area);
CREATE INDEX IF NOT EXISTS idx_servicio_canal ON fact_servicio(id_canal);
CREATE INDEX IF NOT EXISTS idx_area_dominio ON dim_area(id_dominio);
CREATE INDEX IF NOT EXISTS idx_ubicacion_dominio ON dim_ubicacion(id_dominio);
CREATE INDEX IF NOT EXISTS idx_requisito_codigo ON dim_requisito(codigo);
CREATE INDEX IF NOT EXISTS idx_rel_req_orden ON rel_servicio_requisito(orden_presentacion);

COMMENT ON INDEX idx_area_dominio IS 'Índice para consultas de áreas por organismo';
COMMENT ON INDEX idx_ubicacion_dominio IS 'Índice para consultas de ubicaciones por organismo';
COMMENT ON INDEX idx_requisito_codigo IS 'Índice para búsqueda rápida por código de requisito';

-- ==========================================
-- FIN DE INICIALIZACIÓN
-- ==========================================

\echo '✓ Esquema de base de datos creado exitosamente'
\echo '✓ 10 tablas creadas: 7 dimensionales, 1 de hechos, 2 relacionales'
\echo '✓ Índices y restricciones aplicados'
\echo '⏳ El ETL cargará los datos automáticamente...'
