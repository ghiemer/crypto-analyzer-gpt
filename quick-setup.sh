#!/bin/bash

# =============================================================================
# QUICK DEVELOPMENT SETUP
# =============================================================================
# This script quickly sets up the development environment
# Run this first time after cloning the repository

echo "🚀 Quick Development Setup for Crypto Analyzer GPT"
echo "=================================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is ready"

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

echo "✅ Git is ready"

# Switch to develop branch
echo "🔄 Switching to develop branch..."
git checkout develop 2>/dev/null || git checkout -b develop

# Make scripts executable
echo "🔧 Setting up permissions..."
chmod +x scripts/setup-dev.sh
chmod +x dev.sh

# Create .env from example if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.dev.example .env
    
    echo ""
    echo "⚠️  IMPORTANT: Configure your .env file now!"
    echo ""
    echo "   Edit .env file and set:"
    echo "   - API_KEY: Choose a secure development API key"
    echo "   - DATABASE_URL: Your Render PostgreSQL connection string"
    echo "   - TG_BOT_TOKEN: Your Telegram bot token (optional)"
    echo "   - TG_CHAT_ID: Your Telegram chat ID (optional)"
    echo ""
    echo "   You can get these from your Render dashboard and Telegram @BotFather"
    echo ""
fi

echo "✅ Quick setup complete!"
echo ""
echo "🔧 Next steps:"
echo "   1. Edit .env file with your configuration"
echo "   2. Run: ./dev.sh setup"
echo "   3. Run: ./dev.sh start"
echo ""
echo "📚 For detailed instructions, see: DEVELOPMENT.md"
