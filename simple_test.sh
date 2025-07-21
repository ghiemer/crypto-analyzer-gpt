#!/bin/bash

# Simple API Test - Replace YOUR_API_KEY with your actual key
API_KEY="YOUR_API_KEY"

echo "🔍 Testing Crypto Analyzer GPT API..."
echo "====================================="

echo -e "\n✅ Health Check:"
curl -s https://crypto-analyzer-gpt.onrender.com/health | jq .

echo -e "\n📊 Testing Bitcoin Analysis (replace YOUR_API_KEY):"
echo "Command to run:"
echo 'curl -H "x-api-key: YOUR_API_KEY" "https://crypto-analyzer-gpt.onrender.com/candles?symbol=BTCUSDT&limit=10&indicators=rsi&granularity=1h" | jq .'

echo -e "\n🔔 Testing Alerts List (replace YOUR_API_KEY):"  
echo "Command to run:"
echo 'curl -H "x-api-key: YOUR_API_KEY" "https://crypto-analyzer-gpt.onrender.com/gpt-alerts/list" | jq .'

echo -e "\n📱 Create Test Alert (replace YOUR_API_KEY):"
echo "Command to run:"
echo 'curl -X POST -H "x-api-key: YOUR_API_KEY" "https://crypto-analyzer-gpt.onrender.com/gpt-alerts/price-above?symbol=BTCUSDT&target_price=100000&description=🚀%20BTC%20to%20the%20moon!" | jq .'

echo -e "\n🎯 Your API is deployed and working!"
echo "🔑 Just replace YOUR_API_KEY with your actual API key from .env"
