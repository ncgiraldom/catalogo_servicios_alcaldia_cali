import pandas as pd
import os
from sqlalchemy import create_engine, text
import time
import numpy as np

# --- CONFIGURACIÓN ---
DB_USER = os.getenv('DB_USER', 'admin_datos')
DB_PASS = os.getenv('DB_PASS', 'cali_segura_2025')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'catalogo_cali')

# Archivos de entrada actualizados
INPUT_MATRIZ = '/app/data/input/matriz_servicios_consolidada_final.xlsx'
INPUT_ARTEFACTOS = '/app/data/input/Artefactos_Consolidado_feb2026.xlsx'

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

def clean_text(text):
    """Limpia y normaliza texto"""
    if pd.isna(text) or str(text).lower() in ['nan', 'no registra', 'sin definir', '', 'sin información']:
        return None
    return str(text).strip()

def load_metadata_funcional(engine, file_path):
    """Carga metadata funcional desde artefactos"""
    print("📚 Cargando METADATA FUNCIONAL...")
    try:
        df = pd.read_excel(file_path, sheet_name='CAT_METADATA_FUNCIONAL', skiprows=2)
        df = df.dropna(subset=['ID_TERMINO'])

        # Renombrar columnas
        df.columns = [
            'id_termino', 'termino', 'definicion_negocio', 'campo_origen_matriz',
            'ejemplos', 'responsable', 'reglas_negocio', 'categoria',
            'fecha_actualizacion', 'version', 'estado'
        ]

        df.to_sql('cat_metadata_funcional', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(df)} términos funcionales cargados")
        return True
    except Exception as e:
        print(f"   ⚠️  Error cargando metadata funcional: {e}")
        return False

def load_metadata_tecnica(engine, file_path):
    """Carga metadata técnica desde artefactos"""
    print("🔧 Cargando METADATA TÉCNICA...")
    try:
        df = pd.read_excel(file_path, sheet_name='CAT_METADATA_TECNICA', skiprows=2)
        df = df.dropna(subset=['ID_CAMPO'])

        # Renombrar columnas
        df.columns = [
            'id_campo', 'tabla', 'campo', 'tipo_dato', 'longitud', 'nulo', 'llave',
            'valor_defecto', 'descripcion', 'mapeo_matriz', 'id_termino_funcional',
            'fecha_actualizacion', 'version', 'estado'
        ]

        # Convertir longitud a int si es posible
        df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce').astype('Int64')

        df.to_sql('cat_metadata_tecnica', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(df)} campos técnicos documentados")
        return True
    except Exception as e:
        print(f"   ⚠️  Error cargando metadata técnica: {e}")
        return False

def load_dim_dominio(conn):
    """Carga dimensión dominio"""
    conn.execute(text("""
        INSERT INTO catalogo.dim_dominio (codigo, nombre_dominio, sigla) VALUES
        ('DOM-001', 'DATIC', 'DATIC'),
        ('DOM-002', 'Secretaría de Cultura', 'CULT'),
        ('DOM-003', 'Secretaría del Deporte y la Recreación', 'DEP'),
        ('DOM-004', 'Secretaría de Vivienda Social y Hábitat', 'VIV')
    """))
    print("   ✓ Dominios cargados (4 registros)")

def load_dim_area(conn):
    """Carga dimensión área"""
    conn.execute(text("""
        INSERT INTO catalogo.dim_area (codigo, id_dominio, nombre_area) VALUES
        ('DATIC-INN', 1, 'Subdirección de Innovación Digital'),
        ('DATIC-TEC', 1, 'Subdirección de Tecnología Digital'),
        ('CULT-BIB', 2, 'Red de Bibliotecas Públicas de Cali'),
        ('CULT-ART', 2, 'Subsecretaría de Artes, Creación y Promoción Cultural'),
        ('CULT-PAT', 2, 'Subsecretaría de Patrimonio, Bibliotecas e Infraestructura'),
        ('CULT-TM', 2, 'Teatro Municipal'),
        ('CULT-TAK', 2, 'Unidad Administrativa Especial Estudio de Grabación Takeshima'),
        ('CULT-EVE', 2, 'Área de eventos y festivales'),
        ('CULT-TER', 2, 'Enfoque territorial y participación comunitaria'),
        ('DEP-FOM', 3, 'Subsecretaria de Fomento'),
        ('DEP-INF', 3, 'Subsecretaria de Infraestructura Deportiva y Recreativa'),
        ('VIV-MEJ', 4, 'Subsecretaria Mejoramiento Integral y Legalización'),
        ('VIV-GES', 4, 'Subsecretaria Gestión de suelo y Oferta de Vivienda'),
        ('VIV-UAG', 4, 'Unidad de Apoyo a la Gestión')
    """))
    print("   ✓ Áreas cargadas (14 registros)")

