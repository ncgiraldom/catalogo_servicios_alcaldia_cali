# Guía de Solución de Problemas - No se Cargan los Datos

Si después de ejecutar `docker-compose up -d` las tablas aparecen vacías, sigue estos pasos:

## Paso 1: Verificar que tienes la última versión

```bash
git pull origin main
git log --oneline -1
```

Deberías ver el commit: `nuevos cambios en puertos` o `actualizacion de proceso`

## Paso 2: Verificar que los archivos clave existen

```bash
# En Windows PowerShell o CMD
dir database\00_init_complete.sql
dir data\input\matriz_servicios_consolidada.xlsx

# En Linux/Mac
ls -la database/00_init_complete.sql
ls -la data/input/matriz_servicios_consolidada.xlsx
```

**Si el archivo Excel NO existe**, este es el problema. El archivo `matriz_servicios_consolidada.xlsx` debe estar en `data/input/`.

## Paso 3: Limpiar Docker completamente

```bash
# Detener y eliminar TODO (contenedores, volúmenes, redes)
docker-compose down -v

# Verificar que no queden contenedores
docker ps -a

# Si hay contenedores del proyecto, eliminarlos manualmente
docker rm -f catalogo_db catalogo_etl catalogo_nocodb catalogo_pgadmin

# Verificar volúmenes
docker volume ls | findstr catalogo

# Eliminar volúmenes si existen
docker volume rm catalogo_servicios_alcaldia_cali_postgres_data
docker volume rm catalogo_servicios_alcaldia_cali_nocodb_data
```

## Paso 4: Verificar conflicto de puertos PostgreSQL

### Verificar si hay PostgreSQL local corriendo:

**Windows:**
```powershell
# Verificar servicio
Get-Service | Where-Object {$_.Name -like "*postgres*"}

# Verificar puerto 5432
netstat -ano | findstr :5432
```

**Si hay PostgreSQL local corriendo:**

Opción A - Detenerlo temporalmente:
```powershell
# Como Administrador
Stop-Service postgresql-x64-14
```

Opción B - Usar puerto alternativo (5433):
El proyecto ya está configurado para usar 5433 si hay conflicto.

## Paso 5: Levantar servicios desde cero

```bash
# Construir imagen del ETL
docker-compose build --no-cache etl

# Levantar todos los servicios
docker-compose up -d

# Ver logs en tiempo real
docker logs catalogo_etl -f
```

## Paso 6: Verificar logs del ETL

```bash
# Ver logs del ETL
docker logs catalogo_etl

# Verificar logs de la base de datos
docker logs catalogo_db
```

### ✅ Logs exitosos del ETL:

Deberías ver esto:
```
⏳ Esperando conexión a base de datos...
✅ Conexión exitosa a PostgreSQL
📊 Limpiando y cargando datos maestros...
   ✓ Dominios cargados (4 registros)
   ✓ Áreas cargadas (14 registros)
   ✓ Canales cargados (7 registros)
   ✓ Herramientas TIC cargadas (10 registros)
   ✓ Ubicaciones cargadas (5 registros)
   ✓ Estados cargados (3 registros)
   ✓ Requisitos maestros cargados (26 registros)
🚀 Iniciando procesamiento de: /app/data/input/matriz_servicios_consolidada.xlsx
   📄 Archivo leído: 54 registros encontrados
   ✓ 54 servicios procesados
💾 Cargando FACT_SERVICIO...
   ✓ 54 servicios cargados
💾 Cargando REL_SERVICIO_REQUISITO...
   ✓ 70 relaciones servicio-requisito cargadas
💾 Cargando REL_SERVICIO_UBICACION...
   ✓ 54 relaciones servicio-ubicación cargadas
✅ ¡PROCESO ETL FINALIZADO CON ÉXITO!
```

### ❌ Errores comunes:

**Error 1: "No se encontró el archivo"**
```
❌ No se encontró el archivo en /app/data/input/matriz_servicios_consolidada.xlsx
```
**Solución**: El archivo Excel no está en `data/input/`. Cópialo desde el repositorio.

