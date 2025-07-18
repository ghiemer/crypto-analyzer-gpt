# 📁 Documentation Structure

## 📂 Organization

### Core Documentation (Included in Production)
- `README.md` - Main project documentation
- `LICENSE` - MIT License
- `docs/customgpt/` - CustomGPT integration documentation
- `docs/knowledge/` - Trading knowledge base
- `docs/deployment/` - Deployment guides

### Development Documentation (Excluded from Production)
- `docs/development/` - Development setup and tools
- `docs/features/` - Feature development documentation  
- `docs/internal/` - Internal reports and analysis

## 🚫 Excluded from Production Deployment

The following directories and files are excluded via `.gitignore`:

```
docs/development/    # Development setup, scripts, API keys
docs/features/       # Feature development documentation
docs/internal/       # Internal reports and analysis
```

This ensures a clean production deployment with only essential documentation.

## 📊 Production-Ready Files

Only the following documentation is included in production:
- User-facing documentation
- CustomGPT integration guides
- Trading knowledge base
- Deployment instructions

All development artifacts, internal reports, and feature documentation are kept separate for development use only.