def load_dim_canal(conn):
    """Carga dimensión canal"""
    conn.execute(text("""
        INSERT INTO catalogo.dim_canal (codigo, nombre_canal, descripcion) VALUES
        ('01-TEL', 'Telefónico', 'Atención telefónica'),
        ('02-PRES', 'Presencial', 'Atención en sede física'),
        ('03-WEB', 'Portal Web', 'Sitio web institucional'),
        ('04-APP', 'Aplicativo Móvil', 'Aplicación para dispositivos móviles'),
        ('05-EMAIL', 'Correo Electrónico', 'Atención vía email'),
        ('06-CHAT', 'Chat/WhatsApp', 'Mensajería instantánea'),
        ('07-MULTI', 'Multicanal', 'Múltiples canales disponibles')
    """))
    print("   ✓ Canales cargados (7 registros)")

def load_dim_herramienta_tic(conn):
    """Carga dimensión herramientas TIC"""
    conn.execute(text("""
        INSERT INTO catalogo.dim_herramienta_tic (codigo, nombre_herramienta, descripcion_herr, url) VALUES
        ('LMS', 'LMS Moodle', 'Plataforma de aprendizaje', 'https://moodle.cali.gov.co/login/index.php'),
        ('MARI', 'MARI', 'Sistema de registro de daños', NULL),
        ('LANDING', 'Landing Page', 'Página de aterrizaje web', NULL),
        ('SIGES', 'SIGES', 'Sistema de gestión', NULL),
        ('PORTAL', 'Portal Web', 'Sitio web institucional', 'https://www.cali.gov.co'),
        ('EMAIL', 'Correo Electrónico', 'Sistema de email', NULL),
        ('PRESENCIAL', 'Atención Presencial', 'Sin herramienta digital', NULL),
        ('TELEFONO', 'Línea Telefónica', 'Atención telefónica', NULL),
        ('WHATSAPP', 'WhatsApp', 'Mensajería', NULL),
        ('SIN_INFO', 'Sin información', 'No especificado', NULL)
    """))
    print("   ✓ Herramientas TIC cargadas (10 registros)")

def load_dim_estado(conn):
    """Carga dimensión estado"""
    conn.execute(text("""
        INSERT INTO catalogo.dim_estado (codigo, nombre_estado, descripcion) VALUES
        ('ACT', 'Activo', 'Servicio operativo y visible para ciudadanos'),
        ('INA', 'Inactivo', 'Servicio temporalmente fuera de servicio'),
        ('REV', 'En Revisión', 'Servicio en proceso de actualización')
    """))
    print("   ✓ Estados cargados (3 registros)")