**Error 2: "Connection refused"**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```
**Solución**: PostgreSQL no está listo. Espera 10 segundos y ejecuta:
```bash
docker-compose restart etl
```

**Error 3: "relation does not exist"**
```
psycopg2.errors.UndefinedTable: relation "catalogo.fact_servicio" does not exist
```
**Solución**: El script de inicialización no se ejecutó. Verifica que `database/00_init_complete.sql` existe y ejecuta:
```bash
docker-compose down -v
docker-compose up -d
```

## Paso 7: Verificar que los datos se cargaron

```bash
# Contar servicios
docker exec catalogo_db psql -U admin_datos -d catalogo_cali -c "SELECT COUNT(*) FROM catalogo.fact_servicio;"

# Debería mostrar: 54

# Ver todas las tablas con sus registros
docker exec catalogo_db psql -U admin_datos -d catalogo_cali -c "
SET search_path TO catalogo;
SELECT 'dim_dominio' as tabla, COUNT(*) as registros FROM dim_dominio
UNION ALL SELECT 'dim_area', COUNT(*) FROM dim_area
UNION ALL SELECT 'dim_canal', COUNT(*) FROM dim_canal
UNION ALL SELECT 'dim_herramienta_tic', COUNT(*) FROM dim_herramienta_tic
UNION ALL SELECT 'dim_ubicacion', COUNT(*) FROM dim_ubicacion
UNION ALL SELECT 'dim_estado', COUNT(*) FROM dim_estado
UNION ALL SELECT 'dim_requisito', COUNT(*) FROM dim_requisito
UNION ALL SELECT 'fact_servicio', COUNT(*) FROM fact_servicio
UNION ALL SELECT 'rel_servicio_requisito', COUNT(*) FROM rel_servicio_requisito
UNION ALL SELECT 'rel_servicio_ubicacion', COUNT(*) FROM rel_servicio_ubicacion;
"
```

**Resultado esperado:**
```
         tabla          | registros
------------------------+-----------
 dim_dominio            |         4
 dim_area               |        14
 dim_canal              |         7
 dim_herramienta_tic    |        10
 dim_ubicacion          |         5
 dim_estado             |         3
 dim_requisito          |        26
 fact_servicio          |        54
 rel_servicio_requisito |        70
 rel_servicio_ubicacion |        54
```

## Paso 8: Ejecutar ETL manualmente (si todo lo demás falla)

```bash
# Si el ETL no se ejecutó automáticamente
docker-compose run --rm etl
```

## Checklist Completo

- [ ] Ejecuté `git pull origin main`
- [ ] El archivo `database/00_init_complete.sql` existe
- [ ] El archivo `data/input/matriz_servicios_consolidada.xlsx` existe
- [ ] Ejecuté `docker-compose down -v` para limpiar
- [ ] No hay PostgreSQL local usando el puerto 5432 (o cambié a puerto 5433)
- [ ] Ejecuté `docker-compose up -d`
- [ ] Vi los logs con `docker logs catalogo_etl`
- [ ] El ETL mostró "✅ ¡PROCESO ETL FINALIZADO CON ÉXITO!"
- [ ] Verifiqué con psql que hay 54 servicios

## Información de Contacto

Si después de seguir todos estos pasos aún no funciona, comparte:

1. Output de `docker logs catalogo_etl`
2. Output de `docker logs catalogo_db | tail -50`
3. Output de `docker-compose ps`
4. Tu sistema operativo y versión de Docker

## Puertos Utilizados

- **5432**: PostgreSQL local (si lo tienes instalado)
- **5433**: PostgreSQL en Docker (configurado para evitar conflicto)
- **8080**: NocoDB
- **5050**: pgAdmin

## Conexión desde Power BI

Si PostgreSQL local está corriendo en 5432:
```
Servidor: localhost:5433
Base de datos: catalogo_cali
Usuario: admin_datos
Contraseña: cali_segura_2025
```

Si detuviste PostgreSQL local:
```
Servidor: localhost:5432
Base de datos: catalogo_cali
Usuario: admin_datos
Contraseña: cali_segura_2025
```
