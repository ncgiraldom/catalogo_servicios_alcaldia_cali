# Catálogo de Servicios - Alcaldía de Cali

Sistema de Gobierno de Datos para el catálogo de servicios ciudadanos de la Alcaldía de Santiago de Cali.

## Características

- Base de datos PostgreSQL con esquema dimensional (Star Schema)
- ETL automatizado para carga de datos desde Excel
- Interfaz visual con NocoDB (tipo Excel/Airtable)
- Administrador PostgreSQL (pgAdmin)
- Despliegue completo con Docker Compose

## Requisitos Previos

- Docker Desktop instalado y en ejecución
- Git (para clonar el repositorio)
- 2 GB de RAM disponible
- Puertos disponibles: 5432, 5050, 8080

## Instalación y Despliegue

### Opción 1: Despliegue Automático Completo

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd catalogo_servicios_alcaldia_cali

# 2. Levantar todos los servicios
docker-compose up -d

# 3. Esperar a que el ETL complete (aprox. 30 segundos)
docker logs catalogo_etl -f
```

**¡Eso es todo!** El sistema estará listo cuando veas el mensaje:

```
✅ ETL COMPLETADO EXITOSAMENTE
📊 54 servicios cargados
```

### Opción 2: Despliegue Paso a Paso

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd catalogo_servicios_alcaldia_cali

# 2. Construir la imagen del ETL
docker-compose build etl

# 3. Levantar la base de datos primero
docker-compose up -d db

# 4. Esperar a que PostgreSQL esté listo (healthcheck)
docker-compose ps

# 5. Levantar los demás servicios
docker-compose up -d
```

## Verificación del Despliegue

### 1. Verificar que todos los contenedores están corriendo

```bash
docker-compose ps
```

Deberías ver 4 servicios con estado "Up":
- catalogo_db
- catalogo_etl (puede mostrar "Exit 0" si completó exitosamente)
- catalogo_nocodb
- catalogo_pgadmin

### 2. Verificar que los datos se cargaron

```bash
# Verificar cantidad de servicios
docker exec catalogo_db psql -U admin_datos -d catalogo_cali -c "SELECT COUNT(*) FROM catalogo.fact_servicio;"

# Debería mostrar: 54
```

### 3. Verificar logs del ETL

```bash
docker logs catalogo_etl
```

Deberías ver:

```
✅ ETL COMPLETADO EXITOSAMENTE
====================================================
📊 RESUMEN DE CARGA - CATÁLOGO SERVICIOS ALCALDÍA CALI
====================================================
TABLA                          | REGISTROS
------------------------------+----------
✓ DIM_DOMINIO                  |        4
✓ DIM_AREA                     |       14
✓ DIM_HERRAMIENTA_TIC          |        5
✓ DIM_UBICACION                |        5
✓ DIM_CANAL                    |        5
✓ DIM_ESTADO                   |        3
✓ DIM_REQUISITO                |       26
✓ FACT_SERVICIO                |       54
✓ REL_SERVICIO_REQUISITO       |       70
✓ REL_SERVICIO_UBICACION       |       54
====================================================
```

## Acceso a los Servicios

### NocoDB (Interfaz Visual)

- URL: http://localhost:8080
- **Primera vez**: Crear cuenta de administrador
- **Conexión a la base de datos**:
  - Host: `db`
  - Port: `5432`
  - Database: `catalogo_cali`
  - User: `admin_datos`
  - Password: `cali_segura_2025`
  - **Schema**: `catalogo` (¡IMPORTANTE!)

### pgAdmin (Administrador PostgreSQL)

- URL: http://localhost:5050
- Email: `admin@cali.gov.co`
- Password: `admin`

**Configurar conexión a PostgreSQL**:
1. Click derecho en "Servers" > "Register" > "Server"
2. General tab:
   - Name: `Catálogo Cali`
3. Connection tab:
   - Host: `db`
   - Port: `5432`
   - Database: `catalogo_cali`
   - Username: `admin_datos`
   - Password: `cali_segura_2025`

