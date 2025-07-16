# 🤝 Contributing to Crypto Analyzer GPT

Thank you for your interest in contributing to this project! Here you will find all the information you need.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Environment](#development-environment)
- [Contribution Process](#contribution-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Process](#pull-request-process)

## 🤝 Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## 🛠️ Development Environment

### Prerequisites

- Python 3.11+
- Redis Server
- PostgreSQL (optional, for local DB tests)
- Git

### Setup

1. **Fork and clone repository**:
   ```bash
   git clone https://github.com/ghiemer/crypto-analyzer-gpt.git
   cd crypto-analyzer-gpt
   ```

2. **Create virtual environment**:
   ```bash
   pyenv virtualenv 3.11.3 crypto-analyzer-gpt-dev
   pyenv activate crypto-analyzer-gpt-dev
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your development keys
   ```

5. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

## 🔄 Contribution Process

### 1. Create or find issue

- Check [existing issues](https://github.com/ghiemer/crypto-analyzer-gpt/issues)
- Create a new issue for bugs or features
- Discuss larger changes in the issue before implementation

### 2. Create branch

```bash
git checkout -b feature/amazing-feature
# or
git checkout -b bugfix/fix-important-bug
```

### 3. Implement changes

- Follow the [Coding Standards](#coding-standards)
- Write tests for new features
- Update documentation

### 4. Run tests

```bash
# All tests
python -m pytest

# With coverage
python -m pytest --cov=app --cov-report=html

# Linting
black . --check
isort . --check-only
flake8 .
```

### 5. Commit and push

```bash
git add .
git commit -m "feat: Add amazing feature"
git push origin feature/amazing-feature
```

### 6. Create pull request

- Use the PR template
- Describe your changes in detail
- Link relevant issues

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some additions:

```python
# Imports
from typing import Dict, List, Optional
import asyncio
import httpx

# Type hints are mandatory
async def get_candles(symbol: str, limit: int = 100) -> Dict[str, Any]:
    """
    Retrieves candlestick data.
    
    Args:
        symbol: Trading symbol (e.g. BTCUSDT)
        limit: Number of candles
        
    Returns:
        Dictionary with candlestick data
        
    Raises:
        HTTPException: On API errors
    """
    pass

# Prefer async/await
async def process_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()
```

### Tools

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### Configuration

```bash
# .pre-commit-config.yaml runs automatically
black .
isort .
flake8 .
mypy app/
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test data
└── conftest.py     # Pytest configuration
```

### Test Examples

```python
# Unit test
async def test_get_candles():
    result = await bitget.candles("BTCUSDT", "1h", 10)
    assert "rows" in result
    assert len(result["rows"]) <= 10

# Integration test
async def test_candles_endpoint(client):
    response = await client.get(
        "/candles?symbol=BTCUSDT&limit=10",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200
```

### Coverage Goals

- **Minimum**: 80% code coverage
- **Target**: 90% code coverage
- **Critical paths**: 100% coverage

## 📖 Documentation

### Docstrings

```python
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculates the Relative Strength Index (RSI).
    
    The RSI is a momentum oscillator that measures the speed
    and change of price movements.
    
    Args:
        data: DataFrame with OHLCV data
        period: Calculation period (default: 14)
        
    Returns:
        Series with RSI values (0-100)
        
    Example:
        >>> df = pd.DataFrame({"close": [100, 105, 103, 108, 110]})
        >>> rsi = calculate_rsi(df)
        >>> print(rsi.iloc[-1])
        75.5
    """
```

### README Updates

- Update README.md for API changes
- Add examples for new features
- Update configuration table

## 🐛 Issue Guidelines

### Bug Reports

```markdown
**Description**
Brief description of the problem.

**Steps to Reproduce**
1. Call endpoint: `GET /candles?symbol=BTCUSDT`
2. Parameters: `limit=1000`
3. Error occurs

**Expected Behavior**
API should return data.

**Actual Behavior**
API returns 500 error.

**Environment**
- Python: 3.11.3
- FastAPI: 0.115.12
- OS: macOS 14.0
```

### Feature Requests

```markdown
**Problem**
Description of the problem or need.

**Solution**
Proposed implementation.

**Alternatives**
Alternative approaches.

**Additional Context**
Screenshots, mockups, etc.
```

## 🔄 Pull Request Process

### PR Checklist

- [ ] Branch is up to date with `main`
- [ ] All tests pass
- [ ] Code coverage >= 80%
- [ ] Linting without errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Issue reference added

### PR Template

```markdown
## Changes
- Added new feature X
- Fixed bug Y
- Performance improvement Z

## Testing
- [ ] Unit tests added
- [ ] Integration tests updated
- [ ] Manually tested

## Documentation
- [ ] README updated
- [ ] API docs updated
- [ ] Changelog updated

## Closes Issues
Closes #123
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs
2. **Code Review**: At least 1 reviewer
3. **Testing**: Manual tests for larger changes
4. **Merge**: Squash-merge into main branch

## 🎯 Types of Contributions

### 🐛 Bug Fixes
- Minor fixes can be submitted directly as PR
- Larger bugs should be discussed as issue first

### ✨ Features
- Create issue for feature discussion
- Implement after feedback
- Add comprehensive tests

### 📖 Documentation
- Improvements are always welcome
- No issue required for minor corrections

### 🔧 Refactoring
- Discuss larger refactoring in issues
- Maintain existing API compatibility

## 🏆 Recognition

Contributions are recognized through:
- Listing in CONTRIBUTORS.md
- Mention in release notes
- GitHub badge in profile

## 📞 Help

For questions:
- Create a [Discussion](https://github.com/ghiemer/crypto-analyzer-gpt/discussions)
- Contact maintainers
- Check the [Documentation](https://your-app.onrender.com/docs)

**Thank you for your contribution!** 🚀
