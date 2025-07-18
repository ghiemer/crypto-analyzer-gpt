#!/bin/bash

# =============================================================================
# CRYPTO ANALYZER GPT - DEVELOPMENT COMMANDS
# =============================================================================

set -e

COMPOSE_FILE="docker-compose.dev.yml"

function help() {
    echo "🚀 Crypto Analyzer GPT - Development Commands"
    echo "=============================================="
    echo ""
    echo "Setup:"
    echo "  ./dev.sh setup          Setup development environment"
    echo ""
    echo "Container Management:"
    echo "  ./dev.sh start          Start development container"
    echo "  ./dev.sh stop           Stop development container"
    echo "  ./dev.sh restart        Restart development container"
    echo "  ./dev.sh build          Rebuild development container"
    echo "  ./dev.sh logs           Show live logs"
    echo "  ./dev.sh status         Show container status"
    echo ""
    echo "Development:"
    echo "  ./dev.sh shell          Enter container shell"
    echo "  ./dev.sh test           Run tests"
    echo "  ./dev.sh lint           Run linting"
    echo "  ./dev.sh format         Format code"
    echo ""
    echo "API Testing:"
    echo "  ./dev.sh health         Test health endpoint"
    echo "  ./dev.sh candles        Test candles endpoint"
    echo "  ./dev.sh docs           Open API documentation"
    echo ""
    echo "Database:"
    echo "  ./dev.sh db-status      Check database connection"
    echo "  ./dev.sh redis          Start local Redis (optional)"
    echo ""
    echo "Cleanup:"
    echo "  ./dev.sh clean          Stop and remove containers"
    echo "  ./dev.sh clean-all      Clean everything (containers, images, volumes)"
}

function setup() {
    echo "🔧 Running setup script..."
    ./scripts/setup-dev.sh
}

function start() {
    echo "🚀 Starting development environment..."
    docker-compose -f $COMPOSE_FILE up -d
    echo "✅ Started! API available at http://localhost:8000"
}

function stop() {
    echo "🛑 Stopping development environment..."
    docker-compose -f $COMPOSE_FILE down
}

function restart() {
    echo "🔄 Restarting development environment..."
    docker-compose -f $COMPOSE_FILE restart
}

function build() {
    echo "🔨 Building development container..."
    docker-compose -f $COMPOSE_FILE build --no-cache
}

function logs() {
    echo "📄 Showing live logs (Ctrl+C to exit)..."
    docker-compose -f $COMPOSE_FILE logs -f
}

function status() {
    echo "📊 Container status:"
    docker-compose -f $COMPOSE_FILE ps
}

function shell() {
    echo "🐚 Entering container shell..."
    docker-compose -f $COMPOSE_FILE exec crypto-analyzer-dev bash
}

function test() {
    echo "🧪 Running tests..."
    docker-compose -f $COMPOSE_FILE exec crypto-analyzer-dev python -m pytest tests/ -v
}

function lint() {
    echo "🔍 Running linting..."
    docker-compose -f $COMPOSE_FILE exec crypto-analyzer-dev flake8 app/
}

function format() {
    echo "🎨 Formatting code..."
    docker-compose -f $COMPOSE_FILE exec crypto-analyzer-dev black app/
}

function health() {
    echo "🏥 Testing health endpoint..."
    if [ -f ".env" ]; then
        source .env
        curl -H "X-API-Key: $API_KEY" http://localhost:8000/health | jq .
    else
        echo "❌ .env file not found. Please run './dev.sh setup' first."
    fi
}

function candles() {
    echo "📊 Testing candles endpoint..."
    if [ -f ".env" ]; then
        source .env
        curl -H "X-API-Key: $API_KEY" "http://localhost:8000/candles?symbol=BTCUSDT&limit=5" | jq .
    else
        echo "❌ .env file not found. Please run './dev.sh setup' first."
    fi
}

function docs() {
    echo "📚 Opening API documentation..."
    open http://localhost:8000/docs
}

function db_status() {
    echo "🗃️ Checking database connection..."
    docker-compose -f $COMPOSE_FILE exec crypto-analyzer-dev python -c "
from app.core.database import engine
if engine:
    try:
        with engine.connect() as conn:
            print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
else:
    print('❌ Database not configured')
"
}

function redis() {
    echo "🔴 Starting local Redis container..."
    docker-compose -f $COMPOSE_FILE --profile redis up -d redis-dev
    echo "✅ Redis started on localhost:6379"
}

function clean() {
    echo "🧹 Cleaning up containers..."
    docker-compose -f $COMPOSE_FILE down --remove-orphans
}

function clean_all() {
    echo "🧹 Cleaning everything (containers, images, volumes)..."
    docker-compose -f $COMPOSE_FILE down --remove-orphans --volumes --rmi all
}

# Main command dispatcher
case "$1" in
    setup) setup ;;
    start) start ;;
    stop) stop ;;
    restart) restart ;;
    build) build ;;
    logs) logs ;;
    status) status ;;
    shell) shell ;;
    test) test ;;
    lint) lint ;;
    format) format ;;
    health) health ;;
    candles) candles ;;
    docs) docs ;;
    db-status) db_status ;;
    redis) redis ;;
    clean) clean ;;
    clean-all) clean_all ;;
    *) help ;;
esac
