#!/bin/bash

echo "=========================================="
echo "Docker Personal Timeline Debug"
echo "=========================================="
echo ""

echo "1. Checking Docker containers status..."
docker compose ps
echo ""

echo "2. Checking frontend logs (last 30 lines)..."
docker compose logs frontend --tail 30
echo ""

echo "3. Checking QA server logs (last 20 lines)..."
docker compose logs qa --tail 20
echo ""

echo "4. Checking backend logs (last 20 lines)..."
docker compose logs backend --tail 20
echo ""

echo "5. Testing frontend container connectivity..."
docker compose exec -T frontend ls -la /app/public/digital_data/ 2>&1 || echo "Frontend container not running or not accessible"
echo ""

echo "6. Checking if frontend is listening on port 3000..."
docker compose exec -T frontend netstat -tlnp 2>&1 | grep 3000 || echo "Port 3000 not listening or netstat not available"
echo ""

echo "7. Checking MyData volume mount..."
docker compose exec -T frontend ls -la /app/MyData/app_data/ 2>&1 || echo "MyData not mounted or not accessible"
echo ""

echo "=========================================="
echo "URLs to test:"
echo "  Frontend: http://localhost:52692"
echo "  QA Server: http://localhost:57485/test"
echo "=========================================="
