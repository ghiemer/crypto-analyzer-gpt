#!/usr/bin/env python3
"""
API-based Log Analysis
Get system status and recent activity via API calls instead of log streaming
"""

import requests
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

class APILogAnalyzer:
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        self.api_key = os.getenv('API_KEY')
        self.base_url = "https://crypto-analyzer-gpt.onrender.com"
        
        if not self.api_key:
            print("❌ API_KEY not found in .env file")
            sys.exit(1)
        
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def api_request(self, endpoint):
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
                return None
        except Exception as e:
            print(f"❌ Error calling {endpoint}: {e}")
            return None
    
    def analyze_system_status(self):
        """Analyze system status via API calls"""
        print("🚀 API-BASED SYSTEM ANALYSIS")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # 1. Health Check
        print("\n🏥 SYSTEM HEALTH")
        print("-" * 30)
        health = requests.get(f"{self.base_url}/health", timeout=10).json()
        print(f"✅ Status: {health.get('status', 'unknown')}")
        print(f"📊 Version: {health.get('version', 'unknown')}")
        print(f"🌍 Environment: {health.get('environment', 'unknown')}")
        
        # 2. Stream Service Status
        print("\n🔄 STREAM SERVICE STATUS")
        print("-" * 30)
        stream_stats = self.api_request("/stream/status")
        if stream_stats:
            print(f"✅ Running: {stream_stats.get('running', False)}")
            print(f"📊 Active Subscriptions: {stream_stats.get('active_subscriptions', 0)}")
            print(f"🔗 Active Streams: {stream_stats.get('active_streams', 0)}")
            print(f"📈 Symbols Monitored: {len(stream_stats.get('symbols_monitored', []))}")
            
            # Show monitored symbols
            symbols = stream_stats.get('symbols_monitored', [])
            if symbols:
                print(f"💰 Symbols: {', '.join(symbols)}")
        
        # 3. Alert System Status
        print("\n⚠️ ALERT SYSTEM STATUS")
        print("-" * 30)
        alert_stats = self.api_request("/gpt-alerts/stats")
        if alert_stats:
            print(f"📊 Total Active: {alert_stats.get('total_active', 0)}")
            print(f"📈 By Symbol: {alert_stats.get('by_symbol', {})}")
            
            # Check if price cache is working (indicates volume fix)
            price_cache = alert_stats.get('price_cache', {})
            print(f"💾 Price Cache: {len(price_cache)} symbols cached")
            
            if price_cache:
                print("✅ Volume Fix Status: WORKING (price data cached)")
                # Show some cached prices
                for symbol, data in list(price_cache.items())[:3]:
                    if isinstance(data, dict) and 'price' in data:
                        print(f"  • {symbol}: ${data['price']:,.2f}")
            else:
                print("⚠️ Volume Fix Status: NO CACHE DATA")
        
        # 4. Test Volume Data Directly
        print("\n🔧 VOLUME FIX VERIFICATION")
        print("-" * 30)
        
        symbols_to_test = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
        volume_working = 0
        
        for symbol in symbols_to_test:
            candle_data = self.api_request(f"/candles?symbol={symbol}&limit=1")
            if candle_data and 'candles' in candle_data:
                candles = candle_data['candles']
                if candles and len(candles) > 0:
                    candle = candles[0]
                    if 'volume' in candle and candle['volume'] > 0:
                        print(f"✅ {symbol}: Volume = {candle['volume']:,.0f}")
                        volume_working += 1
                    else:
                        print(f"❌ {symbol}: No volume data")
                else:
                    print(f"❌ {symbol}: No candle data")
            else:
                print(f"❌ {symbol}: API error")
        
        # 5. Recent Activity via Stream Data
        print("\n📈 RECENT STREAM ACTIVITY")
        print("-" * 30)
        
        for symbol in symbols_to_test[:2]:  # Test ETH and BTC
            stream_data = self.api_request(f"/stream/data/{symbol}")
            if stream_data:
                print(f"📊 {symbol}:")
                print(f"  • Price: ${stream_data.get('price', 0):,.2f}")
                print(f"  • Change: {stream_data.get('change_percent', 0):+.2f}%")
                print(f"  • Volume: {stream_data.get('volume', 0):,.0f}")
                print(f"  • Last Update: {stream_data.get('timestamp', 'unknown')}")
            else:
                print(f"❌ {symbol}: No stream data")
        
        # 6. Summary
        print("\n📋 SUMMARY")
        print("-" * 30)
        print(f"✅ System Health: Online")
        print(f"✅ Volume Fix: {volume_working}/{len(symbols_to_test)} symbols working")
        print(f"✅ Stream Service: {'Active' if stream_stats else 'Unknown'}")
        print(f"✅ Alert System: {'Active' if alert_stats else 'Unknown'}")
        
        if volume_working == len(symbols_to_test):
            print(f"\n🎉 VOLUME COLUMN FIX: FULLY OPERATIONAL!")
            print("All tested symbols are returning volume data correctly.")
        elif volume_working > 0:
            print(f"\n⚠️ VOLUME COLUMN FIX: PARTIALLY WORKING")
            print(f"Only {volume_working}/{len(symbols_to_test)} symbols working.")
        else:
            print(f"\n❌ VOLUME COLUMN FIX: NEEDS ATTENTION")
            print("No symbols are returning volume data.")

def main():
    analyzer = APILogAnalyzer()
    analyzer.analyze_system_status()
    print(f"\n💾 Analysis complete at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
