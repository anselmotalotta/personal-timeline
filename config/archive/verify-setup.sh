#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║              🔍 VERIFYING PERSONAL TIMELINE SETUP                  ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if MyData directory exists
echo "📂 Checking MyData directory..."
if [ -d "/workspace/MyData" ]; then
    echo "   ✅ /workspace/MyData exists"
else
    echo "   ❌ /workspace/MyData not found!"
    exit 1
fi

# Check Facebook posts
echo ""
echo "📊 Checking Facebook posts..."
if [ -d "/workspace/MyData/facebook/posts" ]; then
    post_count=$(find /workspace/MyData/facebook/posts -name "*.json" | wc -l)
    echo "   ✅ Found $post_count JSON files"
    
    if [ -d "/workspace/MyData/facebook/posts/media" ]; then
        media_count=$(find /workspace/MyData/facebook/posts/media -type f | wc -l)
        echo "   ✅ Found $media_count media files"
    fi
else
    echo "   ❌ Facebook posts directory not found!"
    exit 1
fi

# Check app_data
echo ""
echo "🗄️  Checking app_data..."
if [ -d "/workspace/MyData/app_data" ]; then
    echo "   ✅ /workspace/MyData/app_data exists"
    
    if [ -f "/workspace/MyData/app_data/episodes.json" ]; then
        echo "   ✅ Sample data present"
    fi
else
    echo "   ⚠️  app_data directory not found (will be created on first run)"
fi

# Check docker-compose configuration
echo ""
echo "🐋 Checking Docker configuration..."
if [ -f "/workspace/personal-timeline/docker-compose.yml" ]; then
    echo "   ✅ docker-compose.yml exists"
    
    if grep -q "/workspace/MyData/" /workspace/personal-timeline/docker-compose.yml; then
        echo "   ✅ Configured to use /workspace/MyData/"
    else
        echo "   ❌ Not configured for MyData!"
        exit 1
    fi
else
    echo "   ❌ docker-compose.yml not found!"
    exit 1
fi

# Check Docker is available
echo ""
echo "🐳 Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker is available"
    docker --version
else
    echo "   ❌ Docker not found!"
    exit 1
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ ALL CHECKS PASSED!"
echo ""
echo "🚀 Ready to run:"
echo "   cd /workspace/personal-timeline"
echo "   docker compose up -d frontend"
echo ""
echo "   Visit: http://localhost:52692"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
