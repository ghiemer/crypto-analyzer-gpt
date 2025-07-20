#!/usr/bin/env python3
"""
Telegram Alert Debug Script
Analyze why Telegram shows "no alerts" when alerts exist
"""

import asyncio
import aiohttp
import os
from pathlib import Path
from dotenv import load_dotenv

class TelegramAlertDebugger:
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        self.base_url = "https://crypto-analyzer-gpt.onrender.com"
        self.api_key = os.getenv('API_KEY')
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
    async def debug_alert_issue(self):
        """Debug why Telegram shows no alerts"""
        print("🔍 TELEGRAM ALERT DEBUG")
        print("=" * 50)
        
        # Check direct alert APIs
        await self._test_direct_api()
        
        # Check what Telegram function actually calls
        await self._test_telegram_alert_source()
        
        # Test simulating Telegram webhook
        await self._test_telegram_webhook_simulation()
        
    async def _test_direct_api(self):
        """Test direct alert APIs"""
        print("\n📋 STEP 1: DIRECT API TESTS")
        print("-" * 40)
        
        endpoints = [
            ("GPT Alerts List", "/gpt-alerts/list"),
            ("GPT Alerts Stats", "/gpt-alerts/stats"), 
            ("Live Alerts Status", "/live-alerts/status"),
            ("Simple Alerts Status", "/alerts")  # This might be what Telegram uses
        ]
        
        async with aiohttp.ClientSession() as session:
            for name, endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    async with session.get(url, headers=self.headers, timeout=10) as response:
                        status = response.status
                        data = await response.json()
                        
                        print(f"🌐 {name}: {status}")
                        if status == 200:
                            if endpoint == "/gpt-alerts/list":
                                print(f"   └─ Found {len(data)} alerts")
                                for i, alert in enumerate(data[:3]):  # Show first 3
                                    print(f"      {i+1}. {alert.get('symbol')} {alert.get('alert_type')} @ ${alert.get('target_price'):.2f}")
                            elif endpoint == "/gpt-alerts/stats":
                                print(f"   └─ Total: {data.get('total_active', 0)}")
                                print(f"   └─ By Symbol: {data.get('by_symbol', {})}")
                            elif endpoint == "/live-alerts/status":
                                print(f"   └─ Monitoring: {data.get('monitoring_active', False)}")
                                print(f"   └─ Total Alerts: {data.get('total_alerts', 0)}")
                            elif endpoint == "/alerts":
                                print(f"   └─ Response: {str(data)[:100]}...")
                        else:
                            print(f"   └─ ERROR: {status} - {data}")
                            
                except Exception as e:
                    print(f"❌ {name}: ERROR - {e}")
                    
    async def _test_telegram_alert_source(self):
        """Test what the Telegram alert function actually calls"""
        print("\n🤖 STEP 2: TELEGRAM SOURCE ANALYSIS")
        print("-" * 40)
        
        # Try to find what endpoint Telegram uses for alerts
        # Looking at the logs, it calls get_alert_system().get_active_alerts()
        # This might be different from /gpt-alerts/list
        
        print("📋 The logs show Telegram calls get_alert_system().get_active_alerts()")
        print("📋 This might be different from /gpt-alerts/list API endpoint")
        
        # Test the simple alerts endpoint that might be used
        try:
            async with aiohttp.ClientSession() as session:
                # Try internal alert system status
                url = f"{self.base_url}/stream/status"
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    data = await response.json()
                    print(f"🔄 Stream Status: {response.status}")
                    print(f"   └─ Active Streams: {data.get('active_streams', 0)}")
                    print(f"   └─ Symbols: {data.get('streaming_symbols', [])}")
                    
        except Exception as e:
            print(f"❌ Stream Status: ERROR - {e}")
            
    async def _test_telegram_webhook_simulation(self):
        """Simulate what happens when Telegram calls the webhook"""
        print("\n📱 STEP 3: TELEGRAM WEBHOOK SIMULATION")
        print("-" * 40)
        
        # Simulate a Telegram command that would show alerts
        webhook_data = {
            "update_id": 999999,
            "message": {
                "message_id": 999,
                "from": {"id": 7943683515, "first_name": "Test"},
                "chat": {"id": 7943683515, "type": "private"},
                "date": 1642781234,
                "text": "/alerts"
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/telegram/webhook"
                # Note: webhook endpoint doesn't need API key
                async with session.post(url, json=webhook_data, timeout=15) as response:
                    status = response.status
                    data = await response.json()
                    
                    print(f"📨 Webhook Simulation: {status}")
                    print(f"   └─ Response: {data}")
                    
        except Exception as e:
            print(f"❌ Webhook Simulation: ERROR - {e}")
        
        # Give some time for the async Telegram message to be sent
        await asyncio.sleep(2)
        print("⏳ Waiting for Telegram response...")
        
    async def _check_recent_logs(self):
        """Check what the recent logs show"""
        print("\n📊 RECENT FINDINGS FROM LOGS:")
        print("-" * 40)
        print("🔍 At 12:09:57 - Telegram showed '✅ Found 0 active alerts'")
        print("🔍 But our direct API test shows 2 active alerts exist")
        print("🔍 This suggests a disconnect between:")
        print("   • GPT Alert System (/gpt-alerts/list) - HAS alerts")
        print("   • Simple Alert System (get_active_alerts()) - NO alerts")
        
        print("\n💡 HYPOTHESIS:")
        print("   • The Telegram bot uses get_alert_system().get_active_alerts()")
        print("   • This might access a different alert storage than /gpt-alerts/list")
        print("   • GPT creates alerts via /gpt-alerts/price-above API")
        print("   • But Telegram reads from simple_alerts.py system")

async def main():
    debugger = TelegramAlertDebugger()
    await debugger.debug_alert_issue()

if __name__ == "__main__":
    asyncio.run(main())
