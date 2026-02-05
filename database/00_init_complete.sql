/* ============================================================
   INICIALIZACIÓN COMPLETA - GOBIERNO DE DATOS CALI
   Versión: 6.0 - Actualización Febrero 2026
   Fecha: 2026-02-04

   CAMBIOS EN ESTA VERSIÓN:
   - Agregadas tablas de METADATA (funcional y técnica)
   - Campos nuevos en FACT_SERVICIO (descripcion_respuesta_esperada, documentos_daruma)
   - Campos nuevos en DIM_UBICACION (barrio, comuna, correo_elect, tipo_sede)
   - Campo nuevo en DIM_REQUISITO (detalle)
   - Campo nuevo en DIM_HERRAMIENTA_TIC (descripcion_herr)
   - Total: 12 tablas (antes 10)

   Se ejecuta automáticamente al iniciar PostgreSQL por primera vez.
============================================================ */

-- ==========================================
-- PASO 1: CREAR ESQUEMA
-- ==========================================

CREATE SCHEMA IF NOT EXISTS catalogo;
SET search_path TO catalogo, public;

-- ==========================================
-- PASO 2: CREAR TABLAS DE METADATA
-- ==========================================

CREATE TABLE IF NOT EXISTS cat_metadata_funcional (
    id_termino VARCHAR(20) PRIMARY KEY,
    termino VARCHAR(200) NOT NULL,
    definicion_negocio TEXT,
    campo_origen_matriz VARCHAR(200),
    ejemplos TEXT,
    responsable VARCHAR(100),
    reglas_negocio TEXT,
    fecha_actualizacion DATE DEFAULT CURRENT_DATE,
    version VARCHAR(10) DEFAULT '6.0',
    estado VARCHAR(20) DEFAULT 'Activo'
);

COMMENT ON TABLE cat_metadata_funcional IS 'Glosario de términos de negocio y definiciones funcionales';
COMMENT ON COLUMN cat_metadata_funcional.id_termino IS 'Identificador único del término (ej: MF001)';
COMMENT ON COLUMN cat_metadata_funcional.campo_origen_matriz IS 'Campo de la matriz de donde se extrae';

CREATE TABLE IF NOT EXISTS cat_metadata_tecnica (
    id_campo VARCHAR(20) PRIMARY KEY,
    tabla VARCHAR(100) NOT NULL,
    campo VARCHAR(100) NOT NULL,
    tipo_dato VARCHAR(50),
    longitud INTEGER,
    nulo VARCHAR(10),
    llave VARCHAR(10),
    valor_defecto VARCHAR(100),
    descripcion TEXT,
    mapeo_matriz VARCHAR(200),
    id_termino_funcional VARCHAR(20) REFERENCES cat_metadata_funcional(id_termino),
    fecha_actualizacion DATE DEFAULT CURRENT_DATE,
    version VARCHAR(10) DEFAULT '6.0',
    estado VARCHAR(20) DEFAULT 'Activo'
);

COMMENT ON TABLE cat_metadata_tecnica IS 'Diccionario de datos técnico - Documentación de campos';
COMMENT ON COLUMN cat_metadata_tecnica.id_campo IS 'Identificador único del campo (ej: MT001)';
COMMENT ON COLUMN cat_metadata_tecnica.mapeo_matriz IS 'Columna de la matriz de origen';
COMMENT ON COLUMN cat_metadata_tecnica.id_termino_funcional IS 'Relación con metadata funcional';

-- ==========================================
-- PASO 3: CREAR TABLAS DIMENSIONALES
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
    descripcion_herr TEXT,
    descripcion TEXT,
    url VARCHAR(500)
);

COMMENT ON TABLE dim_herramienta_tic IS 'Catálogo de herramientas tecnológicas';
COMMENT ON COLUMN dim_herramienta_tic.codigo IS 'Código único de la herramienta (ej: LMS)';
COMMENT ON COLUMN dim_herramienta_tic.descripcion_herr IS 'Descripción detallada de la herramienta';

CREATE TABLE IF NOT EXISTS dim_ubicacion (
    id_ubicacion SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_sede VARCHAR(200) NOT NULL,
    direccion VARCHAR(300),
    horario VARCHAR(300),
    horario_general VARCHAR(300),
    telefono VARCHAR(50),
    correo_elect VARCHAR(200),
    barrio VARCHAR(100),
    comuna VARCHAR(20),
    tipo_sede VARCHAR(50),
    id_dominio INTEGER REFERENCES dim_dominio(id_dominio),
    estado VARCHAR(50) DEFAULT 'ACTIVO'
);

