#!/bin/bash

echo "🧪 Testing AI Personal Archive Deployment"
echo "========================================="

# Test 1: Check if required files exist
echo "📋 Checking required files..."

required_files=(".env.example" "docker-compose.yml" "start_app.sh" "DEPLOYMENT_GUIDE.md")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
    else
        echo "   ❌ $file missing"
        exit 1
    fi
done

# Test 2: Check if start script is executable
if [ -x "start_app.sh" ]; then
    echo "   ✅ start_app.sh is executable"
else
    echo "   ❌ start_app.sh not executable - run: chmod +x start_app.sh"
    exit 1
fi

# Test 3: Check Docker Compose syntax
echo ""
echo "🐳 Validating Docker Compose configuration..."
if docker compose config > /dev/null 2>&1; then
    echo "   ✅ docker-compose.yml syntax is valid"
else
    echo "   ❌ docker-compose.yml has syntax errors"
    docker compose config
    exit 1
fi

# Test 4: Check environment variables
echo ""
echo "🔧 Checking environment configuration..."
if [ -f ".env" ]; then
    echo "   ✅ .env file exists"
    
    # Check for placeholder values
    if grep -q "your_.*_api_key_here" .env; then
        echo "   ⚠️  .env contains placeholder values - update with real API keys"
    else
        echo "   ✅ .env appears to have real values"
    fi
else
    echo "   ⚠️  No .env file found - will run in limited mode"
fi

# Test 5: Check if ports are available
echo ""
echo "🌐 Checking port availability..."
ports=(52692 57485 8000 8086 5432 5433)
for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "   ⚠️  Port $port is in use - may cause conflicts"
    else
        echo "   ✅ Port $port is available"
    fi
done

# Test 6: Check Docker status
echo ""
echo "🐳 Checking Docker status..."
if docker info > /dev/null 2>&1; then
    echo "   ✅ Docker is running"
    echo "   📊 Docker version: $(docker --version)"
else
    echo "   ❌ Docker is not running - start Docker Desktop first"
    exit 1
fi

# Test 7: Check MyData directory
echo ""
echo "📁 Checking data directory..."
if [ -d "../MyData" ]; then
    echo "   ✅ MyData directory exists"
    echo "   📊 Size: $(du -sh ../MyData 2>/dev/null | cut -f1)"
else
    echo "   ℹ️  MyData directory will be created automatically"
fi

echo ""
echo "🎉 Deployment test completed successfully!"
echo ""
echo "🚀 Ready to start the application:"
echo "   ./start_app.sh"
echo ""
echo "📖 For detailed setup instructions:"
echo "   cat DEPLOYMENT_GUIDE.md"