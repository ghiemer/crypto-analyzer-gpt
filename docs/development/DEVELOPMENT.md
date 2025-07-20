# =============================================================================
# CRYPTO ANALYZER GPT - DEVELOPMENT ENVIRONMENT
# =============================================================================

This document explains how to set up and use the local development environment
for the Crypto Analyzer GPT project.

## 🎯 Overview

The development environment provides:
- **Docker-based setup** for consistency across different machines
- **Hot reloading** for rapid development cycles
- **External database connection** to your Render PostgreSQL instance
- **Isolated develop branch** to keep production (main) branch stable
- **All production features** available for testing

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Development Setup             │
├─────────────────────────────────────────┤
│  Local Docker Container                 │
│  ├── FastAPI (port 8000)               │
│  ├── Hot reloading enabled             │
│  ├── Development dependencies          │
│  └── Volume mounts for live updates    │
│                                         │
│  External Services (Render)            │
│  ├── PostgreSQL Database               │
│  ├── Redis Cache (optional)            │
│  └── All production APIs               │
└─────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites

- **Docker Desktop** installed and running
- **Git** for version control
- **curl** and **jq** for API testing (optional)

### 2. Setup Development Environment

```bash
# Ensure you're on the develop branch
git checkout develop

# Run the setup script
./scripts/setup-dev.sh
```

The setup script will:
1. Check if you're on the `develop` branch
2. Create `.env` file from template if it doesn't exist
3. Build the development Docker container
4. Start the development environment

### 3. Configure Environment Variables

Edit the `.env` file with your settings:

```bash
# Required
API_KEY=your-development-api-key-here
DATABASE_URL=your-render-postgresql-url

# Optional but recommended
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-telegram-chat-id
NEWS_API_KEY=your-newsapi-key
```

## 🔧 Development Commands

Use the `./dev.sh` script for all development tasks:

### Container Management
```bash
./dev.sh start          # Start development environment
./dev.sh stop           # Stop development environment
./dev.sh restart        # Restart containers
./dev.sh build          # Rebuild containers
./dev.sh logs           # Show live logs
./dev.sh status         # Show container status
```

### Development Tasks
```bash
./dev.sh shell          # Enter container shell
./dev.sh test           # Run tests
./dev.sh lint           # Run code linting
./dev.sh format         # Format code with Black
```

### API Testing
```bash
./dev.sh health         # Test health endpoint
./dev.sh candles        # Test candles endpoint with Bitcoin data
./dev.sh docs           # Open API documentation
```

### Database Operations
```bash
./dev.sh db-status      # Check database connection
./dev.sh redis          # Start local Redis (if needed)
```

## 📊 API Testing

Once the environment is running, you can test the API:

### Health Check
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/health
```

### Get Bitcoin Candles with Indicators
```bash
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/candles?symbol=BTCUSDT&indicators=rsi14,sma50&limit=10"
```

### Access API Documentation
Open http://localhost:8000/docs in your browser for interactive API docs.

## 🔄 Development Workflow

### 1. Code Changes
- Edit files in `app/`, `config/`, or `tests/`
- Changes are automatically reflected due to volume mounts
- FastAPI will auto-reload on code changes

### 2. Testing Features
```bash
# Test specific functionality
./dev.sh test

# Check code quality
./dev.sh lint

# Format code
./dev.sh format
```

### 3. Database Testing
- Uses your **external Render PostgreSQL** database
- Same data as production for realistic testing
- No local database setup required

### 4. Telegram Integration Testing
- Configure your own test bot or use production bot
- Test alerts and signals in your personal chat
- Won't interfere with production notifications

## 🔧 Configuration Options

### Environment Variables

```bash
# Core settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# Database (use external Render database)
DATABASE_URL=postgresql://user:pass@host:port/db

# Cache (can be disabled for development)
CACHE_ENABLED=false
REDIS_URL=redis://localhost:6379/0

# Rate limiting (relaxed for development)
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=60
```

### Optional Local Redis

If you want to test caching locally:

```bash
# Start local Redis
./dev.sh redis

# Update .env
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

## 🚨 Troubleshooting

### Container Won't Start
```bash
# Check Docker status
docker info

# Rebuild container
./dev.sh build

# Check logs
./dev.sh logs
```

### Database Connection Issues
```bash
# Test database connection
./dev.sh db-status

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### API Key Issues
```bash
# Test health endpoint
./dev.sh health

# Verify API_KEY in .env
cat .env | grep API_KEY
```

### Port Conflicts
If port 8000 is already in use:
1. Stop the conflicting service
2. Or modify `docker-compose.dev.yml` to use a different port

## 🔄 Branch Strategy

- **main**: Production-ready code deployed to Render
- **develop**: Development branch for new features
- **feature/***:  Feature branches off develop

```bash
# Working on new features
git checkout develop
git pull origin develop
git checkout -b feature/new-feature

# After testing, merge back to develop
git checkout develop
git merge feature/new-feature

# When ready for production
git checkout main
git merge develop
git push origin main  # This triggers Render deployment
```

## 🧹 Cleanup

```bash
# Stop containers
./dev.sh stop

# Remove containers and images
./dev.sh clean-all
```

## 📞 Support

If you encounter issues:
1. Check the logs: `./dev.sh logs`
2. Verify configuration: `cat .env`
3. Test database connection: `./dev.sh db-status`
4. Rebuild if needed: `./dev.sh build`

---

✅ **You're all set!** The development environment mirrors your Render production setup while keeping your code safe on the develop branch.
