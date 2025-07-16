# 🚀 Crypto Analyzer GPT

> Professional cryptocurrency analysis API with real-time market data, technical indicators, and AI-powered insights.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-2.0.0-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Deploy](https://img.shields.io/badge/Deploy-Render-purple.svg)](https://render.com)

## 📋 Overview

**Crypto Analyzer GPT** is a professional-grade REST API designed for cryptocurrency analysis and AI integration. Built with FastAPI, it provides comprehensive market data, technical analysis, sentiment tracking, and news aggregation for informed trading decisions.

### 🎯 Key Features

- **📊 Real-time Market Data** - Live OHLCV data and orderbook information
- **📈 Technical Analysis** - 15+ technical indicators (RSI, MACD, SMA, EMA, Bollinger Bands)
- **📰 News Aggregation** - Multi-source crypto news with sentiment analysis
- **😱 Market Sentiment** - Fear & Greed Index and social sentiment tracking
- **🔮 Futures Data** - Funding rates and open interest from perpetual contracts
- **🤖 AI Integration** - Optimized for CustomGPT and AI trading systems
- **🛡️ Security** - API key authentication and rate limiting
- **⚡ Performance** - Redis caching and optimized response times
- **💹 Futures Data** - Funding rates and Open Interest
- **🚀 AI-optimized** - Specifically developed for CustomGPT and other AI systems

### 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: PostgreSQL, Redis (Caching)
- **APIs**: Bitget, NewsAPI, CryptoPanic, Fear & Greed Index
- **Deployment**: Docker, Render Cloud
- **Monitoring**: Structured Logging, Health Checks

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Redis Server
- PostgreSQL (for Production)

### 1. Clone Repository

```bash
git clone https://github.com/ghiemer/crypto-analyzer-gpt.git
cd crypto-analyzer-gpt
```

### 2. Create Virtual Environment

```bash
# With pyenv (recommended)
pyenv virtualenv 3.11.3 crypto-analyzer-gpt
pyenv activate crypto-analyzer-gpt

# Or with venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Create .env file
cp config/.env.example .env

# Configure at least these values:
# API_KEY=your-secure-api-key-here
# REDIS_URL=redis://localhost:6379/0
```

### 5. Start Application

```bash
# Development Server
uvicorn app.main:app --reload --port 8000

# Production Server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 6. Test API

```bash
# Health Check
curl -H "X-API-Key: your-api-key" http://localhost:8000/health

# Bitcoin data with indicators
curl -H "X-API-Key: your-api-key" "http://localhost:8000/candles?symbol=BTCUSDT&indicators=rsi14,sma50"
```

## 📚 Documentation

- **[CustomGPT Integration](docs/customgpt/)** - Setup and configuration for CustomGPT
- **[Deployment Guide](docs/deployment/)** - Production deployment instructions
- **[API Documentation](docs/customgpt/OPENAI_SCHEMA.json)** - OpenAPI 3.1 schema
- **[Changelog](docs/CHANGELOG.md)** - Version history and updates
- **[Contributing](docs/CONTRIBUTING.md)** - Development guidelines

## 🔧 Configuration

All configuration files are located in the `config/` directory:
- `config/.env.example` - Environment variables template
- `config/pyproject.toml` - Python project configuration
- `config/pyrightconfig.json` - Type checking configuration

## 🚀 Production Deployment

### 1. Render.com Deployment

```bash
# 1. Create Render account
# 2. Create PostgreSQL service
# 3. Create Redis service
# 4. Create Web service with this repository
```

### 2. Environment Setup

```bash
# Render Dashboard -> Environment Variables
API_KEY=your-production-api-key
REDIS_URL=redis://your-redis-instance
DATABASE_URL=postgresql://user:pass@host:port/db
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 3. Health Check

```bash
# Check after deployment
curl -H "X-API-Key: your-key" https://your-app.onrender.com/health
```

### 4. Monitoring

- **Logs**: Render Dashboard -> Logs
- **Metrics**: `/metrics` Endpoint
- **Alerts**: Telegram Bot Integration

## 🔐 Security

### API Authentication

```bash
# All requests require API-Key header
curl -H "X-API-Key: your-secret-key" https://api.example.com/endpoint
```

### Rate Limiting

- **Default**: 100 requests per minute
- **Configurable** via Environment Variables
- **IP-based** with automatic recovery

### Input Validation

- All parameters are validated
- SQL injection protection
- XSS protection through security headers

## 🔌 CustomGPT Integration

### Setup

1. **Generate API-Key**:
   ```bash
   openssl rand -hex 32
   ```

2. **Configure CustomGPT**:
   - Base URL: `https://your-app.onrender.com`
   - Authentication: Custom Header
   - Header: `X-API-Key: your-key`

3. **Example Prompts**:
   ```
   "Analyze Bitcoin with RSI and SMA"
   "Show me Ethereum news"
   "What's the market sentiment today?"
   ```

### Optimized Endpoints

```python
# Simplified queries for AI
GET /candles?symbol=BTCUSDT&indicators=all
GET /news?coin=bitcoin
GET /misc/feargreed
```

## 📊 Monitoring & Logging

### Logs

```bash
# Local logs
tail -f logs/app.log

# Render logs
render logs --service your-service-name
```

### Metrics

```bash
# Prometheus metrics
curl https://your-app.onrender.com/metrics

# Custom metrics
- Request Count
- Response Time
- Cache Hit Rate
- Error Rate
```

## 🧪 Testing

### Unit Tests

```bash
# Run tests
python -m pytest tests/

# With coverage
python -m pytest --cov=app tests/
```

### API Tests

```bash
# Postman Collection
./tests/postman/crypto-analyzer.postman_collection.json

# Manual testing
curl -H "X-API-Key: test-key" http://localhost:8000/health
```

## 🤝 Contributing

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Create Pull Request**

### Development Guidelines

- **Code Style**: Black, isort, flake8
- **Documentation**: Docstrings for all functions
- **Tests**: Minimum 80% coverage
- **Type Hints**: Complete typing

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Bitget** - Crypto exchange API
- **Render** - Cloud hosting platform
- **Redis** - In-memory caching
- **PostgreSQL** - Relational database

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/ghiemer/crypto-analyzer-gpt/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ghiemer/crypto-analyzer-gpt/discussions)
- **Email**: your-email@example.com

---

⭐ **Like this project? Give us a star on GitHub!** ⭐

**Developed with ❤️ for the crypto community**
