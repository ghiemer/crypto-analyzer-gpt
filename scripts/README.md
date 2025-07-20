# 🛠️ Crypto Analyzer Scripts

Sammlung von Utility-Scripts für API-Tests und Log-Monitoring mit automatischer Konfiguration aus `.env`.

## 📋 Verfügbare Scripts

### 🧪 API-Testing

#### `test_api.py`
Vollständiger API-Test mit ETH-Kurs-Abfrage und Alert-Erstellung.

```bash
python scripts/test_api.py
```

**Features:**
- ✅ Lädt Konfiguration automatisch aus `.env`
- 📊 Holt aktuellen ETH-Kurs
- 🔔 Setzt Support/Resistance Alerts
- 📱 Sendet Bestätigungsnachricht an Telegram

#### `simple_monitor.py`
Interaktiver Service-Monitor mit verschiedenen Modi.

```bash
python scripts/simple_monitor.py
```

**Modi:**
1. **Health Check Monitoring**: Periodische API-Checks
2. **Test Suite**: Einmalige Durchführung aller Tests

### 📊 Log-Monitoring

#### `monitor_logs.sh`
Bash-Script für Render-Log-Streaming (benötigt Render CLI).

```bash
./scripts/monitor_logs.sh
```

**Features:**
- ✅ Automatische `.env` Konfiguration
- 🎨 Farbige Ausgabe
- 🔄 Live-Log-Streaming

#### `render_api_monitor.py`
Python-basierter Log-Monitor (experimentell).

```bash
python scripts/render_api_monitor.py
```

**Features:**
- 🚀 Direct API-Zugriff (falls verfügbar)
- 📊 Alternative CLI-Methoden
- 🔄 Polling-basiertes Monitoring

#### `simple_monitor.py`
Einfacher Service-Monitor durch API-Tests.

```bash
python scripts/simple_monitor.py
```

**Features:**
- 🔍 Service-Gesundheit überwachen
- 📈 API-Response-Zeiten messen
- 🔔 Test-Alerts senden

## 🔧 Konfiguration

### `.env` Variablen

```env
# API Configuration
API_KEY=your-api-key-here
RENDER_SERVICE_URL=https://your-service.onrender.com

# Render Service (für Log-Monitoring)
RENDER_SERVICE_ID=srv-your-service-id
RENDER_SERVICE_NAME=your-service-name

# Telegram (für Alerts)
TG_BOT_TOKEN=your-bot-token
TG_CHAT_ID=your-chat-id
```

### 🚀 Quick Setup

1. **Render CLI installieren** (für Log-Monitoring):
```bash
npm install -g @render/cli
render auth login
```

2. **Python Dependencies installieren**:
```bash
pip install requests python-dotenv
```

3. **Scripts ausführbar machen**:
```bash
chmod +x scripts/*.sh scripts/*.py
```

## 📖 Usage Examples

### Schneller API-Test
```bash
# Vollständiger ETH-Test mit Alerts
python scripts/test_api.py
```

### Live Service-Monitoring
```bash
# Gesundheitschecks alle 30 Sekunden
echo "1" | python scripts/simple_monitor.py
# Dann Intervall eingeben: 30
```

### Log-Streaming
```bash
# Live-Logs von Render
./scripts/monitor_logs.sh
```

### Troubleshooting

#### "API_KEY not found"
- Stelle sicher, dass `.env` im Projektroot existiert
- Überprüfe, dass `API_KEY=...` in `.env` gesetzt ist

#### "Render CLI not found"
```bash
npm install -g @render/cli
render auth login
```

#### "Connection error"
- Überprüfe `RENDER_SERVICE_URL` in `.env`
- Teste Service-Verfügbarkeit: `curl -I your-service-url/health`

## 🔒 Sicherheit

- ⚠️ Alle sensiblen Daten in `.env` speichern
- 🚫 `.env` niemals committen (ist in `.gitignore`)
- 🔐 API-Keys regelmäßig rotieren
- 🔍 Logs auf sensible Daten prüfen

## 🎯 Empfohlener Workflow

1. **Entwicklung**: `simple_monitor.py` für API-Tests
2. **Debugging**: `monitor_logs.sh` für Live-Logs
3. **Testing**: `test_api.py` für End-to-End-Tests
4. **Production**: Kombiniere alle Scripts für vollständige Überwachung
