import pandas as pd
import os
from sqlalchemy import create_engine, text
import time

# --- CONFIGURACIÓN ---
DB_USER = os.getenv('DB_USER', 'admin_datos')
DB_PASS = os.getenv('DB_PASS', 'cali_segura_2025')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'catalogo_cali')
INPUT_FILE = '/app/data/input/matriz_servicios_consolidada.xlsx'

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

# Mapeos de datos maestros
MAP_DOMINIO = {
    'DATIC': 1,
    'Secretaría de Cultura': 2,
    'Secretaría del Deporte y la Recreación': 3,
    'Secretaría de Vivienda Social y Hábitat': 4
}

MAP_PREFIJO = {
    'DATIC': 'DATIC',
    'Secretaría de Cultura': 'CULT',
    'Secretaría del Deporte y la Recreación': 'DEP',
    'Secretaría de Vivienda Social y Hábitat': 'VIV'
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

def clean_text(text):
    """Limpia y normaliza texto"""
    if pd.isna(text) or str(text).lower() in ['nan', 'no registra', 'sin definir', '']:
        return None
    return str(text).strip()

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

    # Limpiar todas las tablas y reiniciar secuencias
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
                catalogo.dim_dominio
            RESTART IDENTITY CASCADE
        """))
        print("   ✓ Tablas limpiadas y secuencias reiniciadas")

        # ========== CARGAR DIM_DOMINIO ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_dominio (codigo, nombre_dominio, sigla) VALUES
            ('DOM-001', 'DATIC', 'DATIC'),
            ('DOM-002', 'Secretaría de Cultura', 'CULT'),
            ('DOM-003', 'Secretaría del Deporte y la Recreación', 'DEP'),
            ('DOM-004', 'Secretaría de Vivienda Social y Hábitat', 'VIV')
        """))
        print("   ✓ Dominios cargados (4 registros)")

        # ========== CARGAR DIM_AREA ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_area (codigo, id_dominio, nombre_area) VALUES
            ('DATIC-INN', 1, 'Subdirección de Innovación Digital'),
            ('DATIC-TEC', 1, 'Subdirección de Tecnología Digital'),
            ('CULT-BIB', 2, 'Red de Bibliotecas Públicas de Cali'),
            ('CULT-ART', 2, 'Subsecretaría de Artes, Creación y Promoción Cultural'),
            ('CULT-PBI', 2, 'Subsecretaría de Patrimonio, Bibliotecas e Infraestructura'),
            ('CULT-TEA', 2, 'Teatro Municipal'),
            ('CULT-TAK', 2, 'Unidad Administrativa Especial Estudio de Grabación Takeshima'),
            ('CULT-EVE', 2, 'Área de eventos y festivales'),
            ('CULT-ETPC', 2, 'Enfoque territorial y participación comunitaria'),
            ('DEP-FOM', 3, 'Subsecretaria de Fomento'),
            ('DEP-IDR', 3, 'Subsecretaria de Infraestructura Deportiva y Recreativa'),
            ('VIV-MIL', 4, 'Subsecretaria Mejoramiento Integral y Legalización'),
            ('VIV-GSOV', 4, 'Subsecretaria Gestión de suelo y Oferta de Vivienda'),
            ('VIV-UAG', 4, 'Unidad de Apoyo a la Gestión')
        """))
        print("   ✓ Áreas cargadas (14 registros)")

        # ========== CARGAR DIM_CANAL ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_canal (codigo, nombre_canal) VALUES
            ('01-TEL', 'Telefónico'),
            ('02-CHT', 'Chat Asistido'),
            ('03-COR', 'Correo contactenos@cali.gov.co'),
            ('04-PAG', 'Ventanilla Página web'),
            ('05-CAM', 'Oficina de Atención al Ciudadano - CAM'),
            ('06-EXT', 'Ventanillas Únicas Externas'),
            ('07-CAL', 'C.A.L.I.')
        """))
        print("   ✓ Canales cargados (7 registros)")

        # ========== CARGAR DIM_HERRAMIENTA_TIC ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_herramienta_tic (codigo, nombre_herramienta, descripcion, url) VALUES
            ('LMS', 'LMS Moodle', 'Plataforma de aprendizaje', 'https://moodle.cali.gov.co/login/index.php'),
            ('ORFEO', 'ORFEO', 'Gestión documental', 'https://orfeo.cali.gov.co/'),
            ('MARI', 'MARI', 'Mesa de ayuda', 'https://mari.cali.gov.co'),
            ('PORTAL', 'PAGINA', 'Página web', 'https://www.cali.gov.co/'),
            ('DARUMA', 'DARUMA', 'Consulta de procesos y formatos', 'https://sig.cali.gov.co/app.php/staff/portal/tab/1'),
            ('SIDER', 'SIDER', 'Trámites deportivos y clubes', 'http://sider.cali.gov.co:8081/'),
            ('CULT_LIN', 'CULTURA', 'Oferta de servicios Cultura', 'https://www.culturaenlineacali.com/'),
            ('CORR_INST', 'CORREO INSTITUCIONAL', 'Correo Institucional Alcaldía', 'contactenos@cali.gov.co'),
            ('VENT', 'VENTANILLA VIRTUAL', 'Ventanilla Virtual de la Alcaldía', 'https://archivo.cali.gov.co/participacion/publicaciones/43/oficina_de_atencin_al_ciudadano/'),
            ('NA', 'No Aplica', 'Sin herramienta TIC', NULL)
        """))
        print("   ✓ Herramientas TIC cargadas (10 registros)")

        # ========== CARGAR DIM_UBICACION ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_ubicacion (codigo, nombre_sede, direccion, horario_general, telefono, id_dominio, estado) VALUES
            ('UBI-001', 'LID/PAD DATIC (Múltiples sedes)', 'Según directorio LID/PAD', 'Lun-Vie 7:30-12:00 y 13:30-17:30', 'Según directorio', 1, 'Activo'),
            ('UBI-027', 'Secretaría de Deporte y Recreación', 'Por definir', 'Por definir', 'Por definir', 3, 'Activo'),
            ('UBI-030', 'Secretaría de Vivienda - Edificio Fuente Versalles', 'Av. 5An # 20-08 Edificio Fuente Versalles', 'Lun-Vie 8:00-12:30 y 13:30-17:00', '(602) 6684340', 4, 'Activo'),
            ('UBI-033', 'Zonas WiFi Públicas', 'Múltiples ubicaciones en la ciudad', '24/7 (si la zona está en operación)', NULL, 1, 'Activo'),
            ('UBI-099', 'Sin definir', NULL, NULL, NULL, NULL, 'Pendiente')
        """))
        print("   ✓ Ubicaciones cargadas (5 registros)")

        # ========== CARGAR DIM_ESTADO ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_estado (codigo, nombre_estado, descripcion) VALUES
            ('ACT', 'Activo', 'Operativo y visible'),
            ('INA', 'Inactivo', 'Descontinuado'),
            ('REV', 'En Revisión', 'Pendiente aprobación')
        """))
        print("   ✓ Estados cargados (3 registros)")

        # ========== CARGAR DIM_REQUISITO (DATOS MAESTROS) ==========
        conn.execute(text("""
            INSERT INTO catalogo.dim_requisito (id_requisito, codigo, nombre_requisito, tipo_soporte, categoria) VALUES
            ('R001', 'R001', 'Formulario de inscripción Landing', 'Digital', 'Registro'),
            ('R002', 'R002', 'Requisitos publicados en Landing', 'Digital', 'Información'),
            ('R003', 'R003', 'Plan de Formación', 'Digital', 'Educativo'),
            ('R004', 'R004', 'Contenidos Programáticos', 'Digital', 'Educativo'),
            ('R005', 'R005', 'Material de Apoyo', 'Digital', 'Educativo'),
            ('R006', 'R006', 'Estar registrado', 'Digital', 'Registro'),
            ('R007', 'R007', 'Formato/solicitud de préstamo', 'Físico', 'Solicitud'),
            ('R008', 'R008', 'Oficio formal con exposición de motivos', 'Físico', 'Solicitud'),
            ('R009', 'R009', 'Formulario en aplicativo MARI (Daños)', 'Digital', 'Solicitud'),
            ('R010', 'R010', 'Responder preguntas de Caracterización', 'Digital', 'Registro'),
            ('R011', 'R011', 'Demostrar titularidad del predio', 'Físico', 'Legal'),
            ('R012', 'R012', 'Constancia de pago - Cartera Sec. Vivienda', 'Físico', 'Financiero'),
            ('R013', 'R013', 'Poder autenticado del titular (si aplica)', 'Físico', 'Legal'),
            ('R014', 'R014', 'Certificado cédula (Registraduría)', 'Digital', 'Identificación'),
            ('R015', 'R015', 'Certificado Libertad y Tradición (30 días)', 'Físico', 'Legal'),
            ('R016', 'R016', 'Solicitud de Certificado de Adjudicación', 'Físico', 'Solicitud'),
            ('R017', 'R017', 'Solicitud de Intervención en Territorio', 'Físico', 'Solicitud'),
            ('R018', 'R018', 'Seguimiento solicitudes intervención', 'Digital', 'Seguimiento'),
            ('R019', 'R019', 'Solicitud reconocimiento/renovación deportivo', 'Físico', 'Solicitud'),
            ('R020', 'R020', 'Documentos constitución organización deportiva', 'Físico', 'Legal'),
            ('R021', 'R021', 'Informe de Gestor Deportivo', 'Digital', 'Informe'),
            ('R022', 'R022', 'Resolución Reconocimiento/Renovación/Disolución', 'Físico', 'Legal'),
            ('R023', 'R023', 'Solicitud disolución clubes deportivos', 'Físico', 'Solicitud'),
            ('R024', 'R024', 'Ficha inscripción beneficiarios programas', 'Físico', 'Registro'),
            ('R000', 'R000', 'Sin información', 'N/A', 'N/A'),
            ('R999', 'R999', 'No requiere documentación ni requisitos', 'N/A', 'N/A')
        """))
        print("   ✓ Requisitos maestros cargados (26 registros)")

    print(f"🚀 Iniciando procesamiento de: {INPUT_FILE}")

    try:
        df = pd.read_excel(INPUT_FILE, sheet_name='Hoja1')
        print(f"   📄 Archivo leído: {len(df)} registros encontrados")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo en {INPUT_FILE}")
        return
    except Exception as e:
        print(f"❌ Error leyendo el archivo Excel: {e}")
        return

    # Verificar columnas requeridas
    required_columns = ['N°', 'Nombre del Servicio', 'Organismo']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Error: Faltan columnas requeridas: {missing_columns}")
        return

    print("🔄 Transformando datos...")

    fact_data = []
    rel_req_data = []
    rel_ubi_data = []
    dim_req_unique = set()

    for idx, row in df.iterrows():
        prefijo = MAP_PREFIJO.get(row['Organismo'], 'SERV')
        codigo_serv = f"{prefijo}-{str(row['N°']).zfill(3)}"
        id_dominio = MAP_DOMINIO.get(row['Organismo'], 1)

        # Mapear área desde columna "Área que lo realiza"
        area_nombre = str(row.get('Área que lo realiza', '')).strip() if pd.notna(row.get('Área que lo realiza')) else ''
        id_area = MAP_AREA.get(area_nombre, None)

        # Construir registro del servicio
        fact_data.append({
            'codigo_servicio': codigo_serv,
            'id_dominio': id_dominio,
            'id_area': id_area,
            'id_herramienta_tic': None,  # Por definir con mapeo específico
            'id_estado': 1,  # ACT (Activo) por defecto
            'id_canal': None,  # Por definir con mapeo específico
            'nombre_servicio': row['Nombre del Servicio'],
            'descripcion': clean_text(row.get('Descripción del Servicio', '')),
            'proposito': clean_text(row.get('Propósito del producto', '')),
            'dirigido_a': clean_text(row.get('A quién va dirigido', '')),
            'tiempo_respuesta': clean_text(row.get('Tiempo de Obtención', '')),
            'fundamento_legal': clean_text(row.get('Fundamento Legal o Procedimental', '')),
            'informacion_costo': clean_text(row.get('Información sobre Costos', '')),
            'volumen_mensual_promedio': pd.to_numeric(row.get('Promedio de solicitudes que se generan por mes', 0), errors='coerce') or 0
        })

        # Procesar requisitos
        raw_reqs = str(row.get('Requisitos (Normalizado)', ''))
        if clean_text(raw_reqs):
            # Limpiar llaves {} y caracteres especiales
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
                dim_req_unique.add(code)

        # Asignar ubicación por defecto según organismo
        ubicacion_map = {
            1: 1,   # DATIC -> UBI-001
            2: 5,   # Cultura -> UBI-099 (Sin definir)
            3: 2,   # Deporte -> UBI-027
            4: 3    # Vivienda -> UBI-030
        }
        id_ubicacion = ubicacion_map.get(id_dominio, 5)

        rel_ubi_data.append({
            'codigo_servicio_temp': codigo_serv,
            'codigo_servicio': codigo_serv,
            'id_ubicacion': id_ubicacion,
            'es_sede_principal': True
        })

    df_fact = pd.DataFrame(fact_data)

    print(f"   ✓ {len(df_fact)} servicios procesados")
    print(f"   ✓ {len(dim_req_unique)} códigos de requisito identificados")

    # ========== CARGAR FACT_SERVICIO ==========
    print("💾 Cargando FACT_SERVICIO...")
    df_fact.to_sql('fact_servicio', engine, schema='catalogo', if_exists='append', index=False)
    print(f"   ✓ {len(df_fact)} servicios cargados")

    # ========== CARGAR REL_SERVICIO_REQUISITO ==========
    print("💾 Cargando REL_SERVICIO_REQUISITO...")
    if len(rel_req_data) > 0:
        df_services_db = pd.read_sql("SELECT id_servicio, codigo_servicio FROM catalogo.fact_servicio", engine)
        df_rel_req = pd.DataFrame(rel_req_data)
        df_merged = pd.merge(df_rel_req, df_services_db, left_on='codigo_servicio_temp', right_on='codigo_servicio', how='inner')
        # Usar codigo_servicio_x que viene de df_rel_req
        final_rel = df_merged[['id_servicio', 'id_requisito', 'codigo_servicio_x', 'codigo_requisito', 'es_obligatorio', 'orden_presentacion']].copy()
        final_rel.rename(columns={'codigo_servicio_x': 'codigo_servicio'}, inplace=True)

        final_rel.to_sql('rel_servicio_requisito', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(final_rel)} relaciones servicio-requisito cargadas")

    # ========== CARGAR REL_SERVICIO_UBICACION ==========
    print("💾 Cargando REL_SERVICIO_UBICACION...")
    if len(rel_ubi_data) > 0:
        df_rel_ubi = pd.DataFrame(rel_ubi_data)
        df_merged_ubi = pd.merge(df_rel_ubi, df_services_db, left_on='codigo_servicio_temp', right_on='codigo_servicio', how='inner')
        # Usar codigo_servicio_x que viene de df_rel_ubi
        final_rel_ubi = df_merged_ubi[['id_servicio', 'id_ubicacion', 'codigo_servicio_x', 'es_sede_principal']].copy()
        final_rel_ubi.rename(columns={'codigo_servicio_x': 'codigo_servicio'}, inplace=True)

        final_rel_ubi.to_sql('rel_servicio_ubicacion', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(final_rel_ubi)} relaciones servicio-ubicación cargadas")

    # ========== RESUMEN FINAL ==========
    print("\n" + "="*60)
    print("📊 RESUMEN DE CARGA - CATÁLOGO SERVICIOS ALCALDÍA CALI")
    print("="*60)

    count_dominios = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_dominio", engine)
    count_areas = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_area", engine)
    count_canales = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_canal", engine)
    count_herramientas = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_herramienta_tic", engine)
    count_ubicaciones = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_ubicacion", engine)
    count_estados = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_estado", engine)
    count_requisitos = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_requisito", engine)
    count_servicios = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.fact_servicio", engine)
    count_rel_req = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.rel_servicio_requisito", engine)
    count_rel_ubi = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.rel_servicio_ubicacion", engine)

    print("DIMENSIONALES:")
    print(f"  • Dominios (Organismos):        {count_dominios['total'].iloc[0]:>3}")
    print(f"  • Áreas:                        {count_areas['total'].iloc[0]:>3}")
    print(f"  • Canales de Atención:          {count_canales['total'].iloc[0]:>3}")
    print(f"  • Herramientas TIC:             {count_herramientas['total'].iloc[0]:>3}")
    print(f"  • Ubicaciones (Sedes):          {count_ubicaciones['total'].iloc[0]:>3}")
    print(f"  • Estados:                      {count_estados['total'].iloc[0]:>3}")
    print(f"  • Requisitos:                   {count_requisitos['total'].iloc[0]:>3}")
    print("\nHECHOS:")
    print(f"  • Servicios:                    {count_servicios['total'].iloc[0]:>3}")
    print("\nRELACIONES:")
    print(f"  • Servicio-Requisito:           {count_rel_req['total'].iloc[0]:>3}")
    print(f"  • Servicio-Ubicación:           {count_rel_ubi['total'].iloc[0]:>3}")
    print("="*60)

    engine.dispose()
    print("✅ ¡PROCESO ETL FINALIZADO CON ÉXITO!")

if __name__ == "__main__":
    run_etl()
