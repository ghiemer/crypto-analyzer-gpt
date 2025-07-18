#!/bin/bash

# =============================================================================
# CRYPTO ANALYZER GPT - DEVELOPMENT SETUP SCRIPT
# =============================================================================

set -e  # Exit on any error

echo "🚀 Setting up Crypto Analyzer GPT Development Environment"
echo "============================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if we're on develop branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo "⚠️  Warning: You're not on the 'develop' branch (current: $CURRENT_BRANCH)"
    echo "   It's recommended to develop on the 'develop' branch to keep 'main' stable."
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "🔄 Switch to develop branch with: git checkout develop"
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from example..."
    cp .env.dev.example .env
    echo "⚠️  Please edit .env file with your configuration before starting!"
    echo "   Most importantly:"
    echo "   - API_KEY: Set a secure API key"
    echo "   - DATABASE_URL: Use your Render PostgreSQL URL"
    echo "   - TG_BOT_TOKEN & TG_CHAT_ID: For Telegram integration (optional)"
    echo ""
    read -p "Press Enter when you've configured .env file..."
fi

# Validate required environment variables
echo "🔍 Validating configuration..."
source .env

if [ -z "$API_KEY" ] || [ "$API_KEY" = "your-development-api-key-here" ]; then
    echo "❌ Please set a valid API_KEY in .env file"
    exit 1
fi

if [ -z "$DATABASE_URL" ] || [ "$DATABASE_URL" = "your-render-database-url-here" ]; then
    echo "❌ Please set a valid DATABASE_URL in .env file"
    echo "   Use your Render PostgreSQL connection string"
    exit 1
fi

echo "✅ Configuration looks good!"

# Build development container
echo "🔨 Building development container..."
docker-compose -f docker-compose.dev.yml build

# Start the development environment
echo "🚀 Starting development environment..."
docker-compose -f docker-compose.dev.yml up -d

echo ""
echo "✅ Development environment started successfully!"
echo ""
echo "📊 Access points:"
echo "   • API: http://localhost:8000"
echo "   • Health: http://localhost:8000/health"
echo "   • Docs: http://localhost:8000/docs"
echo ""
echo "🔧 Development commands:"
echo "   • View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "   • Stop: docker-compose -f docker-compose.dev.yml down"
echo "   • Restart: docker-compose -f docker-compose.dev.yml restart"
echo "   • Shell: docker-compose -f docker-compose.dev.yml exec crypto-analyzer-dev bash"
echo ""
echo "📝 Test API with:"
echo "   curl -H \"X-API-Key: $API_KEY\" http://localhost:8000/health"
echo ""

# Optional: Show logs
read -p "Show live logs now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📄 Showing live logs (Ctrl+C to exit):"
    docker-compose -f docker-compose.dev.yml logs -f
fi