### PostgreSQL (Conexión Directa)

Desde tu máquina local (Power BI, Python, etc.):

```
Host: localhost
Port: 5432
Database: catalogo_cali
User: admin_datos
Password: cali_segura_2025
Schema: catalogo
```

## Estructura de Datos

El modelo de datos incluye **10 tablas**:

### Tablas Dimensionales (7)
1. **dim_dominio**: Organismos de la Alcaldía (4 registros)
2. **dim_area**: Áreas y subdirecciones (14 registros)
3. **dim_canal**: Canales de atención (5 registros)
4. **dim_herramienta_tic**: Herramientas tecnológicas (5 registros)
5. **dim_ubicacion**: Sedes y puntos de atención (5 registros)
6. **dim_estado**: Estados de servicio (3 registros)
7. **dim_requisito**: Requisitos documentales (26 registros)

### Tabla de Hechos (1)
8. **fact_servicio**: Catálogo de servicios ciudadanos (54 registros)

### Tablas Relacionales (2)
9. **rel_servicio_requisito**: Servicios vs Requisitos (70 relaciones)
10. **rel_servicio_ubicacion**: Servicios vs Ubicaciones (54 relaciones)

## Consultas SQL Útiles

### Ver todos los servicios con su organismo y área

```sql
SELECT
    s.codigo_servicio,
    s.nombre_servicio,
    d.nombre_dominio,
    a.nombre_area,
    e.nombre_estado
FROM catalogo.fact_servicio s
LEFT JOIN catalogo.dim_dominio d ON s.id_dominio = d.id_dominio
LEFT JOIN catalogo.dim_area a ON s.id_area = a.id_area
LEFT JOIN catalogo.dim_estado e ON s.id_estado = e.id_estado
ORDER BY s.codigo_servicio;
```

### Ver servicios con sus requisitos

```sql
SELECT
    s.codigo_servicio,
    s.nombre_servicio,
    r.codigo AS codigo_requisito,
    r.nombre_requisito,
    r.categoria,
    rel.orden_presentacion
FROM catalogo.fact_servicio s
INNER JOIN catalogo.rel_servicio_requisito rel ON s.id_servicio = rel.id_servicio
INNER JOIN catalogo.dim_requisito r ON rel.id_requisito = r.id_requisito
ORDER BY s.codigo_servicio, rel.orden_presentacion;
```

### Ver servicios por organismo

```sql
SELECT
    d.nombre_dominio,
    COUNT(s.id_servicio) as cantidad_servicios
FROM catalogo.dim_dominio d
LEFT JOIN catalogo.fact_servicio s ON d.id_dominio = s.id_dominio
GROUP BY d.nombre_dominio
ORDER BY cantidad_servicios DESC;
```

## Mantenimiento y Actualización

### Recargar datos desde cero

```bash
# 1. Detener y eliminar todos los contenedores y volúmenes
docker-compose down -v

# 2. Levantar nuevamente
docker-compose up -d

# Los datos se cargarán automáticamente
```

### Actualizar solo los datos (sin borrar la BD)

```bash
# 1. Ejecutar el ETL manualmente
docker-compose run --rm etl

# Esto agregará datos nuevos sin borrar los existentes
```

### Ver logs en tiempo real

```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs solo del ETL
docker logs catalogo_etl -f

# Ver logs de la base de datos
docker logs catalogo_db -f
```

## Solución de Problemas

### El ETL no carga datos

**Síntoma**: Las tablas están vacías después de `docker-compose up`

**Solución**:
```bash
# 1. Verificar que el archivo Excel existe
ls -la data/input/matriz_servicios_consolidada.xlsx

# 2. Ver logs del ETL
docker logs catalogo_etl

# 3. Si es necesario, ejecutar manualmente
docker-compose run --rm etl
```

### Error "relation does not exist"

**Síntoma**: Errores de tablas no encontradas

