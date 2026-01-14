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

# Check for .env file and provide guidance
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found - AI features will be limited"
    echo "   📝 To enable AI features:"
    echo "   1. Copy: cp .env.example .env"
    echo "   2. Edit .env and add your API keys"
    echo "   3. Restart: ./start_app.sh"
    echo ""
    echo "   🔑 Get API keys from:"
    echo "   • OpenAI: https://platform.openai.com/api-keys"
    echo "   • Anthropic: https://console.anthropic.com/"
    echo "   • Google: https://makersuite.google.com/app/apikey"
    echo ""
    read -p "   Continue without AI features? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "   Setup cancelled. Add API keys and try again."
        exit 1
    fi
else
    echo "✅ Found .env configuration file"
    
    # Check if any API keys are configured
    api_keys_found=false
    if grep -q "^OPENAI_API_KEY=sk-" .env 2>/dev/null; then
        echo "   🔑 OpenAI API key configured"
        api_keys_found=true
    fi
    if grep -q "^ANTHROPIC_API_KEY=sk-ant-" .env 2>/dev/null; then
        echo "   🔑 Anthropic API key configured"
        api_keys_found=true
    fi
    if grep -q "^GOOGLE_API_KEY=.*" .env 2>/dev/null && ! grep -q "^GOOGLE_API_KEY=your_google_api_key_here" .env; then
        echo "   🔑 Google API key configured"
        api_keys_found=true
    fi
    
    if [ "$api_keys_found" = false ]; then
        echo "   ⚠️  No valid API keys found in .env file"
        echo "   📝 Edit .env and add at least one API key for AI features"
    fi
fi

echo ""

# Create MyData directory if it doesn't exist
if [ ! -d "../MyData" ]; then
    echo "📁 Creating MyData directory..."
    mkdir -p ../MyData/app_data
    echo "   Sample data will be created automatically"
fi

echo "🔧 Starting services..."
docker compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

echo ""
echo "🔍 Checking service status..."
docker compose ps

echo ""
echo "🌐 Application URLs:"
echo "   📱 Main App:      http://localhost:52692"
echo "   🤖 AI Chat:       http://localhost:57485" 
echo "   ⚙️  Backend API:   http://localhost:8000"
echo "   🧠 AI Services:   http://localhost:8086"
echo "   📊 Health Check:  http://localhost:8086/health"

echo ""
echo "💡 Useful commands:"
echo "   📊 View logs:     docker compose logs -f"
echo "   🛑 Stop services: docker compose down"
echo "   🔄 Restart:       docker compose restart"

echo ""
if [ -f ".env" ] && [ "$api_keys_found" = true ]; then
    echo "🎉 Application ready with AI features!"
else
    echo "🎉 Application ready (limited mode - add API keys for AI features)"
fi
echo ""
echo "   Visit http://localhost:52692 to get started"
echo "   The status badge will show AI feature availability"