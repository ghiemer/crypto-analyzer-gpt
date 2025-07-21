# Klassenbasierte Optimierung - Refactoring Plan

## Ziel
Die Anwendung für ein Agent Framework vorbereiten durch Umwandlung funktionaler Services in Klassen, ohne die bestehenden Endpunkte zu beeinträchtigen.

## Aktuelle Analyse

### Bereits klassenbasiert (✅)
- `UniversalStreamService` - Stream Management
- `SimpleAlertSystem` - Alert Management  
- `StreamSubscription` - Stream Abonnements
- `TelegramMenuSetup` - Telegram Menu Setup
- `DatabaseAlertVerifier` - Database Verification

### Zu refaktorieren (🔄)

#### 1. BitgetService (app/services/bitget.py)
**Aktuelle Funktionen:**
- `candles()` - Kerzendaten abrufen
- `orderbook()` - Orderbuch abrufen  
- `funding()` - Funding Rate abrufen
- `open_interest()` - Open Interest abrufen
- `_get()` - HTTP Client mit Caching
- `_normalize()` - Granularität normalisieren
- `_ms()` - Timestamp konvertieren

**Neue Klasse: `BitgetAPIClient`**
```python
class BitgetAPIClient:
    def __init__(self, cache_enabled: bool = True)
    async def get_candles(symbol: str, ...) -> pd.DataFrame
    async def get_orderbook(symbol: str, ...) -> Dict
    async def get_funding_rate(symbol: str) -> Dict
    async def get_open_interest(symbol: str) -> Dict
```

#### 2. IndicatorService (app/core/indicators.py)
**Aktuelle Funktionen:**
- `available()` - Verfügbare Indikatoren
- `compute()` - Indikatoren berechnen
- Registrierte Indikatoren (SMA, RSI, MACD, etc.)

**Neue Klasse: `TechnicalIndicatorService`**
```python
class TechnicalIndicatorService:
    def __init__(self)
    def get_available_indicators() -> List[str]
    def calculate_indicator(df: pd.DataFrame, indicator: str, **kwargs) -> pd.DataFrame
    def calculate_multiple(df: pd.DataFrame, indicators: List[str]) -> pd.DataFrame
    def register_custom_indicator(name: str, func: Callable)
```

#### 3. FearGreedService (app/services/feargreed.py)
**Neue Klasse: `FearGreedIndexService`**

#### 4. TelegramService (app/services/telegram_bot.py)  
**Neue Klasse: `TelegramBotService`**

#### 5. CacheService (app/core/cache.py)
**Neue Klasse: `CacheManager`**

#### 6. DatabaseService (app/core/database.py)
**Neue Klasse: `DatabaseManager`**

#### 7. TradingMonitorService (app/services/trading_monitor.py)
**Neue Klasse: `TradingMonitorService`**

## Implementation Strategie

### Phase 1: Core Services
1. `BitgetAPIClient` - API Client für externe Daten
2. `TechnicalIndicatorService` - Technische Analyse
3. `CacheManager` - Cache Management

### Phase 2: Business Services  
4. `FearGreedIndexService` - Sentiment Analysis
5. `TelegramBotService` - Telegram Integration
6. `DatabaseManager` - Database Operations

### Phase 3: Monitoring Services
7. `TradingMonitorService` - Trading Monitoring
8. Integration mit bestehendem `SimpleAlertSystem`

### Phase 4: Agent Framework Vorbereitung
9. `AgentToolRegistry` - Registry für Agent Tools
10. `AgentServiceManager` - Service Management für Agents
11. Wrapper-Funktionen für bestehende Endpunkte

## Backward Compatibility

Alle bestehenden Funktionen bleiben als Wrapper verfügbar:
```python
# Alte Funktion (bleibt verfügbar)
async def candles(symbol: str, **kwargs):
    client = BitgetAPIClient()
    return await client.get_candles(symbol, **kwargs)

# Neue Klasse für Agents
class BitgetAPIClient:
    async def get_candles(self, symbol: str, **kwargs):
        # Implementation
```

## Agent Framework Integration

Jede Service-Klasse implementiert:
```python
class BaseAgentTool:
    def get_tool_definition(self) -> Dict
    def get_available_methods(self) -> List[str]  
    async def execute_method(self, method: str, **kwargs) -> Any
```

## Nächste Schritte

1. ✅ Branch erstellt: `feature/class-based-optimization`
2. 🔄 Phase 1 Implementation starten
3. Tests für jede neue Klasse
4. Schrittweise Migration der bestehenden Endpunkte
5. Agent Framework Integration vorbereiten
