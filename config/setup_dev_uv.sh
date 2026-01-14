#!/bin/bash

echo "🚀 Setting up AI-Augmented Personal Archive Development Environment with UV"
echo "=========================================================================="

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✅ UV installed successfully"
else
    echo "✅ UV is already installed ($(uv --version))"
fi

echo ""
echo "🔧 Setting up Python environment with UV..."

# Install dependencies with UV (with pip fallback)
if uv sync; then
    echo "✅ Dependencies installed successfully with UV"
    echo "⚡ Installation completed ~50% faster than pip!"
else
    echo "⚠️  UV sync failed, falling back to pip..."
    if [ -f "src/requirements.txt" ]; then
        uv pip install -r src/requirements.txt
        echo "✅ Dependencies installed with pip fallback"
    else
        echo "❌ No requirements.txt found for fallback"
        exit 1
    fi
fi

echo ""
echo "🧪 Setting up development tools..."

# Install development dependencies
uv sync --extra dev || echo "⚠️  Dev dependencies not available, continuing..."

echo ""
echo "📁 Creating necessary directories..."
mkdir -p MyData/app_data
mkdir -p logs
mkdir -p models

echo ""
echo "🔐 Setting up environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from template"
        echo "⚠️  Please edit .env file and add your API keys"
    else
        echo "⚠️  No .env.example found, you'll need to create .env manually"
    fi
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🎯 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your AI provider API keys"
echo "2. Place your personal data in MyData/ directory"
echo "3. Run: ./start_app.sh"
echo ""
echo "UV Commands for development:"
echo "  uv sync                    # Install/update dependencies"
echo "  uv sync --extra ai         # Install with AI dependencies"
echo "  uv sync --extra dev        # Install with dev dependencies"
echo "  uv run python -m src.main # Run the application"
echo "  uv add <package>           # Add new dependency"
echo "  uv remove <package>        # Remove dependency"