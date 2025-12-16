#!/bin/bash

echo "=========================================="
echo "Restarting Docker Services"
echo "=========================================="
echo ""

echo "1. Stopping existing containers..."
docker compose down
echo ""

echo "2. Rebuilding images with fixes..."
docker compose build
echo ""

echo "3. Starting services..."
docker compose up -d
echo ""

echo "4. Waiting for services to start (10 seconds)..."
sleep 10
echo ""

echo "5. Checking container status..."
docker compose ps
echo ""

echo "6. Tailing logs (Ctrl+C to stop)..."
echo "   Watch for any errors..."
echo ""
docker compose logs -f
