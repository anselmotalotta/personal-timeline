

#!/bin/bash

echo "Docker Diagnostic Script"
echo "========================"

# Check current state
echo "1. Checking running containers:"
docker compose ps

echo ""
echo "2. Checking container logs:"
echo "Backend logs (last 10 lines):"
docker compose logs --tail=10 backend 2>/dev/null || echo "Backend not running"

echo ""
echo "QA logs (last 10 lines):"
docker compose logs --tail=10 qa 2>/dev/null || echo "QA not running"

echo ""
echo "3. Checking Docker images:"
docker images | grep personal-timeline

echo ""
echo "4. Testing Docker build manually:"
echo "Creating test build to check dependency installation..."

cat > /tmp/test_build.py << 'EOF'
import subprocess
import sys

def test_build():
    print("Testing Docker build process...")
    
    # Create a simple test Dockerfile
    test_dockerfile = """
FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir geopy flask-cors
RUN python -c "import geopy; from flask_cors import CORS; print('SUCCESS: Dependencies installed')"
"""
    
    with open("/tmp/Dockerfile.test", "w") as f:
        f.write(test_dockerfile)
    
    result = subprocess.run(
        ["docker", "build", "-t", "test-deps", "-f", "/tmp/Dockerfile.test", "/tmp"],
        capture_output=True,
        text=True
    )
    
    if "SUCCESS: Dependencies installed" in result.stdout:
        print("✅ Basic Docker dependency installation works")
        return True
    else:
        print("❌ Docker dependency installation failed")
        print("STDOUT:", result.stdout[-500:] if result.stdout else "(empty)")
        print("STDERR:", result.stderr[-500:] if result.stderr else "(empty)")
        return False

if __name__ == "__main__":
    success = test_build()
    sys.exit(0 if success else 1)
EOF

python /tmp/test_build.py

echo ""
echo "5. Recommended fix sequence:"
echo "   # Stop everything"
echo "   docker compose down"
echo ""
echo "   # Remove all images"
echo "   docker rmi -f personal-timeline-backend personal-timeline-qa personal-timeline-frontend"
echo ""
echo "   # Clear build cache"
echo "   docker builder prune -a -f"
echo ""
echo "   # Rebuild with verbose output"
echo "   docker compose build --no-cache --progress=plain 2>&1 | tee build.log"
echo ""
echo "   # Check if dependencies were installed"
echo "   grep -i 'geopy\|flask-cors\|success\|error' build.log | tail -20"
echo ""
echo "6. Alternative: Single-stage build (simpler)"
echo "   Change Dockerfile to single stage without virtual env copy"
echo "   Just install dependencies directly in final image"

