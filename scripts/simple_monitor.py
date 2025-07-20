#!/usr/bin/env python3
"""
Simple Render Log Viewer - Direct log access without CLI interaction
Fetches logs by making API calls to your service and watching response patterns
"""

import os
import sys
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, Any

class SimpleLogMonitor:
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Load configuration from environment
        self.api_key = os.getenv('API_KEY')
        self.service_url = os.getenv('RENDER_SERVICE_URL', 'http://localhost:8000')
        self.service_name = os.getenv('RENDER_SERVICE_NAME', 'crypto-analyzer-gpt')
        
        if not self.api_key:
            print("❌ API_KEY not found in .env file")
            sys.exit(1)
        
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        self.last_request_time = None
    
    def test_api_endpoint(self, endpoint: str, method: str = 'GET', data: Optional[dict] = None) -> Optional[Dict[str, Any]]:
        """Test an API endpoint and log the response"""
        url = f"{self.service_url}{endpoint}"
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=self.headers, timeout=10)
            else:
                print(f"❌ Unsupported method: {method}")
                return None
            
            # Log the request
            status_icon = "✅" if 200 <= response.status_code < 300 else "❌"
            print(f"[{timestamp}] {status_icon} {method} {endpoint} - {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"[{timestamp}] 📊 Response: {json.dumps(data, indent=2)[:200]}...")
                    return data
                except:
                    print(f"[{timestamp}] 📊 Response: {response.text[:200]}...")
            else:
                print(f"[{timestamp}] ❌ Error: {response.text}")
            
            return response.json() if response.status_code == 200 else None
            
        except requests.exceptions.Timeout:
            print(f"[{timestamp}] ⏱️ Timeout on {method} {endpoint}")
        except requests.exceptions.ConnectionError:
            print(f"[{timestamp}] 🔌 Connection error on {method} {endpoint}")
        except Exception as e:
            print(f"[{timestamp}] ❌ Error on {method} {endpoint}: {e}")
        
        return None
    
    def monitor_with_health_checks(self, interval: int = 10):
        """Monitor service by periodically testing endpoints"""
        print(f"🔍 Starting service monitoring: {self.service_name}")
        print(f"🌐 Service URL: {self.service_url}")
        print(f"🔄 Check interval: {interval}s")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("💡 Press Ctrl+C to stop")
        print()
        
        check_count = 0
        
        try:
            while True:
                check_count += 1
                print(f"\n🔍 Health Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 40)
                
                # Test health endpoint
                self.test_api_endpoint('/health')
                
                # Every 3rd check, test more endpoints
                if check_count % 3 == 0:
                    print("\n🧪 Extended API Tests:")
                    # Test candles endpoint
                    self.test_api_endpoint('/candles?symbol=BTCUSDT&limit=1')
                    
                    # Test fear/greed
                    self.test_api_endpoint('/feargreed')
                
                # Every 5th check, send a test alert
                if check_count % 5 == 0:
                    print("\n🔔 Testing Alert System:")
                    test_alert = {
                        "symbol": "BTCUSDT",
                        "current_price": 45000.0,
                        "alert_type": "PRICE_CHANGE",
                        "details": f"Monitoring Test #{check_count} - System is responsive"
                    }
                    self.test_api_endpoint('/telegram/alert', 'POST', test_alert)
                
                print(f"\n⏳ Next check in {interval}s...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")
    
    def run_continuous_tests(self):
        """Run various API tests to generate log activity"""
        print("🚀 Running continuous API tests to monitor responses...")
        
        test_scenarios = [
            ('/health', 'GET', None),
            ('/candles?symbol=ETHUSDT&limit=1', 'GET', None),
            ('/candles?symbol=BTCUSDT&limit=1', 'GET', None),
            ('/feargreed', 'GET', None),
            ('/telegram/send', 'POST', {"message": "Test message from monitor"}),
        ]
        
        for i, (endpoint, method, data) in enumerate(test_scenarios):
            print(f"\n🧪 Test {i+1}/{len(test_scenarios)}: {method} {endpoint}")
            result = self.test_api_endpoint(endpoint, method, data)
            time.sleep(2)  # Brief pause between tests

def main():
    print("📊 Simple Render Log Monitor")
    print("=============================")
    
    monitor = SimpleLogMonitor()
    
    print("Choose monitoring mode:")
    print("1. Health Check Monitoring (periodic)")
    print("2. Run Test Suite (one-time)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            interval = input("Check interval in seconds (default 10): ").strip()
            interval = int(interval) if interval.isdigit() else 10
            monitor.monitor_with_health_checks(interval)
        elif choice == "2":
            monitor.run_continuous_tests()
        else:
            print("Invalid choice. Running health check monitoring...")
            monitor.monitor_with_health_checks()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
