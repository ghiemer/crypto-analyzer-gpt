# 🤖 Telegram Bot Setup & CustomGPT Integration

## 📋 **Telegram Bot Einrichtung**

### 1. Bot erstellen
1. Gehe zu [@BotFather](https://t.me/BotFather) auf Telegram
2. Sende `/newbot`
3. Wähle einen Namen: `CryptoAnalyzer`
4. Wähle einen Username: `crypto_analyzer_signals_bot`
5. Kopiere den **Bot Token** (Format: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Chat ID ermitteln
1. Starte den Bot oder füge ihn zu einer Gruppe hinzu
2. Sende eine Nachricht an den Bot
3. Besuche: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Suche nach `"chat":{"id":` - das ist deine Chat ID

### 3. Umgebungsvariablen setzen
```bash
# In deiner .env Datei
TG_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TG_CHAT_ID=-1001234567890
```

---

## 🎯 **CustomGPT Nutzung**

### **Allgemeine Nachricht senden**
```
Sende eine Nachricht an Telegram: "📊 BTC Analyse abgeschlossen. Aktueller Preis: $45,000. Technische Indikatoren zeigen bullisches Momentum."
```

### **Trading Signal senden**
```
Sende ein Trading Signal für BTCUSDT:
- Signal: BUY
- Confidence: 85%
- Entry: $44,800
- Target 1: $46,500
- Target 2: $48,000
- Stop Loss: $42,000
- Analyse: "RSI zeigt überverkaufte Bedingungen, MACD bullischer Crossover, Preis durchbrach Widerstand"
```

### **Preis Alert senden**
```
Sende einen Preis Alert für BTCUSDT: Breakout bei $45,000 - "Preis durchbrach Widerstand bei $44,500"
```

---

## 🚀 **Automatisierte Signale**

### **Beispiel GPT Prompt für automatische Signale**
```
Analysiere BTCUSDT und wenn die Bedingungen erfüllt sind, sende ein Trading Signal:

Bedingungen für BUY Signal:
- RSI < 30 (überverkauft)
- MACD bullischer Crossover
- Preis über 20 SMA
- Volumen > Durchschnitt

Bedingungen für SELL Signal:
- RSI > 70 (überkauft)
- MACD bearischer Crossover
- Preis unter 20 SMA
- Negative Divergenz

Sende das Signal über Telegram wenn eine Bedingung erfüllt ist.
```

---

## 🔧 **Erweiterte Funktionen**

### **Multi-Symbol Überwachung**
```python
symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
for symbol in symbols:
    # Analysiere jedes Symbol
    # Sende Alerts bei wichtigen Levels
```

### **Zeitbasierte Alerts**
```python
# Täglich um 9:00 Markt-Update
# Stündlich bei kritischen Levels
# Sofort bei Breakouts
```

### **Risk Management Integration**
```python
# Automatische Stop Loss Updates
# Position Size Empfehlungen
# Portfolio Risk Alerts
```

---

## 📊 **Beispiel Nachrichten**

### **Trading Signal**
```
🚨 TRADING SIGNAL 🚨

Symbol: BTCUSDT
Signal: BUY
Confidence: 85%
Current Price: $45,000.50

📊 Trading Plan:
• Entry: $44,800.00
• Target 1: $46,500.00
• Target 2: $48,000.00
• Stop Loss: $42,000.00
• Risk/Reward: 1:2.5

📈 Analysis:
RSI zeigt überverkaufte Bedingungen, MACD bullischer Crossover, Preis durchbrach Widerstand

⏰ Time: 2025-01-15T14:30:00Z

⚠️ Risk Warning: Trading involves risk. Always manage your position size appropriately.
```

### **Price Alert**
```
🔔 PRICE ALERT 🔔

BTCUSDT: $45,000.50
Alert Type: BREAKOUT

Preis durchbrach Widerstand bei $44,500

📊 Check your analysis for next steps!
```

---

## 🔒 **Sicherheitshinweise**

1. **Bot Token geheim halten** - Niemals in Code oder GitHub
2. **Chat ID prüfen** - Nur autorisierte Chats
3. **Rate Limits beachten** - Telegram API Limits
4. **Fehlerbehandlung** - Robuste Error Handling
5. **Backup Plan** - Alternative Notification Methoden

---

## 🎯 **Best Practices**

### **Message Formatting**
- Emojis für bessere Lesbarkeit
- Klare Struktur mit Bullet Points
- Wichtige Informationen hervorheben
- Zeitstempel für Nachverfolgung

### **Signal Qualität**
- Nur hochwertige Signale senden
- Confidence Level immer angeben
- Klare Entry/Exit Punkte
- Risk/Reward Verhältnis zeigen

### **Timing**
- Nicht zu häufig senden (Spam vermeiden)
- Nur bei wichtigen Entwicklungen
- Marktzeiten berücksichtigen
- Zeitzone beachten

---

## 🔍 **Troubleshooting**

### **Häufige Probleme**
- Bot Token falsch → Neu von BotFather holen
- Chat ID falsch → getUpdates API verwenden
- Nachricht kommt nicht an → Bot in Chat aktivieren
- Rate Limit → Weniger Nachrichten senden

### **Testing**
```bash
# Test Telegram Connection
curl -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>&text=Test Message"
```
