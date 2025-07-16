# 📁 Project Structure

```
crypto-analyzer-gpt/
├── 📁 app/                     # Main application code
│   ├── 📁 core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── alerts.py           # Alert management
│   │   ├── cache.py            # Redis caching
│   │   ├── database.py         # Database configuration
│   │   ├── errors.py           # Error handling
│   │   ├── indicators.py       # Technical indicators
│   │   └── settings.py         # Application settings
│   ├── 📁 models/              # Data models
│   │   ├── __init__.py
│   │   └── candle.py           # OHLCV data models
│   ├── 📁 routes/              # API endpoints
│   │   ├── __init__.py
│   │   ├── alerts.py           # Alert endpoints
│   │   ├── candles.py          # Market data endpoints
│   │   ├── misc.py             # Utility endpoints
│   │   ├── news.py             # News endpoints
│   │   ├── orderbook.py        # Orderbook endpoints
│   │   ├── perp.py             # Perpetual futures endpoints
│   │   └── telegram.py         # Telegram bot endpoints
│   ├── 📁 services/            # External services
│   │   ├── __init__.py
│   │   ├── bitget.py           # Bitget API integration
│   │   ├── feargreed.py        # Fear & Greed Index
│   │   └── telegram_bot.py     # Telegram notifications
│   └── main.py                 # FastAPI application entry point
├── 📁 docs/                    # Documentation
│   ├── 📁 customgpt/           # CustomGPT integration
│   │   ├── CUSTOMGPT_DESCRIPTION.md
│   │   ├── CUSTOMGPT_INSTRUCTIONS.md
│   │   ├── CUSTOMGPT_SHORT_INSTRUCTIONS.md
│   │   └── OPENAI_SCHEMA.json
│   ├── 📁 deployment/          # Deployment guides
│   │   ├── DEPLOYMENT.md
│   │   ├── DOCKER.md
│   │   └── RENDER.md
│   ├── 📁 knowledge/           # Trading knowledge base
│   │   ├── README.md
│   │   ├── technical_analysis_strategies.md
│   │   ├── risk_management_framework.md
│   │   ├── market_sentiment_analysis.md
│   │   ├── trading_psychology.md
│   │   └── fundamental_analysis.md
│   ├── CHANGELOG.md            # Version history
│   ├── CONTRIBUTING.md         # Contribution guidelines
│   └── TELEGRAM_INTEGRATION.md # Telegram bot setup guide
├── 📁 tests/                   # Test suite
│   ├── __init__.py
│   ├── test_api.py             # API endpoint tests
│   ├── test_imports.py         # Import validation
│   ├── test_telegram.py        # Telegram integration tests
│   └── stubs.py                # Test utilities
├── 📁 .vscode/                 # VS Code configuration
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── .python-version             # Python version specification
├── Dockerfile                  # Docker container configuration
├── LICENSE                     # MIT license
├── README.md                   # Project documentation
├── pyproject.toml              # Python project configuration
├── pyrightconfig.json          # Type checking configuration
├── render.yaml                 # Render deployment configuration
└── requirements.txt            # Python dependencies
```

## 📋 Key Directories

### `/app/` - Main Application
- **`core/`**: Core functionality including settings, caching, and utilities
- **`models/`**: Pydantic models for data validation
- **`routes/`**: FastAPI route handlers organized by functionality
- **`services/`**: External API integrations and third-party services
- **`main.py`**: Application entry point with FastAPI configuration

### `/docs/` - Documentation
- **`customgpt/`**: CustomGPT integration files and schemas
- **`deployment/`**: Deployment guides for various platforms
- **`knowledge/`**: Trading strategy knowledge base for AI enhancement

### `/tests/` - Test Suite
- Comprehensive API endpoint testing
- Import validation and type checking
- Test utilities and mock data

## 🔧 Configuration Files

- **`.env.example`**: Template for environment variables
- **`pyproject.toml`**: Python project configuration with tool settings
- **`pyrightconfig.json`**: Type checking configuration for development
- **`render.yaml`**: Render.com deployment configuration
- **`requirements.txt`**: Python dependencies for production

## 🚀 Key Features by Directory

### Core Services (`/app/services/`)
- **Bitget API**: Real-time market data and futures information
- **Fear & Greed Index**: Market sentiment analysis
- **Telegram Bot**: Alert notifications and monitoring

### API Endpoints (`/app/routes/`)
- **Candles**: OHLCV data with technical indicators
- **Orderbook**: Market depth and liquidity information
- **News**: Aggregated crypto news with sentiment analysis
- **Perpetual Futures**: Funding rates and open interest
- **Alerts**: Custom alert management
- **Telegram**: Signal delivery and notification system

### Knowledge Base (`/docs/knowledge/`)
- **Technical Analysis**: Professional trading strategies
- **Risk Management**: Position sizing and risk control
- **Market Sentiment**: Sentiment analysis techniques
- **Trading Psychology**: Behavioral finance principles
- **Fundamental Analysis**: Crypto valuation frameworks

This structure provides a clean, maintainable, and scalable foundation for cryptocurrency analysis and AI integration.
