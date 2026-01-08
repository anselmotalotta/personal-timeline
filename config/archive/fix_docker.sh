#!/bin/bash

# Fix Docker Port Conflict
# Run this script to stop existing containers and rebuild

cd /workspace/personal-timeline

echo "========================================"
echo "🛑 Stopping all containers..."
echo "========================================"
docker-compose down

echo ""
echo "========================================"
echo "🧹 Cleaning up stopped containers..."
echo "========================================"
docker container prune -f

echo ""
echo "========================================"
echo "🏗️ Rebuilding services..."
echo "========================================"
docker-compose build

echo ""
echo "========================================"
echo "🚀 Starting services in detached mode..."
echo "========================================"
docker-compose up -d

echo ""
echo "========================================"
echo "✅ Done! Current status:"
echo "========================================"
docker-compose ps

echo ""
echo "========================================"
echo "📊 Service URLs:"
echo "========================================"
echo "Frontend: http://localhost:52692"
echo "QA API:   http://localhost:57485"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop:      docker-compose down"
echo "========================================"
