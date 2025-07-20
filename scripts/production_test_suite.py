#!/usr/bin/env python3
"""
Production Test Suite
Comprehensive testing of the deployed crypto analyzer system
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

class ProductionTester:
    def __init__(self, base_url: str = "https://crypto-analyzer-gpt.onrender.com"):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        self.base_url = base_url
        self.api_key = os.getenv('API_KEY')
        self.test_results = []
        self.start_time = datetime.now()
        
        if not self.api_key:
            print("❌ API_KEY not found in .env file")
            sys.exit(1)
        
        # Set up headers with API key
        self.headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
    async def run_all_tests(self):
        """Run comprehensive production tests"""
        print("🚀 Starting Production Test Suite")
        print(f"📊 Base URL: {self.base_url}")
        print(f"⏰ Started at: {self.start_time.isoformat()}")
        print("="*60)
        
        # Test categories
        await self._test_health_endpoints()
        await self._test_api_endpoints()
        await self._test_alert_system()
        await self._test_data_services()
        await self._test_volume_fix()
        
        # Generate report
        self._generate_report()
        
    async def _test_health_endpoints(self):
        """Test health and status endpoints"""
        print("\n🏥 HEALTH & STATUS TESTS")
        print("-" * 40)
        
        tests = [
            ("Health Check", "/health", "GET"),
            ("API Status", "/", "GET"),
            ("Version Info", "/version", "GET"),
        ]
        
        for test_name, endpoint, method in tests:
            result = await self._api_test(test_name, endpoint, method)
            self.test_results.append(result)
            
    async def _test_api_endpoints(self):
        """Test main API endpoints"""
        print("\n🔌 API ENDPOINTS TESTS")
        print("-" * 40)
        
        tests = [
            ("Candles - ETHUSDT", "/candles?symbol=ETHUSDT&limit=10", "GET"),
            ("Candles - BTCUSDT", "/candles?symbol=BTCUSDT&limit=10", "GET"),
            ("News API", "/news?limit=5", "GET"),
            ("Fear & Greed", "/feargreed", "GET"),
            ("Orderbook - ETHUSDT", "/orderbook?symbol=ETHUSDT", "GET"),
        ]
        
        for test_name, endpoint, method in tests:
            result = await self._api_test(test_name, endpoint, method)
            self.test_results.append(result)
            
    async def _test_alert_system(self):
        """Test alert system functionality"""
        print("\n⚠️ ALERT SYSTEM TESTS")
        print("-" * 40)
        
        # Test alert endpoints
        tests = [
            ("List Alerts", "/gpt-alerts/list", "GET"),
            ("Alert Stats", "/gpt-alerts/stats", "GET"),
            ("Stream Stats", "/stream/status", "GET"),
        ]
        
        for test_name, endpoint, method in tests:
            result = await self._api_test(test_name, endpoint, method)
            self.test_results.append(result)
            
        # Test alert creation
        await self._test_alert_creation()
        
    async def _test_alert_creation(self):
        """Test creating and managing alerts"""
        test_alert = {
            "symbol": "ETHUSDT",
            "target_price": 4000.0,
            "description": "Test alert from production suite"
        }
        
        result = await self._api_test(
            "Create Test Alert",
            "/gpt-alerts/price-above",
            "POST",
            data=test_alert
        )
        self.test_results.append(result)
        
    async def _test_data_services(self):
        """Test data service endpoints"""
        print("\n📊 DATA SERVICES TESTS")
        print("-" * 40)
        
        tests = [
            ("RSI Indicator", "/rsi?symbol=ETHUSDT", "GET"),
            ("SMA Indicator", "/sma?symbol=ETHUSDT", "GET"),
            ("Perp Trading", "/perp?symbol=ETHUSDT", "GET"),
        ]
        
        for test_name, endpoint, method in tests:
            result = await self._api_test(test_name, endpoint, method)
            self.test_results.append(result)
            
    async def _test_volume_fix(self):
        """Test that volume column fix is working"""
        print("\n🔧 VOLUME FIX VERIFICATION")
        print("-" * 40)
        
        # Test multiple symbols to verify volume data
        symbols = ["ETHUSDT", "BTCUSDT", "SOLUSDT"]
        
        for symbol in symbols:
            result = await self._api_test(
                f"Volume Data - {symbol}",
                f"/candles?symbol={symbol}&limit=1",
                "GET",
                check_volume=True
            )
            self.test_results.append(result)
            
    async def _api_test(self, test_name: str, endpoint: str, method: str, 
                       data: Optional[Dict] = None, check_volume: bool = False) -> Dict:
        """Execute single API test"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                if method == "GET":
                    async with session.get(url, headers=self.headers, timeout=30) as response:
                        status = response.status
                        response_data = await response.json()
                elif method == "POST":
                    async with session.post(url, json=data, headers=self.headers, timeout=30) as response:
                        status = response.status
                        response_data = await response.json()
                        
                response_time = (time.time() - start_time) * 1000
                
                # Check volume data if requested
                volume_check = "N/A"
                if check_volume and isinstance(response_data, dict):
                    candles = response_data.get('candles', [])
                    if candles and len(candles) > 0:
                        first_candle = candles[0]
                        if "volume" in first_candle and first_candle["volume"] > 0:
                            volume_check = "✅ Volume OK"
                        else:
                            volume_check = "❌ Volume Missing"
                    else:
                        volume_check = "❌ No candles data"
                
                success = status == 200
                status_emoji = "✅" if success else "❌"
                
                print(f"{status_emoji} {test_name}: {status} ({response_time:.0f}ms)")
                if check_volume:
                    print(f"   └─ {volume_check}")
                
                return {
                    "test": test_name,
                    "success": success,
                    "status": status,
                    "response_time": response_time,
                    "volume_check": volume_check,
                    "timestamp": datetime.now().isoformat(),
                    "url": url
                }
                
        except Exception as e:
            error_time = (time.time() - start_time) * 1000
            print(f"❌ {test_name}: ERROR - {str(e)} ({error_time:.0f}ms)")
            
            return {
                "test": test_name,
                "success": False,
                "status": "ERROR",
                "error": str(e),
                "response_time": error_time,
                "volume_check": "ERROR",
                "timestamp": datetime.now().isoformat(),
                "url": url
            }
            
    def _generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📋 TEST RESULTS SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        avg_response_time = sum(r["response_time"] for r in self.test_results) / total_tests if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Average Response Time: {avg_response_time:.0f}ms")
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        print(f"⏰ Total Duration: {duration:.1f}s")
        
        # Failed tests details
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            print("-" * 40)
            for result in self.test_results:
                if not result["success"]:
                    print(f"• {result['test']}: {result.get('error', result['status'])}")
        
        # Volume check summary
        volume_tests = [r for r in self.test_results if r["volume_check"] != "N/A"]
        if volume_tests:
            print(f"\n🔧 VOLUME FIX VERIFICATION:")
            print("-" * 40)
            for result in volume_tests:
                print(f"• {result['test']}: {result['volume_check']}")
        
        # Save detailed report
        self._save_detailed_report()
        
    def _save_detailed_report(self):
        """Save detailed JSON report"""
        report_data = {
            "test_run": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "base_url": self.base_url,
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r["success"]),
                "success_rate": (sum(1 for r in self.test_results if r["success"]) / len(self.test_results)) * 100
            },
            "test_results": self.test_results
        }
        
        report_file = f"production_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved: {report_file}")

async def main():
    """Main test execution"""
    tester = ProductionTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
