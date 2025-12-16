
#!/bin/bash

echo "Testing Docker configuration..."
echo "================================"

# Create a simple test to verify Dockerfile works
cat > /tmp/test_requirements.txt << 'EOF'
geopy>=2.4.0
Flask-Cors>=5.0.0
EOF

cat > /tmp/test_Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Copy test requirements
COPY test_requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r test_requirements.txt

# Test imports
RUN python -c "import geopy; from flask_cors import CORS; print('✅ All imports work')"
EOF

echo "1. Created test Dockerfile and requirements"
echo "2. Testing basic Docker build..."

cd /tmp
if docker build -t test-deps -f test_Dockerfile . 2>&1 | grep -q "✅ All imports work"; then
    echo "✅ Docker build test PASSED - dependencies install correctly"
else
    echo "❌ Docker build test FAILED"
    docker build -t test-deps -f test_Dockerfile . 2>&1 | tail -20
fi

echo ""
echo "For the actual project, run these commands:"
echo "==========================================="
echo "cd ~/workspace/FacebookPostDownloader/personal-timeline"
echo ""
echo "# OPTION 1: Complete clean rebuild"
echo "docker compose down"
echo "docker builder prune -a -f"
echo "docker compose up -d --build --no-cache"
echo ""
echo "# OPTION 2: Rebuild specific services"
echo "docker compose build --no-cache backend"
echo "docker compose build --no-cache qa"
echo "docker compose up -d"
echo ""
echo "# Check logs after rebuild:"
echo "docker compose logs -f backend"
