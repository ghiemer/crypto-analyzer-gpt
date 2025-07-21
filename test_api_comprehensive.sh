#!/bin/bash

# Crypto Analyzer GPT API Comprehensive Testing Script
# Replace YOUR_API_KEY with your actual API key

BASE_URL="https://crypto-analyzer-gpt.onrender.com"
API_KEY="${API_KEY:-YOUR_API_KEY}"  # Use environment variable or fallback

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Crypto Analyzer GPT API Testing Suite${NC}"
echo -e "${BLUE}=========================================${NC}"

# Function to test endpoint with colored output
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}Testing: $description${NC}"
    echo -e "${BLUE}$method $endpoint${NC}"
    
    if [ "$method" = "GET" ]; then
        if [ -n "$data" ]; then
            curl -s -w "\n${GREEN}Status: %{http_code} | Time: %{time_total}s${NC}\n" \
                -H "x-api-key: $API_KEY" \
                "$BASE_URL$endpoint?$data"
        else
            curl -s -w "\n${GREEN}Status: %{http_code} | Time: %{time_total}s${NC}\n" \
                -H "x-api-key: $API_KEY" \
                "$BASE_URL$endpoint"
        fi
    elif [ "$method" = "POST" ]; then
        if [[ "$data" == *"json"* ]]; then
            curl -s -w "\n${GREEN}Status: %{http_code} | Time: %{time_total}s${NC}\n" \
                -X POST \
                -H "Content-Type: application/json" \
                -H "x-api-key: $API_KEY" \
                -d "$data" \
                "$BASE_URL$endpoint"
        else
            curl -s -w "\n${GREEN}Status: %{http_code} | Time: %{time_total}s${NC}\n" \
                -X POST \
                -H "x-api-key: $API_KEY" \
                "$BASE_URL$endpoint?$data"
        fi
    elif [ "$method" = "DELETE" ]; then
        curl -s -w "\n${GREEN}Status: %{http_code} | Time: %{time_total}s${NC}\n" \
            -X DELETE \
            -H "x-api-key: $API_KEY" \
            "$BASE_URL$endpoint"
    fi
    
    echo -e "${BLUE}---${NC}"
}

echo -e "\n${GREEN}✅ 1. HEALTH CHECK${NC}"
test_endpoint "GET" "/health" "" "Health check endpoint"

echo -e "\n${GREEN}🕯️ 2. CANDLESTICK DATA & TECHNICAL ANALYSIS${NC}"
test_endpoint "GET" "/candles" "symbol=BTCUSDT&limit=50&indicators=rsi,sma,macd&granularity=1h" "Bitcoin 1h candles with indicators"
test_endpoint "GET" "/candles" "symbol=ETHUSDT&limit=100&indicators=all&granularity=4h" "Ethereum 4h candles with all indicators"

echo -e "\n${GREEN}😨 3. FEAR & GREED INDEX${NC}"
test_endpoint "GET" "/feargreed" "" "Current Fear & Greed Index"

echo -e "\n${GREEN}📰 4. CRYPTOCURRENCY NEWS${NC}"
test_endpoint "GET" "/news" "coin=bitcoin&limit=5" "Bitcoin news (5 articles)"
test_endpoint "GET" "/news" "coin=ethereum&limit=3" "Ethereum news (3 articles)"

echo -e "\n${GREEN}⚡ 5. PERPETUAL FUTURES DATA${NC}"
test_endpoint "GET" "/perp/funding" "symbol=BTCUSDT" "Bitcoin funding rates"
test_endpoint "GET" "/perp/oi" "symbol=BTCUSDT" "Bitcoin open interest"
test_endpoint "GET" "/perp/funding" "symbol=ETHUSDT" "Ethereum funding rates"

echo -e "\n${GREEN}📊 6. ORDERBOOK DATA${NC}"
test_endpoint "GET" "/orderbook" "symbol=BTCUSDT&limit=20" "Bitcoin orderbook (20 levels)"
test_endpoint "GET" "/orderbook" "symbol=ETHUSDT&limit=10" "Ethereum orderbook (10 levels)"

echo -e "\n${GREEN}🔔 7. GPT ALERTS SYSTEM${NC}"
test_endpoint "GET" "/gpt-alerts/list" "" "List all active alerts"

test_endpoint "POST" "/gpt-alerts/price-above" "symbol=BTCUSDT&target_price=50000&description=🚀 BTC above 50K!" "Create price above alert for BTC"
test_endpoint "POST" "/gpt-alerts/price-below" "symbol=ETHUSDT&target_price=3000&description=📉 ETH below 3K support" "Create price below alert for ETH"
test_endpoint "POST" "/gpt-alerts/breakout" "symbol=BTCUSDT&resistance_level=45000&description=💥 BTC breakout above 45K resistance" "Create breakout alert for BTC"

test_endpoint "GET" "/gpt-alerts/list" "" "List alerts after creation"

echo -e "\n${GREEN}📱 8. TELEGRAM INTEGRATION${NC}"
# Test Telegram message
telegram_message='{
  "message": "🤖 API Test: BTC Analysis Complete! Current price showing bullish momentum with RSI at 65 and MACD crossover confirmed.",
  "symbol": "BTCUSDT",
  "signal": "BUY",
  "confidence": 85,
  "analysis_type": "technical"
}'
test_endpoint "POST" "/telegram/send" "$telegram_message" "Send general Telegram message"

# Test Trading Signal
trading_signal='{
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
}'
test_endpoint "POST" "/telegram/signal" "$trading_signal" "Send trading signal to Telegram"

# Test Price Alert
price_alert='{
  "symbol": "BTCUSDT", 
  "current_price": 45250.50,
  "alert_type": "BREAKOUT",
  "details": "Price broke above 45K resistance with high volume",
  "change_percentage": 2.5
}'
test_endpoint "POST" "/telegram/alert" "$price_alert" "Send price alert to Telegram"

echo -e "\n${BLUE}📋 Test Summary Complete!${NC}"
echo -e "${YELLOW}Note: Replace YOUR_API_KEY with your actual API key${NC}"
echo -e "${YELLOW}Some endpoints may require valid Telegram bot configuration${NC}"