**Solución**: Asegúrate de estar usando el schema correcto:
```sql
SET search_path TO catalogo, public;
```

O especifica el schema en las consultas:
```sql
SELECT * FROM catalogo.fact_servicio;
```

### NocoDB no muestra las tablas

**Causa**: Estás conectado al schema `public` en lugar de `catalogo`

**Solución**:
1. En NocoDB, ve a la configuración de la base de datos
2. Verifica que el campo "Schema" diga `catalogo`
3. Si no, edita la conexión y cambia el schema

### Puerto 5432 ya está en uso

**Síntoma**: Error al iniciar PostgreSQL

**Solución**:
```bash
# Opción 1: Detener PostgreSQL local
# En Windows: Detener el servicio desde "Servicios"
# En Linux/Mac: sudo systemctl stop postgresql

# Opción 2: Cambiar el puerto en docker-compose.yml
# Cambiar "5432:5432" a "5433:5432"
```

## Arquitectura del Proyecto

```
catalogo_servicios_alcaldia_cali/
├── data/
│   └── input/
│       ├── matriz_servicios_consolidada.xlsx   # Datos fuente
│       └── Artefactos_Revisado_19ene2026.xlsx  # Modelo de referencia
├── database/
│   ├── 00_init_complete.sql                    # Script de inicialización
│   ├── 01_schema_ddl.sql                       # (Legacy - no se usa)
│   ├── 02_migration_add_canal.sql              # (Legacy - ya integrado)
│   └── 03_migration_update_requisito.sql       # (Legacy - ya integrado)
├── etl/
│   ├── Dockerfile                              # Imagen del ETL
│   ├── requirements.txt                        # Dependencias Python
│   └── etl_pipeline.py                         # Script ETL principal
├── docker-compose.yml                          # Orquestación de servicios
└── README.md                                   # Este archivo
```

## Variables de Entorno

Puedes personalizar las credenciales creando un archivo `.env`:

```env
DB_USER=admin_datos
DB_PASS=cali_segura_2025
DB_NAME=catalogo_cali
```

## Conectar desde Power BI

1. Abrir Power BI Desktop
2. Obtener datos > PostgreSQL
3. Servidor: `localhost:5432`
4. Base de datos: `catalogo_cali`
5. Credenciales:
   - Usuario: `admin_datos`
   - Contraseña: `cali_segura_2025`
6. En el navegador, expandir el schema **`catalogo`**
7. Seleccionar las tablas necesarias

**Query recomendada para Power BI**:
```sql
SELECT
    s.*,
    d.nombre_dominio,
    d.sigla,
    a.nombre_area,
    h.nombre_herramienta,
    h.url,
    e.nombre_estado,
    c.nombre_canal
FROM catalogo.fact_servicio s
LEFT JOIN catalogo.dim_dominio d ON s.id_dominio = d.id_dominio
LEFT JOIN catalogo.dim_area a ON s.id_area = a.id_area
LEFT JOIN catalogo.dim_herramienta_tic h ON s.id_herramienta_tic = h.id_herramienta
LEFT JOIN catalogo.dim_estado e ON s.id_estado = e.id_estado
LEFT JOIN catalogo.dim_canal c ON s.id_canal = c.id_canal;
```

## Escalabilidad y Mejoras Futuras

Para escalar este proyecto se recomienda:

1. **Orquestación**: Migrar a Apache Airflow para gestión de workflows
2. **Incremental**: Implementar carga incremental en lugar de TRUNCATE/INSERT
3. **API REST**: Exponer datos vía FastAPI o Django REST Framework
4. **Validación**: Agregar Great Expectations para calidad de datos
5. **Monitoreo**: Implementar logs estructurados y alertas
6. **CI/CD**: Agregar GitHub Actions para pruebas automatizadas

## Licencia

Proyecto de Gobierno de Datos - Alcaldía de Santiago de Cali

## Contacto

Para soporte técnico o consultas, contactar al equipo de DATIC - Subdirección de Innovación Digital.
