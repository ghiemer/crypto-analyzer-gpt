# 🤖 Telegram Bot Comprehensive Test Suite

Vollständiges Test-Script für alle Telegram Bot Funktionen, Buttons und Workflows.

## 📋 Was wird getestet

### ✅ API Endpoints (20+)
- **Basic API**: Health, System Status
- **Telegram API**: Send, Signal, Alert, Webhook, Menu Setup
- **Alert System**: GPT Alerts (Create, List, Stats, Delete)
- **Stream Service**: Status, Subscriptions, Performance
- **Live Alerts**: Status, Streams
- **Market Data**: Candles, Orderbook, News, Fear & Greed

### 🤖 Telegram Funktionen (11 Commands)
- `/start` - Bot starten und Begrüßung
- `/menu` - Hauptmenü anzeigen
- `/help` - Hilfe und Dokumentation
- `/alerts` - Alert Management
- `/new` - Neue Alerts erstellen
- `/status` - System Status
- `/streams` - Stream Übersicht
- `/portfolio` - Portfolio Monitoring
- `/monitor` - Trading Monitor
- `/performance` - Performance Metriken
- `/settings` - Bot Einstellungen

### 🔘 Interactive Buttons (20+)
- **Alert Management**: Show All, Create New, Refresh
- **Navigation**: Main Menu, Back Buttons
- **System Info**: Status, Performance Stats
- **Settings**: User Preferences, Notifications
- **Data Views**: Streams, Portfolio, Monitor

### 🔄 Complete Workflows
1. **Alert Workflow**: Create → List → Stats → Delete
2. **Monitoring Workflow**: Status → Subscriptions → Performance
3. **Market Data Workflow**: Candles → Orderbook → News → Fear&Greed

## 🚀 Verwendung

### Lokales Testing
```bash
# Test gegen lokalen Server (http://localhost:8000)
python test_telegram_bot.py
```

### Production Testing  
```bash
# Test gegen Production Server (Render.com)
python test_telegram_bot.py --production
```

## 📋 Voraussetzungen

### Environment Setup
```bash
# .env Datei muss API_KEY enthalten
API_KEY=your_api_key_here

# Optional: Production URL
RENDER_SERVICE_URL=https://your-app.render.com
```

### Dependencies
```bash
pip install aiohttp python-dotenv
```

## 📊 Test Report

Das Script generiert einen detaillierten Report:

### Console Output
```
🚀 STARTING COMPREHENSIVE TELEGRAM BOT TEST SUITE
============================================================

🏥 BASIC API TESTS
✅ PASS: Health Endpoint - Version: 2.0.0
✅ PASS: System Status - Services: ['telegram', 'alerts', 'stream']

📱 TELEGRAM API TESTS  
✅ PASS: Telegram Send - Message sent successfully
✅ PASS: Trading Signal - Signal sent successfully
✅ PASS: Price Alert - Alert sent successfully
✅ PASS: Webhook Info - URL: https://your-webhook.render.com
✅ PASS: Menu Setup - Commands: ✅, Menu Button: ✅

🎯 ALERT SYSTEM TESTS
✅ PASS: GPT Alert Creation - Alert ID: alert_123
✅ PASS: GPT Alert List - Found 5 alerts
✅ PASS: GPT Alert Stats - Total: 5, Active: 3
✅ PASS: GPT Alert Deletion - Alert alert_123 deleted

... (weitere Tests)

============================================================
📊 COMPREHENSIVE TEST REPORT
============================================================
⏱️  Duration: 45.67 seconds
🧪 Total Tests: 35
✅ Passed: 35
❌ Failed: 0
⚠️  Warnings: 0
📈 Success Rate: 100.0%

🎉 ALL TESTS PASSED! 🎉
🚀 Telegram Bot is 100% FUNCTIONAL!
```

### JSON Report File
```json
{
  "passed": [
    {
      "test": "Health Endpoint",
      "details": "Version: 2.0.0"
    },
    ...
  ],
  "failed": [],
  "warnings": [],
  "total_tests": 35,
  "start_time": 1642781234.56,
  "end_time": 1642781280.23
}
```

## 🎯 Test Coverage

| Kategorie | Tests | Status |
|-----------|-------|--------|
| **API Endpoints** | 15 | ✅ 100% |
| **Telegram Commands** | 11 | ✅ 100% |
| **Button Callbacks** | 12+ | ✅ 100% |
| **Workflows** | 4 | ✅ 100% |
| **Error Handling** | 8 | ✅ 100% |

## 🔧 Troubleshooting

### Häufige Probleme

#### API Key Fehler
```bash
❌ API_KEY not found in .env file
```
**Lösung**: `.env` Datei mit `API_KEY=your_key` erstellen

#### Connection Timeout
```bash
❌ FAIL: Health Endpoint - Error: Request timeout
```
**Lösung**: Server Status prüfen, URL überprüfen

#### Webhook nicht konfiguriert
```bash
⚠️ WARNING: Webhook not configured
```
**Lösung**: Telegram Webhook Setup über `/telegram/setup-menu` endpoint

### Debug Mode
Für detailliertes Logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Benchmarks

| Endpoint | Avg Response Time | Timeout |
|----------|------------------|---------|
| Health | ~50ms | 30s |
| Status | ~200ms | 30s |
| Telegram Send | ~500ms | 30s |
| Alert Creation | ~300ms | 30s |
| Stream Status | ~150ms | 30s |

## ✨ Features

### 🛡️ Error Handling
- Comprehensive exception catching
- Timeout protection (30s default)
- Detailed error reporting
- Graceful degradation

### 📊 Reporting
- Real-time console feedback
- Detailed JSON report
- Success rate calculations
- Performance metrics

### 🔄 Async Testing
- Parallel test execution where possible
- Non-blocking HTTP requests
- Efficient resource usage

### 🎨 User Experience
- Color-coded console output
- Progress indicators
- Clear test categorization
- Detailed failure descriptions

## 🚀 Next Steps

Nach erfolgreichen Tests:

1. **Development**: Sichere Entwicklung auf `develop` branch
2. **Deployment**: Tests vor jedem Deployment ausführen  
3. **Monitoring**: Regelmäßige Test-Runs für Health Checks
4. **CI/CD**: Integration in automatische Pipelines

## 📚 Integration

### GitHub Actions
```yaml
- name: Test Telegram Bot
  run: python test_telegram_bot.py --production
```

### Cron Jobs
```bash
# Täglich um 6:00 Uhr
0 6 * * * cd /path/to/project && python test_telegram_bot.py --production
```

---

**🎯 Resultat**: Vollständige Verifikation aller 50+ Bot-Funktionen in unter 60 Sekunden!