COMMENT ON TABLE dim_ubicacion IS 'Catálogo de sedes y puntos de atención';
COMMENT ON COLUMN dim_ubicacion.codigo IS 'Código único de la ubicación (ej: UBI-001)';
COMMENT ON COLUMN dim_ubicacion.id_dominio IS 'Organismo responsable de la sede';
COMMENT ON COLUMN dim_ubicacion.barrio IS 'Barrio donde se ubica la sede';
COMMENT ON COLUMN dim_ubicacion.comuna IS 'Comuna de la ciudad';
COMMENT ON COLUMN dim_ubicacion.tipo_sede IS 'Tipo: Central, Regional, Punto de Atención, etc.';
COMMENT ON COLUMN dim_ubicacion.correo_elect IS 'Correo electrónico de contacto';

CREATE TABLE IF NOT EXISTS dim_requisito (
    id_requisito VARCHAR(20) PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_requisito VARCHAR(500) NOT NULL,
    detalle TEXT,
    tipo_soporte VARCHAR(50),
    categoria VARCHAR(100)
);

COMMENT ON TABLE dim_requisito IS 'Catálogo maestro de requisitos para servicios';
COMMENT ON COLUMN dim_requisito.codigo IS 'Código único del requisito (ej: R001, R002)';
COMMENT ON COLUMN dim_requisito.categoria IS 'Categoría del requisito (Registro, Información, Legal, etc.)';
COMMENT ON COLUMN dim_requisito.detalle IS 'Descripción ampliada del requisito';

CREATE TABLE IF NOT EXISTS dim_estado (
    id_estado SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE,
    nombre_estado VARCHAR(50) NOT NULL,
    descripcion TEXT
);

COMMENT ON TABLE dim_estado IS 'Catálogo de estados de servicio';
COMMENT ON COLUMN dim_estado.codigo IS 'Código único del estado (ej: ACT, INA, REV)';

-- ==========================================
-- PASO 4: CREAR TABLA DE HECHOS
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
    descripcion_respuesta_esperada TEXT,
    tiempo_respuesta TEXT,
    fundamento_legal TEXT,
    informacion_costo TEXT,
    documentos_daruma TEXT,

    volumen_mensual_promedio INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE fact_servicio IS 'Tabla de hechos - Catálogo de servicios ciudadanos';
COMMENT ON COLUMN fact_servicio.id_canal IS 'Canal principal de atención para el servicio';
COMMENT ON COLUMN fact_servicio.descripcion_respuesta_esperada IS 'Descripción del resultado o respuesta que obtiene el ciudadano';
COMMENT ON COLUMN fact_servicio.documentos_daruma IS 'Códigos de procedimientos/formatos en sistema DARUMA';

-- ==========================================
-- PASO 5: CREAR TABLAS DE RELACIÓN
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
-- PASO 6: CREAR ÍNDICES
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_servicio_nombre ON fact_servicio(nombre_servicio);
CREATE INDEX IF NOT EXISTS idx_servicio_area ON fact_servicio(id_area);
CREATE INDEX IF NOT EXISTS idx_servicio_canal ON fact_servicio(id_canal);
CREATE INDEX IF NOT EXISTS idx_area_dominio ON dim_area(id_dominio);
CREATE INDEX IF NOT EXISTS idx_ubicacion_dominio ON dim_ubicacion(id_dominio);
CREATE INDEX IF NOT EXISTS idx_ubicacion_comuna ON dim_ubicacion(comuna);
CREATE INDEX IF NOT EXISTS idx_ubicacion_tipo ON dim_ubicacion(tipo_sede);
CREATE INDEX IF NOT EXISTS idx_requisito_codigo ON dim_requisito(codigo);
CREATE INDEX IF NOT EXISTS idx_rel_req_orden ON rel_servicio_requisito(orden_presentacion);
CREATE INDEX IF NOT EXISTS idx_metadata_tec_tabla ON cat_metadata_tecnica(tabla);

COMMENT ON INDEX idx_area_dominio IS 'Índice para consultas de áreas por organismo';
COMMENT ON INDEX idx_ubicacion_dominio IS 'Índice para consultas de ubicaciones por organismo';
COMMENT ON INDEX idx_requisito_codigo IS 'Índice para búsqueda rápida por código de requisito';
COMMENT ON INDEX idx_ubicacion_comuna IS 'Índice para búsquedas por comuna';
COMMENT ON INDEX idx_metadata_tec_tabla IS 'Índice para búsquedas de metadata por tabla';

-- ==========================================
-- FIN DE INICIALIZACIÓN
-- ==========================================

\echo '✓ Esquema de base de datos v6.0 creado exitosamente'
\echo '✓ 12 tablas creadas: 2 metadata, 7 dimensionales, 1 de hechos, 2 relacionales'
\echo '✓ Índices y restricciones aplicados'
\echo '⏳ El ETL cargará los datos automáticamente...'
