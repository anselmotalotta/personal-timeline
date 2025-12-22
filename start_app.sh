#!/bin/bash

echo "🚀 Starting AI-Augmented Personal Archive"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    echo "   1. Open Docker Desktop"
    echo "   2. Wait for it to fully start"
    echo "   3. Run this script again"
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Create MyData directory if it doesn't exist
if [ ! -d "../MyData" ]; then
    echo "📁 Creating MyData directory..."
    mkdir -p ../MyData/app_data
    echo "   Sample data will be created automatically"
fi

echo "🔧 Starting services..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "🌐 Application URLs:"
echo "   Main App:     http://localhost:52692"
echo "   AI Chat:      http://localhost:57485" 
echo "   Backend API:  http://localhost:8000"
echo "   AI Services:  http://localhost:8086"

echo ""
echo "📊 To view logs: docker-compose logs -f"
echo "🛑 To stop:      docker-compose down"
echo ""
echo "🎉 Application should be ready in ~30 seconds!"