# Agent Framework - Klassenbasierte Optimierung

## Übersicht

Diese Branch `feature/class-based-optimization` erweitert die Crypto Analyzer GPT Anwendung um ein klassenbasiertes Agent Framework. Alle bestehenden Funktionalitäten bleiben vollständig kompatibel, während neue strukturierte Services für Agent-Integration verfügbar werden.

## ✨ Neue Features

### 🏗️ Klassenbasierte Services

#### 1. BitgetAPIClient (`app/services/bitget_client.py`)
```python
# Neue klassenbasierte Implementierung
from app.services.bitget_client import get_bitget_client

client = get_bitget_client()
candles = await client.get_candles("BTCUSDT", "1h", 100)
orderbook = await client.get_orderbook("BTCUSDT", 10)

# Alte funktionale Implementierung (weiterhin verfügbar)
from app.services.bitget import candles as old_candles
candles = await old_candles("BTCUSDT", "1h", 100)
```

**Features:**
- Async Context Manager Support
- Verbesserte Fehlerbehandlung
- Strukturierte Parameter-Validierung
- Agent Framework Integration
- Vollständige Backward Compatibility

#### 2. TechnicalIndicatorService (`app/core/indicators_service.py`)
```python
from app.core.indicators_service import get_indicator_service

service = get_indicator_service()
available = service.get_available_indicators()
indicators = service.calculate_multiple(df, ["sma_50", "rsi_14", "macd"])
```

**Features:**
- 15+ technische Indikatoren
- Batch-Berechnungen
- Sichere Fehlerbehandlung
- Custom Indicator Registration
- Agent Tool Definition

#### 3. CacheManager (`app/core/cache_manager.py`)
```python
from app.core.cache_manager import get_cache_manager

cache = get_cache_manager()
await cache.initialize()
await cache.set("key", {"data": "value"}, ttl=300)
data = await cache.get("key")
```

**Features:**
- Redis Backend
- Automatische JSON Serialisierung
- TTL Management
- Bulk Operations
- Cache Statistics

### 🤖 Agent Framework Integration

#### AgentToolRegistry (`app/core/agent_framework.py`)
Zentrales Registry für alle Agent Tools mit automatischer Service-Discovery.

```python
from app.core.agent_framework import get_agent_tool_registry

registry = get_agent_tool_registry()
tools = registry.get_available_tools()
result = await registry.execute_tool_method("BitgetAPIClient", "get_candles", symbol="BTCUSDT")
```

### 🛡️ Backward Compatibility

Alle bestehenden Funktionen bleiben unverändert verfügbar:

```python
# Diese funktioniert weiterhin genau wie vorher
from app.services.bitget import candles
from app.core.indicators import available, compute

data = await candles("BTCUSDT", "1h", 100)
indicators = available()
```

## 🚀 Installation & Test

### 1. System starten
```bash
# Development Environment
./dev.sh start

# Production Environment  
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Agent Framework testen
```bash
# Test Script ausführen
python test_agent_framework.py

# Oder direkte API Tests
curl -X GET "http://localhost:8000/agent/tools" \
     -H "X-API-Key: your-api-key"
```

### 3. Neue Endpoints

| Endpoint | Beschreibung |
|----------|-------------|
| `GET /agent/tools` | Liste aller verfügbaren Agent Tools |
| `GET /agent/tools/{tool_name}` | Detaillierte Tool-Definition |
| `POST /agent/tools/{tool_name}/{method}` | Tool-Methode ausführen |
| `GET /agent/registry/stats` | Registry Statistiken |
| `POST /agent/test/bitget` | Bitget Client Test |
| `POST /agent/test/indicators` | Indicator Service Test |

## 🔧 Integration mit Agent Frameworks

### Schema Export
```bash
curl -X GET "http://localhost:8000/agent/registry/export" \
     -H "X-API-Key: your-api-key" \
     > agent_tools_schema.json
```

### Tool Execution Beispiel
```python
import httpx

async def execute_agent_tool():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/agent/tools/BitgetAPIClient/get_candles",
            headers={"X-API-Key": "your-api-key"},
            json={
                "symbol": "BTCUSDT",
                "granularity": "1h",
                "limit": 100
            }
        )
        return response.json()
```

## 📊 Verfügbare Agent Tools

### Market Data Tools
- **BitgetAPIClient**: Kryptowährungs-Marktdaten
  - `get_candles()` - OHLCV Daten
  - `get_orderbook()` - Orderbuch
  - `get_funding_rate()` - Funding Rates
  - `get_open_interest()` - Open Interest

### Technical Analysis Tools
- **TechnicalIndicatorService**: Technische Analyse
  - `calculate_indicator()` - Einzelner Indikator
  - `calculate_multiple()` - Mehrere Indikatoren
  - `get_available_indicators()` - Verfügbare Indikatoren

### System Tools
- **CacheManager**: Cache Management
  - `get()` / `set()` / `delete()` - Cache Operationen
  - `get_stats()` - Cache Statistiken

## 🎯 Nächste Schritte

1. **Weitere Services klassifizieren:**
   - FearGreedIndexService
   - TelegramBotService
   - DatabaseManager
   - TradingMonitorService

2. **Agent Framework erweitern:**
   - OpenAI Function Calling Integration
   - LangChain Tool Integration
   - Custom Agent Templates

3. **Performance optimieren:**
   - Connection Pooling
   - Request Batching
   - Cache Strategies

## 🐛 Debugging

### Logs prüfen
```bash
# Development Container
./dev.sh logs

# Direct Python
tail -f logs/app.log
```

### Test einzelne Komponenten
```python
# Test im Python REPL
from app.services.bitget_client import get_bitget_client
client = get_bitget_client()
# ... weitere Tests
```

## 📈 Monitoring

Die neuen Services bieten erweiterte Monitoring-Funktionen:

- Cache Hit/Miss Ratios
- API Request Statistics  
- Tool Execution Metrics
- Error Tracking

Zugriff über `/agent/registry/stats` oder direkt in den Service-Klassen.

## 🤝 Beitragen

1. Branch erstellen: `git checkout -b feature/new-agent-tool`
2. Service-Klasse implementieren (erbt von `BaseAgentTool`)
3. Tests hinzufügen
4. Tool im `AgentServiceManager` registrieren
5. Pull Request erstellen

---

**Status**: ✅ Ready for Production
**Kompatibilität**: 100% Backward Compatible  
**Nächste Version**: 2.1.0 mit vollständigem Agent Framework