def load_dim_requisito(engine, file_path):
    """Carga requisitos desde artefactos"""
    print("📋 Cargando DIM_REQUISITO...")
    try:
        df = pd.read_excel(file_path, sheet_name='06_DIM_REQUISITO', skiprows=2)
        df = df.dropna(subset=['CODIGO'])

        # Preparar dataframe
        df_req = pd.DataFrame({
            'id_requisito': df['CODIGO'].astype(str),
            'codigo': df['CODIGO'].astype(str),
            'nombre_requisito': df['NOMBRE_REQUISITO'].astype(str),
            'detalle': df['DETALLE'].apply(clean_text),
            'tipo_soporte': None,  # No viene en artefactos nuevos
            'categoria': None  # No viene en artefactos nuevos
        })

        df_req.to_sql('dim_requisito', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(df_req)} requisitos cargados desde artefactos")

        # Agregar código R999 que está en la matriz pero no en artefactos
        requisito_r999 = pd.DataFrame([
            {
                'id_requisito': 'R999',
                'codigo': 'R999',
                'nombre_requisito': 'Sin información disponible',
                'detalle': 'Servicio sin requisitos documentados en matriz',
                'tipo_soporte': None,
                'categoria': None
            }
        ])

        requisito_r999.to_sql('dim_requisito', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ 1 requisito adicional agregado (R999)")

        return True
    except Exception as e:
        print(f"   ⚠️  Error cargando requisitos: {e}")
        return False

def load_dim_ubicacion(engine, file_path):
    """Carga ubicaciones desde artefactos"""
    print("📍 Cargando DIM_UBICACION...")
    try:
        df = pd.read_excel(file_path, sheet_name='07_DIM_UBICACION', skiprows=2)
        df = df.dropna(subset=['CODIGO'])

        # Preparar dataframe
        df_ubi = pd.DataFrame({
            'codigo': df['CODIGO'].astype(str),
            'nombre_sede': df['NOMBRE_SEDE'].astype(str),
            'direccion': df['DIRECCION'].apply(clean_text),
            'horario': df['HORARIO'].apply(clean_text),
            'horario_general': df['HORARIO'].apply(clean_text),
            'telefono': df['TELEFONO'].apply(clean_text),
            'correo_elect': df['CORREO_ELECT'].apply(clean_text),
            'barrio': df['BARRIO'].apply(clean_text),
            'comuna': df['COMUNA'].apply(clean_text),
            'tipo_sede': df['TIPO_SEDE'].apply(clean_text),
            'estado': df['ESTADO'].astype(str),
            'id_dominio': None  # Se puede agregar si está en artefactos
        })

        df_ubi.to_sql('dim_ubicacion', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(df_ubi)} ubicaciones cargadas")
        return True
    except Exception as e:
        print(f"   ⚠️  Error cargando ubicaciones: {e}")
        return False

def process_servicios(df_matriz, engine):
    """Procesa y carga servicios desde matriz"""
    print("🚀 Procesando servicios desde matriz...")

    # Mapeos
    MAP_DOMINIO = {
        'DATIC': 1,
        'Secretaría de Cultura': 2,
        'Secretaría del Deporte y la Recreación': 3,
        'Secretaría de Vivienda Social y Hábitat': 4
    }

    MAP_AREA = {
        'Subdirección de Innovación Digital': 1,
        'Subdirección de Tecnología Digital': 2,
        'Red de Bibliotecas Públicas de Cali': 3,
        'Subsecretaría de Artes, Creación y Promoción Cultural': 4,
        'Subsecretaría de Patrimonio, Bibliotecas e Infraestructura': 5,
        'Teatro Municipal': 6,
        'Unidad Administrativa Especial Estudio de Grabación Takeshima': 7,
        'Área de eventos y festivales': 8,
        'Enfoque territorial y participación comunitaria': 9,
        'Subsecretaria de Fomento': 10,
        'Subsecretaria de Infraestructura Deportiva y Recreativa': 11,
        'Subsecretaria Mejoramiento Integral y Legalización': 12,
        'Subsecretaria Gestión de suelo y Oferta de Vivienda': 13,
        'Unidad de Apoyo a la Gestión': 14,
    }

    servicios_data = []
    rel_req_data = []
    rel_ubi_data = []

    for idx, row in df_matriz.iterrows():
        # Extraer datos básicos
        codigo_serv = clean_text(row.get('codigo_servicio'))
        nombre = clean_text(row.get('Nombre del Servicio'))
        organismo = clean_text(row.get('Organismo'))
        area = clean_text(row.get('Área que lo realiza'))

        if not codigo_serv or not nombre:
            continue

        # Preparar servicio
        servicio = {
            'codigo_servicio': codigo_serv,
            'id_dominio': MAP_DOMINIO.get(organismo, 1),
            'id_area': MAP_AREA.get(area, 1),
            'id_herramienta_tic': 10,  # Por defecto sin info
            'id_estado': 1,  # Activo
            'id_canal': 7,  # Multicanal por defecto
            'nombre_servicio': nombre,
            'descripcion': clean_text(row.get('Descripción del Servicio')),
            'proposito': clean_text(row.get('Propósito del producto')),
            'dirigido_a': clean_text(row.get('A quién va dirigido')),
            'descripcion_respuesta_esperada': clean_text(row.get('Nombre del resultado, producto o respuesta que se obtiene')),
            'tiempo_respuesta': clean_text(row.get('Tiempo de Obtención')),
            'fundamento_legal': clean_text(row.get('Fundamento Legal o Procedimental')),
            'informacion_costo': clean_text(row.get('Información sobre Costos')),
            'documentos_daruma': clean_text(row.get('Documentos DARUMA PROCEDIMIENTO/ FORMATO')),
            'volumen_mensual_promedio': int(row.get('Promedio solicitudes por mes', 0)) if pd.notna(row.get('Promedio solicitudes por mes')) else 0
        }
        servicios_data.append(servicio)

        # Procesar requisitos
        raw_reqs = clean_text(row.get('Requisitos (Normalizado)'))
        if raw_reqs:
            raw_reqs = raw_reqs.replace('{', '').replace('}', '').replace(',', ';')
            codes = [x.strip() for x in raw_reqs.split(';') if x.strip()]
            for orden, code in enumerate(codes, start=1):
                rel_req_data.append({
                    'codigo_servicio_temp': codigo_serv,
                    'codigo_servicio': codigo_serv,
                    'codigo_requisito': code,
                    'id_requisito': code,
                    'es_obligatorio': True,
                    'orden_presentacion': orden
                })

        # Procesar ubicaciones
        raw_ubi = clean_text(row.get('Ubicación (Normalizado)'))
        if raw_ubi:
            raw_ubi = raw_ubi.replace('{', '').replace('}', '').replace(',', ';')
            codes = [x.strip() for x in raw_ubi.split(';') if x.strip()]
            for ubi_code in codes:
                # Obtener ID de ubicación desde base de datos
                df_ubi_db = pd.read_sql(f"SELECT id_ubicacion FROM catalogo.dim_ubicacion WHERE codigo = '{ubi_code}'", engine)
                if len(df_ubi_db) > 0:
                    rel_ubi_data.append({
                        'codigo_servicio_temp': codigo_serv,
                        'codigo_servicio': codigo_serv,
                        'id_ubicacion': int(df_ubi_db.iloc[0]['id_ubicacion']),
                        'es_sede_principal': True
                    })

    print(f"   ✓ {len(servicios_data)} servicios procesados")
    return servicios_data, rel_req_data, rel_ubi_data

def run_etl():
    print("⏳ Esperando conexión a base de datos...")
    time.sleep(5)

    try:
        engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
        print("✅ Conexión exitosa a PostgreSQL")
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return

    print("📊 Limpiando y cargando datos maestros...")

    # Limpiar todas las tablas
    with engine.connect() as conn:
        conn.execute(text("""
            TRUNCATE TABLE
                catalogo.rel_servicio_requisito,
                catalogo.rel_servicio_ubicacion,
                catalogo.fact_servicio,
                catalogo.dim_requisito,
                catalogo.dim_ubicacion,
                catalogo.dim_herramienta_tic,
                catalogo.dim_area,
                catalogo.dim_canal,
                catalogo.dim_estado,
                catalogo.dim_dominio,
                catalogo.cat_metadata_funcional,
                catalogo.cat_metadata_tecnica
            RESTART IDENTITY CASCADE
        """))
        print("   ✓ Tablas limpiadas y secuencias reiniciadas")

        # Cargar metadata
        load_metadata_funcional(engine, INPUT_ARTEFACTOS)
        load_metadata_tecnica(engine, INPUT_ARTEFACTOS)

        # Cargar dimensiones maestras
        load_dim_dominio(conn)
        load_dim_area(conn)
        load_dim_canal(conn)
        load_dim_herramienta_tic(conn)
        load_dim_estado(conn)

    # Cargar dimensiones desde artefactos
    load_dim_requisito(engine, INPUT_ARTEFACTOS)
    load_dim_ubicacion(engine, INPUT_ARTEFACTOS)

    # Leer y procesar matriz
    print(f"📄 Leyendo matriz: {INPUT_MATRIZ}")
    try:
        df_matriz = pd.read_excel(INPUT_MATRIZ)
        print(f"   ✓ {len(df_matriz)} registros encontrados")
    except Exception as e:
        print(f"❌ Error leyendo matriz: {e}")
        return

    # Procesar servicios
    servicios_data, rel_req_data, rel_ubi_data = process_servicios(df_matriz, engine)

    # Cargar servicios
    print("💾 Cargando FACT_SERVICIO...")
    df_servicios = pd.DataFrame(servicios_data)
    df_servicios.to_sql('fact_servicio', engine, schema='catalogo', if_exists='append', index=False)
    print(f"   ✓ {len(df_servicios)} servicios cargados")

    # Cargar relaciones requisitos
    print("💾 Cargando REL_SERVICIO_REQUISITO...")
    if len(rel_req_data) > 0:
        df_services_db = pd.read_sql("SELECT id_servicio, codigo_servicio FROM catalogo.fact_servicio", engine)
        df_rel_req = pd.DataFrame(rel_req_data)
        df_merged = pd.merge(df_rel_req, df_services_db, left_on='codigo_servicio_temp', right_on='codigo_servicio', how='inner')
        final_rel = df_merged[['id_servicio', 'id_requisito', 'codigo_servicio_x', 'codigo_requisito', 'es_obligatorio', 'orden_presentacion']].copy()
        final_rel.rename(columns={'codigo_servicio_x': 'codigo_servicio'}, inplace=True)
        final_rel.to_sql('rel_servicio_requisito', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(final_rel)} relaciones servicio-requisito cargadas")

    # Cargar relaciones ubicaciones
    print("💾 Cargando REL_SERVICIO_UBICACION...")
    if len(rel_ubi_data) > 0:
        df_services_db = pd.read_sql("SELECT id_servicio, codigo_servicio FROM catalogo.fact_servicio", engine)
        df_rel_ubi = pd.DataFrame(rel_ubi_data)
        df_merged_ubi = pd.merge(df_rel_ubi, df_services_db, left_on='codigo_servicio_temp', right_on='codigo_servicio', how='inner')
        final_rel_ubi = df_merged_ubi[['id_servicio', 'id_ubicacion', 'codigo_servicio_x', 'es_sede_principal']].copy()
        final_rel_ubi.rename(columns={'codigo_servicio_x': 'codigo_servicio'}, inplace=True)
        final_rel_ubi.to_sql('rel_servicio_ubicacion', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(final_rel_ubi)} relaciones servicio-ubicación cargadas")

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE CARGA - CATÁLOGO SERVICIOS ALCALDÍA CALI v6.0")
    print("=" * 60)

    with engine.connect() as conn:
        tables = [
            ('cat_metadata_funcional', 'METADATA FUNCIONAL'),
            ('cat_metadata_tecnica', 'METADATA TÉCNICA'),
            ('dim_dominio', 'DIM_DOMINIO'),
            ('dim_area', 'DIM_AREA'),
            ('dim_canal', 'DIM_CANAL'),
            ('dim_herramienta_tic', 'DIM_HERRAMIENTA_TIC'),
            ('dim_ubicacion', 'DIM_UBICACION'),
            ('dim_estado', 'DIM_ESTADO'),
            ('dim_requisito', 'DIM_REQUISITO'),
            ('fact_servicio', 'FACT_SERVICIO'),
            ('rel_servicio_requisito', 'REL_SERVICIO_REQUISITO'),
            ('rel_servicio_ubicacion', 'REL_SERVICIO_UBICACION')
        ]

        for table, label in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM catalogo.{table}"))
            count = result.scalar()
            print(f"  • {label:30s} {count:5d}")

    print("=" * 60)
    print("✅ ¡PROCESO ETL v6.0 FINALIZADO CON ÉXITO!")
    print("=" * 60)

if __name__ == '__main__':
    run_etl()
