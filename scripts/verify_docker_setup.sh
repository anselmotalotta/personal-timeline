#!/bin/bash

echo "=========================================="
echo "Docker Setup Verification"
echo "=========================================="
echo ""

cd /workspace/personal-timeline

echo "✓ Checking data directory structure..."
echo ""

if [ -d "MyData" ]; then
    echo "  ✅ MyData/ exists"
else
    echo "  ❌ MyData/ does NOT exist"
    exit 1
fi

if [ -L "MyData/facebook" ]; then
    echo "  ✅ MyData/facebook symlink exists"
    target=$(readlink MyData/facebook)
    echo "     → Points to: $target"
else
    echo "  ❌ MyData/facebook symlink NOT found"
fi

if [ -d "MyData/facebook/posts" ]; then
    json_count=$(find MyData/facebook/posts -name "*.json" -type f | wc -l)
    echo "  ✅ MyData/facebook/posts/ accessible ($json_count JSON files)"
else
    echo "  ❌ MyData/facebook/posts/ NOT accessible"
fi

if [ -d "MyData/app_data" ]; then
    echo "  ✅ MyData/app_data/ exists"
    if [ -f "MyData/app_data/raw_data.db" ]; then
        echo "     ✅ raw_data.db found"
    else
        echo "     ⚠️  raw_data.db NOT found (will be created on first run)"
    fi
else
    echo "  ❌ MyData/app_data/ does NOT exist"
fi

echo ""
echo "✓ Checking docker-compose.yml..."
echo ""

if [ -f "docker-compose.yml" ]; then
    echo "  ✅ docker-compose.yml exists"
    
    if grep -q "./MyData:/app/MyData" docker-compose.yml; then
        echo "  ✅ Volume mounts configured correctly"
    else
        echo "  ⚠️  Volume mounts may need review"
    fi
else
    echo "  ❌ docker-compose.yml NOT found"
    exit 1
fi

echo ""
echo "✓ Checking source files..."
echo ""

if [ -f "src/common/bootstrap/data_source.json" ]; then
    echo "  ✅ data_source.json exists"
    
    if grep -q '"input_directory": "MyData/facebook"' src/common/bootstrap/data_source.json; then
        echo "  ✅ Facebook path configured correctly (relative)"
    elif grep -q '"/workspace/MyData/facebook"' src/common/bootstrap/data_source.json; then
        echo "  ⚠️  Facebook path uses absolute path (may not work in Docker)"
    else
        echo "  ⚠️  Facebook path configuration unclear"
    fi
else
    echo "  ❌ data_source.json NOT found"
fi

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo ""

# Count issues
issues=0

[ ! -d "MyData" ] && ((issues++))
[ ! -L "MyData/facebook" ] && ((issues++))
[ ! -d "MyData/facebook/posts" ] && ((issues++))
[ ! -d "MyData/app_data" ] && ((issues++))
[ ! -f "docker-compose.yml" ] && ((issues++))

if [ $issues -eq 0 ]; then
    echo "✅ All checks passed! Ready to run:"
    echo ""
    echo "   bash RESTART_DOCKER.sh"
    echo ""
else
    echo "❌ Found $issues issue(s). Please review the output above."
    echo ""
    echo "See DOCKER_DATA_SETUP.md for setup instructions."
    echo ""
fi

echo "=========================================="
