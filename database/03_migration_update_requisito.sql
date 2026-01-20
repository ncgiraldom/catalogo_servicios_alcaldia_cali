/* MIGRACIÓN: Actualizar dim_requisito con campos faltantes
   Versión: 4.2 - Alineación con artefactos
   Fecha: 2026-01-20
*/

SET search_path TO catalogo, public;

-- ==========================================
-- 1. AGREGAR CAMPOS FALTANTES EN DIM_REQUISITO
-- ==========================================

ALTER TABLE dim_requisito ADD COLUMN IF NOT EXISTS codigo VARCHAR(20) UNIQUE;
ALTER TABLE dim_requisito ADD COLUMN IF NOT EXISTS categoria VARCHAR(100);

COMMENT ON COLUMN dim_requisito.codigo IS 'Código único del requisito (ej: R001, R002)';
COMMENT ON COLUMN dim_requisito.categoria IS 'Categoría del requisito (Registro, Información, Legal, etc.)';

-- ==========================================
-- 2. CREAR ÍNDICE PARA CÓDIGO
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_requisito_codigo ON dim_requisito(codigo);

COMMENT ON INDEX idx_requisito_codigo IS 'Índice para búsqueda rápida por código de requisito';
