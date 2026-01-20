import pandas as pd
import os
from sqlalchemy import create_engine, text
import time

# --- CONFIGURACIÓN ---
DB_USER = os.getenv('DB_USER', 'admin_datos')
DB_PASS = os.getenv('DB_PASS', 'cali_segura_2025')
DB_HOST = os.getenv('DB_HOST', 'localhost') # 'db' si corre en docker
DB_NAME = os.getenv('DB_NAME', 'catalogo_cali')
INPUT_FILE = '/app/data/input/matriz_servicios_consolidada.xlsx'

# String de conexión
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:5432/{DB_NAME}"

# Mapeos (Simulados, idealmente vendrían de la BD)
MAP_DOMINIO = {
    'DATIC': 1, 
    'Secretaría de Cultura': 2, 
    'Secretaría de Vivienda Social y Hábitat': 3, 
    'Secretaría del Deporte y la Recreación': 4
}

def clean_text(text):
    if pd.isna(text) or str(text).lower() in ['nan', 'no registra', 'sin definir']:
        return None
    return str(text).strip()

def run_etl():
    print("⏳ Esperando conexión a base de datos...")
    time.sleep(5)

    try:
        engine = create_engine(DATABASE_URL)
        print("✅ Conexión exitosa a PostgreSQL")
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return

    # --- CARGAR DATOS MAESTROS ---
    print("📊 Cargando datos maestros...")

    # Limpiar todas las tablas en el orden correcto (respetando foreign keys)
    try:
        with engine.begin() as conn:
            conn.execute(text("TRUNCATE TABLE catalogo.rel_servicio_requisito CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.rel_servicio_ubicacion CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.fact_servicio CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.dim_requisito CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.dim_ubicacion CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.dim_herramienta_tic CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.dim_area CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.dim_estado CASCADE"))
            conn.execute(text("TRUNCATE TABLE catalogo.dim_dominio CASCADE"))
        print("   ✓ Tablas limpiadas")
    except Exception as e:
        print(f"   ⚠️ Error limpiando tablas: {e}")

    # Crear connection pool para asegurar commits
    with engine.begin() as connection:
        # Insertar dominios (organismos)
        try:
            dominios = [
                {'codigo': 'DOM-001', 'nombre_dominio': 'DATIC', 'sigla': 'DATIC'},
                {'codigo': 'DOM-002', 'nombre_dominio': 'Secretaría de Cultura', 'sigla': 'SC'},
                {'codigo': 'DOM-003', 'nombre_dominio': 'Secretaría de Vivienda Social y Hábitat', 'sigla': 'SVSH'},
                {'codigo': 'DOM-004', 'nombre_dominio': 'Secretaría del Deporte y la Recreación', 'sigla': 'SDR'}
            ]
            df_dominios = pd.DataFrame(dominios)
            df_dominios.to_sql('dim_dominio', connection, schema='catalogo', if_exists='append', index=False)
            print("   ✓ Dominios cargados")
        except Exception as e:
            print(f"   ⚠️ Error cargando dominios: {e}")
            raise

        # Insertar estados
        try:
            estados = [
                {'nombre_estado': 'En diseño'},
                {'nombre_estado': 'En pruebas'},
                {'nombre_estado': 'Activo'},
                {'nombre_estado': 'Suspendido'},
                {'nombre_estado': 'Descontinuado'}
            ]
            df_estados = pd.DataFrame(estados)
            df_estados.to_sql('dim_estado', connection, schema='catalogo', if_exists='append', index=False)
            print("   ✓ Estados cargados")
        except Exception as e:
            print(f"   ⚠️ Error cargando estados: {e}")
            raise

    print("   ✓ Commit de datos maestros realizado")

    print(f"🚀 Iniciando procesamiento de: {INPUT_FILE}")

    try:
        df = pd.read_excel(INPUT_FILE, sheet_name='Hoja1')
        print(f"   📄 Archivo leído: {len(df)} registros encontrados")
    except FileNotFoundError:
        print(f"❌ No se encontró el archivo en {INPUT_FILE}. Verifica que la carpeta 'data/input' esté montada.")
        return
    except Exception as e:
        print(f"❌ Error leyendo el archivo Excel: {e}")
        return

    # --- TRANSFORMACIÓN ---
    print("🔄 Transformando datos...")

    # Verificar columnas requeridas
    required_columns = ['N°', 'Nombre del Servicio', 'Organismo']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Error: Faltan columnas requeridas: {missing_columns}")
        print(f"   Columnas disponibles: {list(df.columns)}")
        return
    
    fact_data = []
    rel_req_data = []
    dim_req_unique = set()

    for idx, row in df.iterrows():
        # Generamos el código de servicio
        codigo_serv = f"SERV-{str(row['N°']).zfill(3)}"

        # Preparamos Fact Service
        fact_data.append({
            'codigo_servicio': codigo_serv,
            'id_dominio': MAP_DOMINIO.get(row['Organismo'], 1), # Default DATIC
            'id_estado': 3, # Activo
            'nombre_servicio': row['Nombre del Servicio'],
            'descripcion': clean_text(row.get('Descripción del Servicio', '')),
            'proposito': clean_text(row.get('Propósito del producto', '')),
            'dirigido_a': clean_text(row.get('A quién va dirigido', '')),
            'tiempo_respuesta': clean_text(row.get('Tiempo de Obtención', '')),
            'fundamento_legal': clean_text(row.get('Fundamento Legal o Procedimental', '')),
            'informacion_costo': clean_text(row.get('Información sobre Costos', '')),
            'volumen_mensual_promedio': pd.to_numeric(row.get('Promedio de solicitudes que se generan por mes', 0), errors='coerce') or 0
        })

        # Preparamos Requisitos
        raw_reqs = str(row.get('Requisitos (Normalizado)', ''))
        if clean_text(raw_reqs):
            codes = [x.strip() for x in raw_reqs.replace(',', ';').split(';') if x.strip()]
            for code in codes:
                # Datos para la tabla intermedia
                rel_req_data.append({
                    'codigo_servicio_temp': codigo_serv, # Usaremos esto para buscar el ID luego
                    'id_requisito': code,
                    'es_obligatorio': True
                })
                dim_req_unique.add(code)

    df_fact = pd.DataFrame(fact_data)
    df_dim_req = pd.DataFrame([{'id_requisito': r, 'nombre_requisito': f'Requisito {r}', 'tipo_soporte': 'Digital'} for r in dim_req_unique])

    print(f"   ✓ {len(df_fact)} servicios procesados")
    print(f"   ✓ {len(df_dim_req)} requisitos únicos identificados")

    # --- CARGA (LOAD) ---
    
    # Nota: Usamos 'append' pero en producción idealmente validamos existencia (Upsert)
    print("💾 Cargando DIM_REQUISITO...")
    try:
        # Insertar ignorando duplicados (requiere soporte específico o limpieza previa)
        # Para el piloto, usamos to_sql con if_exists='append' y manejo de errores simple
        for _, r in df_dim_req.iterrows():
            try:
                pd.DataFrame([r]).to_sql('dim_requisito', engine, schema='catalogo', if_exists='append', index=False)
            except:
                pass # Ya existe
    except Exception as e:
        print(f"⚠️ Alerta en carga requisitos: {e}")

    print("💾 Cargando FACT_SERVICIO...")
    try:
        # Eliminar duplicados si existen en el DataFrame
        df_fact_unique = df_fact.drop_duplicates(subset=['codigo_servicio'], keep='first')
        if len(df_fact_unique) < len(df_fact):
            print(f"   ⚠️ Se encontraron {len(df_fact) - len(df_fact_unique)} registros duplicados, se conserva el primero")

        df_fact_unique.to_sql('fact_servicio', engine, schema='catalogo', if_exists='append', index=False)
        print(f"   ✓ {len(df_fact_unique)} servicios cargados exitosamente.")
    except Exception as e:
        print(f"❌ Error cargando servicios: {e}")
        import traceback
        traceback.print_exc()
        return

    print("💾 Cargando RELACIONES...")
    if len(rel_req_data) > 0:
        # Necesitamos recuperar los IDs autogenerados de fact_servicio
        df_services_db = pd.read_sql("SELECT id_servicio, codigo_servicio FROM catalogo.fact_servicio", engine)

        # Cruzamos el ID real de base de datos con nuestros datos de requisitos
        df_rel_req = pd.DataFrame(rel_req_data)
        df_merged = pd.merge(df_rel_req, df_services_db, left_on='codigo_servicio_temp', right_on='codigo_servicio', how='inner')

        final_rel = df_merged[['id_servicio', 'id_requisito', 'es_obligatorio']]

        try:
            final_rel.to_sql('rel_servicio_requisito', engine, schema='catalogo', if_exists='append', index=False)
            print(f"   ✓ {len(final_rel)} relaciones servicio-requisito cargadas.")
        except Exception as e:
            print(f"❌ Error cargando relaciones: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   ⚠️ No hay requisitos para cargar.")

    # Resumen final
    print("\n" + "="*50)
    print("📊 RESUMEN DE CARGA")
    print("="*50)

    try:
        count_servicios = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.fact_servicio", engine)
        count_requisitos = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_requisito", engine)
        count_relaciones = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.rel_servicio_requisito", engine)
        count_dominios = pd.read_sql("SELECT COUNT(*) as total FROM catalogo.dim_dominio", engine)

        print(f"Dominios:            {count_dominios['total'].iloc[0]}")
        print(f"Servicios:           {count_servicios['total'].iloc[0]}")
        print(f"Requisitos únicos:   {count_requisitos['total'].iloc[0]}")
        print(f"Relaciones S-R:      {count_relaciones['total'].iloc[0]}")
        print("="*50)
    except Exception as e:
        print(f"⚠️ Error obteniendo resumen: {e}")

    engine.dispose()
    print("✅ ¡PROCESO ETL FINALIZADO CON ÉXITO!")

if __name__ == "__main__":
    run_etl()