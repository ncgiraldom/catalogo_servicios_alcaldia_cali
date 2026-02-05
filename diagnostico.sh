#!/bin/bash

echo "===================================================="
echo "DIAGNOSTICO DEL PROYECTO - CATALOGO SERVICIOS CALI"
echo "===================================================="
echo ""

echo "[1/8] Verificando version de Git..."
git log --oneline -1
echo ""

echo "[2/8] Verificando archivos criticos..."
if [ -f "database/00_init_complete.sql" ]; then
    echo "  [OK] database/00_init_complete.sql existe"
else
    echo "  [ERROR] database/00_init_complete.sql NO EXISTE"
fi

if [ -f "data/input/matriz_servicios_consolidada.xlsx" ]; then
    echo "  [OK] data/input/matriz_servicios_consolidada.xlsx existe"
else
    echo "  [ERROR] data/input/matriz_servicios_consolidada.xlsx NO EXISTE"
fi
echo ""

echo "[3/8] Verificando Docker..."
docker --version
echo ""

echo "[4/8] Verificando servicios PostgreSQL locales..."
if command -v systemctl &> /dev/null; then
    systemctl status postgresql 2>/dev/null || echo "  PostgreSQL no instalado localmente (OK)"
elif command -v brew &> /dev/null; then
    brew services list | grep postgres || echo "  PostgreSQL no instalado localmente (OK)"
else
    echo "  No se puede verificar servicios locales"
fi
echo ""

echo "[5/8] Verificando puertos en uso..."
echo "Puertos 5432 y 5433:"
if command -v lsof &> /dev/null; then
    lsof -i :5432 -i :5433 || echo "  Puertos libres"
elif command -v netstat &> /dev/null; then
    netstat -tuln | grep -E ":5432|:5433" || echo "  Puertos libres"
else
    echo "  No se puede verificar puertos"
fi
echo ""

echo "[6/8] Verificando contenedores Docker..."
docker-compose ps
echo ""

echo "[7/8] Logs del ETL:"
docker logs catalogo_etl
echo ""

echo "[8/8] Verificando datos en PostgreSQL..."
docker exec catalogo_db psql -U admin_datos -d catalogo_cali -c "SET search_path TO catalogo; SELECT 'fact_servicio' as tabla, COUNT(*) as registros FROM fact_servicio;"
echo ""

echo "===================================================="
echo "DIAGNOSTICO COMPLETADO"
echo "===================================================="
echo ""
echo "Si ves errores arriba, consulta TROUBLESHOOTING.md"
