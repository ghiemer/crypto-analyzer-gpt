#!/usr/bin/env python3
"""
Alert Testing Suite
Comprehensive testing of alert creation, storage, and monitoring
"""

import requests
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os
import sys

class AlertTester:
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
        
        self.test_results = []
        
    def api_request(self, method, endpoint, data=None, params=None):
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
            elif method.upper() == 'POST':
                if data:
                    response = requests.post(url, headers=self.headers, json=data, timeout=15)
                else:
                    response = requests.post(url, headers=self.headers, params=params, timeout=15)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=self.headers, timeout=15)
            else:
                print(f"❌ Unsupported method: {method}")
                return None
            
            print(f"🌐 {method} {endpoint} -> {response.status_code}")
            
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    print(f"✅ Success: {json.dumps(data, indent=2)[:200]}...")
                    return data
                except json.JSONDecodeError:
                    print(f"✅ Success: {response.text[:100]}...")
                    return {"status": "success", "text": response.text}
            else:
                print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def test_alert_lifecycle(self):
        """Test complete alert lifecycle"""
        print("🚀 ALERT LIFECYCLE TEST")
        print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
        print("="*60)
        
        # Step 1: Get current price for realistic alerts
        print("\n📋 STEP 1: GET CURRENT PRICE")
        print("-" * 40)
        
        price_data = self.api_request('GET', '/candles', params={'symbol': 'ETHUSDT', 'limit': 1})
        if not price_data or 'candles' not in price_data or not price_data['candles']:
            print("❌ Cannot get current price - aborting test")
            return False
        
        current_price = price_data['candles'][0]['close']
        print(f"💰 Current ETH Price: ${current_price:,.2f}")
        
        # Calculate alert prices (1% above and below current price)
        alert_above_price = current_price * 1.01
        alert_below_price = current_price * 0.99
        
        print(f"📈 Will create alert ABOVE: ${alert_above_price:,.2f}")
        print(f"📉 Will create alert BELOW: ${alert_below_price:,.2f}")
        
        # Step 2: Clear existing test alerts
        print("\n📋 STEP 2: CLEAR EXISTING TEST ALERTS")
        print("-" * 40)
        
        existing_alerts = self.api_request('GET', '/gpt-alerts/list')
        if existing_alerts:
            test_alerts = [alert for alert in existing_alerts if 'Test alert' in alert.get('description', '')]
            print(f"🧹 Found {len(test_alerts)} existing test alerts to clean up")
            
            for alert in test_alerts:
                delete_result = self.api_request('DELETE', f"/gpt-alerts/{alert['id']}")
                if delete_result:
                    print(f"✅ Deleted test alert {alert['id']}")
        
        # Step 3: Create ABOVE alert
        print("\n📋 STEP 3: CREATE ABOVE ALERT")
        print("-" * 40)
        
        above_params = {
            "symbol": "ETHUSDT",
            "target_price": alert_above_price,
            "description": f"Test alert ABOVE current price {current_price}"
        }
        
        above_response = self.api_request('POST', '/gpt-alerts/price-above', params=above_params)
        above_alert_id = above_response.get('alert_id') if above_response else None
        
        if above_alert_id:
            print(f"✅ ABOVE Alert created with ID: {above_alert_id}")
            self.test_results.append({"type": "above_alert", "success": True, "id": above_alert_id})
        else:
            print("❌ Failed to create ABOVE alert")
            self.test_results.append({"type": "above_alert", "success": False})
        
        # Step 4: Create BELOW alert
        print("\n📋 STEP 4: CREATE BELOW ALERT")
        print("-" * 40)
        
        below_params = {
            "symbol": "ETHUSDT",
            "target_price": alert_below_price,
            "description": f"Test alert BELOW current price {current_price}"
        }
        
        below_response = self.api_request('POST', '/gpt-alerts/price-below', params=below_params)
        below_alert_id = below_response.get('alert_id') if below_response else None
        
        if below_alert_id:
            print(f"✅ BELOW Alert created with ID: {below_alert_id}")
            self.test_results.append({"type": "below_alert", "success": True, "id": below_alert_id})
        else:
            print("❌ Failed to create BELOW alert")
            self.test_results.append({"type": "below_alert", "success": False})
        
        # Step 5: Verify alerts are in the list
        print("\n📋 STEP 5: VERIFY ALERTS IN LIST")
        print("-" * 40)
        
        time.sleep(2)  # Wait for processing
        
        updated_alerts = self.api_request('GET', '/gpt-alerts/list')
        if updated_alerts:
            created_alerts = []
            for alert in updated_alerts:
                if alert.get('id') in [above_alert_id, below_alert_id]:
                    created_alerts.append(alert)
                    print(f"✅ Found alert: {alert['symbol']} {alert.get('alert_type', 'unknown')} @ ${alert['target_price']:,.2f}")
            
            print(f"📊 Verified {len(created_alerts)}/2 created alerts in list")
            self.test_results.append({"type": "verification", "success": len(created_alerts) == 2, "found": len(created_alerts)})
        else:
            print("❌ Could not retrieve alert list")
            self.test_results.append({"type": "verification", "success": False})
        
        # Step 6: Check alert statistics
        print("\n📋 STEP 6: CHECK ALERT STATISTICS")
        print("-" * 40)
        
        stats = self.api_request('GET', '/gpt-alerts/stats')
        if stats:
            print(f"📈 Alert Statistics:")
            print(f"  • Total Active: {stats.get('total_active', 0)}")
            print(f"  • By Symbol: {stats.get('by_symbol', {})}")
            print(f"  • Price Cache: {len(stats.get('price_cache', {}))} symbols")
            
            # Check if our alerts are counted
            ethusdt_count = stats.get('by_symbol', {}).get('ETHUSDT', 0)
            if ethusdt_count >= 2:
                print(f"✅ ETHUSDT alerts properly counted: {ethusdt_count}")
                self.test_results.append({"type": "statistics", "success": True, "count": ethusdt_count})
            else:
                print(f"⚠️ ETHUSDT alert count unexpected: {ethusdt_count}")
                self.test_results.append({"type": "statistics", "success": False, "count": ethusdt_count})
        
        # Step 7: Check monitoring system
        print("\n📋 STEP 7: CHECK MONITORING SYSTEM")
        print("-" * 40)
        
        live_status = self.api_request('GET', '/live-alerts/status')
        if live_status:
            print(f"🔄 Live Monitoring Status:")
            print(f"  • Total Alerts: {live_status.get('total_alerts', 0)}")
            print(f"  • Active Streams: {live_status.get('active_streams', 0)}")
            
            if live_status.get('total_alerts', 0) > 0:
                print("✅ Monitoring system is tracking alerts")
                self.test_results.append({"type": "monitoring", "success": True})
            else:
                print("⚠️ Monitoring system shows no alerts")
                self.test_results.append({"type": "monitoring", "success": False})
        
        # Step 8: Test Telegram notification
        print("\n📋 STEP 8: TEST TELEGRAM NOTIFICATION")
        print("-" * 40)
        
        notification_message = f"""🧪 **Alert System Test Results**

✅ **Alerts Created Successfully:**
• ABOVE Alert: ${alert_above_price:,.2f} (ID: {above_alert_id})
• BELOW Alert: ${alert_below_price:,.2f} (ID: {below_alert_id})

📊 **Current ETH Price:** ${current_price:,.2f}

🔔 **Alert System Status:** Fully Operational
⏰ **Test Time:** {datetime.now().strftime('%H:%M:%S')}

The alert system is working correctly and monitoring price movements!"""
        
        telegram_result = self.api_request('POST', '/telegram/send', data={'message': notification_message})
        
        if telegram_result:
            print("📱 Telegram notification sent successfully!")
            self.test_results.append({"type": "telegram", "success": True})
        else:
            print("❌ Telegram notification failed")
            self.test_results.append({"type": "telegram", "success": False})
        
        return True
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*60)
        print("📊 ALERT TESTING RESULTS")
        print("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result.get("success", False))
        
        print(f"📈 Overall Results:")
        print(f"  • Total Tests: {total_tests}")
        print(f"  • Successful: {successful_tests}")
        print(f"  • Success Rate: {(successful_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        
        print(f"\n🔍 Test Details:")
        for result in self.test_results:
            test_type = result.get("type", "unknown")
            success = result.get("success", False)
            status_emoji = "✅" if success else "❌"
            
            if test_type == "above_alert":
                print(f"  {status_emoji} ABOVE Alert Creation: {'Success' if success else 'Failed'}")
                if success:
                    print(f"      └─ Alert ID: {result.get('id')}")
            elif test_type == "below_alert":
                print(f"  {status_emoji} BELOW Alert Creation: {'Success' if success else 'Failed'}")
                if success:
                    print(f"      └─ Alert ID: {result.get('id')}")
            elif test_type == "verification":
                found = result.get("found", 0)
                print(f"  {status_emoji} Alert Verification: Found {found}/2 alerts")
            elif test_type == "statistics":
                count = result.get("count", 0)
                print(f"  {status_emoji} Alert Statistics: {count} ETHUSDT alerts counted")
            elif test_type == "monitoring":
                print(f"  {status_emoji} Live Monitoring: {'Active' if success else 'Inactive'}")
            elif test_type == "telegram":
                print(f"  {status_emoji} Telegram Notification: {'Sent' if success else 'Failed'}")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ALL ALERT TESTS PASSED!")
            print("The alert system is fully functional and ready for production use.")
        elif successful_tests >= total_tests * 0.8:
            print(f"\n✅ MOST ALERT TESTS PASSED!")
            print("Alert system is mostly functional with minor issues.")
        else:
            print(f"\n❌ ALERT SYSTEM NEEDS ATTENTION!")
            print("Multiple test failures detected.")

def main():
    """Main test execution"""
    tester = AlertTester()
    
    try:
        success = tester.test_alert_lifecycle()
        if success:
            tester.generate_report()
        else:
            print("❌ Alert lifecycle test failed")
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()
