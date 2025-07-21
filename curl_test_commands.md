# Individual cURL Test Commands for Crypto Analyzer GPT API
# Replace YOUR_API_KEY with your actual API key

API_KEY="YOUR_API_KEY"
BASE_URL="https://crypto-analyzer-gpt.onrender.com"

## 1. HEALTH CHECK (No API key required)
curl "$BASE_URL/health"

## 2. TECHNICAL ANALYSIS & CANDLES
# Bitcoin 1h candles with RSI and SMA
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/candles?symbol=BTCUSDT&limit=50&indicators=rsi,sma&granularity=1h"

# Ethereum 4h candles with all indicators  
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/candles?symbol=ETHUSDT&limit=100&indicators=all&granularity=4h"

# Short timeframe analysis
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/candles?symbol=BTCUSDT&limit=200&indicators=macd,bb,stoch&granularity=15min"

## 3. MARKET SENTIMENT
# Fear & Greed Index
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/feargreed"

## 4. CRYPTOCURRENCY NEWS
# Bitcoin news
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/news?coin=bitcoin&limit=5"

# Ethereum news
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/news?coin=ethereum&limit=3"

## 5. FUTURES DATA
# Bitcoin funding rates
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/perp/funding?symbol=BTCUSDT"

# Bitcoin open interest
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/perp/oi?symbol=BTCUSDT"

# Ethereum funding rates
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/perp/funding?symbol=ETHUSDT"

## 6. ORDERBOOK ANALYSIS
# Bitcoin orderbook (20 levels)
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/orderbook?symbol=BTCUSDT&limit=20"

# Ethereum orderbook (10 levels)
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/orderbook?symbol=ETHUSDT&limit=10"

## 7. ALERTS MANAGEMENT
# List all active alerts
curl -H "x-api-key: $API_KEY" \
  "$BASE_URL/gpt-alerts/list"

# Create price above alert
curl -X POST -H "x-api-key: $API_KEY" \
  "$BASE_URL/gpt-alerts/price-above?symbol=BTCUSDT&target_price=50000&description=🚀%20BTC%20above%2050K!"

# Create price below alert  
curl -X POST -H "x-api-key: $API_KEY" \
  "$BASE_URL/gpt-alerts/price-below?symbol=ETHUSDT&target_price=3000&description=📉%20ETH%20below%203K%20support"

# Create breakout alert
curl -X POST -H "x-api-key: $API_KEY" \
  "$BASE_URL/gpt-alerts/breakout?symbol=BTCUSDT&resistance_level=45000&description=💥%20BTC%20breakout%20above%2045K"

# Delete alert (replace ALERT_ID with actual ID from list)
curl -X DELETE -H "x-api-key: $API_KEY" \
  "$BASE_URL/gpt-alerts/delete/ALERT_ID"

## 8. TELEGRAM INTEGRATION
# Send general message
curl -X POST -H "Content-Type: application/json" -H "x-api-key: $API_KEY" \
  -d '{
    "message": "🤖 API Test: BTC Analysis Complete! Current price showing bullish momentum with RSI at 65.",
    "symbol": "BTCUSDT",
    "signal": "BUY",
    "confidence": 85,
    "analysis_type": "technical"
  }' \
  "$BASE_URL/telegram/send"

# Send trading signal
curl -X POST -H "Content-Type: application/json" -H "x-api-key: $API_KEY" \
  -d '{
    "symbol": "BTCUSDT",
    "signal": "BUY", 
    "confidence": 88,
    "current_price": 45250.00,
    "entry_price": 45000.00,
    "target_1": 47000.00,
    "target_2": 49000.00,
    "stop_loss": 43000.00,
    "risk_reward": 2.5,
    "analysis": "RSI oversold recovery, MACD bullish crossover, volume spike confirmed",
    "timestamp": "2025-07-21T21:45:00Z"
  }' \
  "$BASE_URL/telegram/signal"

# Send price alert
curl -X POST -H "Content-Type: application/json" -H "x-api-key: $API_KEY" \
  -d '{
    "symbol": "BTCUSDT",
    "current_price": 45250.50,
    "alert_type": "BREAKOUT",
    "details": "Price broke above 45K resistance with high volume", 
    "change_percentage": 2.5
  }' \
  "$BASE_URL/telegram/alert"

## QUICK TEST COMMANDS (Copy and paste these)

# Quick health check
curl https://crypto-analyzer-gpt.onrender.com/health

# Quick BTC analysis (replace YOUR_API_KEY)
curl -H "x-api-key: YOUR_API_KEY" \
  "https://crypto-analyzer-gpt.onrender.com/candles?symbol=BTCUSDT&limit=20&indicators=rsi,sma,macd&granularity=1h" | jq .

# Quick Fear & Greed (replace YOUR_API_KEY)  
curl -H "x-api-key: YOUR_API_KEY" \
  "https://crypto-analyzer-gpt.onrender.com/feargreed" | jq .

# Quick alerts list (replace YOUR_API_KEY)
curl -H "x-api-key: YOUR_API_KEY" \
  "https://crypto-analyzer-gpt.onrender.com/gpt-alerts/list" | jq .
