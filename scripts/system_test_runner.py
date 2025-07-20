#!/usr/bin/env python3
"""
Complete System Test & Monitor
Combines production testing with real-time log monitoring
"""

import asyncio
import subprocess
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# Import our test modules
from production_test_suite import ProductionTester
from fetch_logs import LogFetcher

class SystemTestRunner:
    def __init__(self, service_id: str = "srv-d1rm3dfgi27c73cioohg"):
        self.service_id = service_id
        self.tester = ProductionTester()
        self.log_fetcher = LogFetcher(service_id)
        self.test_start = None
        
    async def run_comprehensive_test(self, monitor_logs: bool = True):
        """Run comprehensive system test with optional log monitoring"""
        print("🚀 COMPREHENSIVE SYSTEM TEST & MONITORING")
        print("="*60)
        
        self.test_start = datetime.now()
        
        # Phase 1: Pre-test log analysis
        print("\n📋 PHASE 1: PRE-TEST LOG ANALYSIS")
        await self._pre_test_analysis()
        
        # Phase 2: Run production tests
        print("\n📋 PHASE 2: PRODUCTION TESTS")
        await self._run_production_tests()
        
        # Phase 3: Post-test log analysis
        print("\n📋 PHASE 3: POST-TEST LOG ANALYSIS")
        await self._post_test_analysis()
        
        # Phase 4: Volume fix verification
        print("\n📋 PHASE 4: VOLUME FIX VERIFICATION")
        await self._verify_volume_fix()
        
        # Phase 5: Generate comprehensive report
        print("\n📋 PHASE 5: COMPREHENSIVE REPORT")
        await self._generate_comprehensive_report()
        
    async def _pre_test_analysis(self):
        """Analyze system state before testing"""
        print("🔍 Fetching recent logs for baseline analysis...")
        
        logs = self.log_fetcher.fetch_logs(lines=50)
        if logs:
            analysis = self.log_fetcher.analyze_logs(logs)
            
            print(f"📊 System Health Baseline:")
            print(f"  • Total log lines: {len(logs)}")
            print(f"  • Errors in last 50 lines: {analysis['patterns_found']['errors']['count']}")
            print(f"  • Volume fix status: {analysis['volume_fix_status']}")
            
            # Check if system is responsive
            if analysis['patterns_found']['api_calls']['count'] > 0:
                print("✅ System appears active (API calls detected)")
            else:
                print("⚠️ Low system activity detected")
        else:
            print("❌ Could not fetch baseline logs")
    
    async def _run_production_tests(self):
        """Run the production test suite"""
        print("🧪 Executing production test suite...")
        await self.tester.run_all_tests()
    
    async def _post_test_analysis(self):
        """Analyze logs after testing"""
        print("🔍 Analyzing logs after test execution...")
        
        # Wait a moment for logs to propagate
        await asyncio.sleep(2)
        
        logs = self.log_fetcher.fetch_logs(lines=100)
        if logs:
            analysis = self.log_fetcher.analyze_logs(logs)
            
            # Look for test-related activity
            test_related_logs = [log for log in logs if any(keyword in log.lower() 
                                for keyword in ['test', 'alert', 'api', 'http'])]
            
            print(f"📈 Post-Test Analysis:")
            print(f"  • Test-related log entries: {len(test_related_logs)}")
            print(f"  • New errors since test start: {analysis['patterns_found']['errors']['count']}")
            print(f"  • API activity: {analysis['patterns_found']['api_calls']['count']} calls")
            
    async def _verify_volume_fix(self):
        """Specifically verify the volume fix is working"""
        print("🔧 Verifying volume column fix...")
        
        # Get recent logs and look for volume-related activity
        logs = self.log_fetcher.fetch_logs(lines=200)
        
        volume_errors = [log for log in logs if "Error getting enhanced price data" in log and "'volume'" in log]
        volume_successes = [log for log in logs if "checking" in log and "alerts" in log]
        
        print(f"Volume Fix Verification:")
        print(f"  • Volume errors found: {len(volume_errors)}")
        print(f"  • Successful price checks: {len(volume_successes)}")
        
        if volume_errors:
            print("❌ Volume fix may not be working properly")
            print("Recent volume errors:")
            for error in volume_errors[-3:]:  # Show last 3 errors
                print(f"    {error}")
        elif volume_successes:
            print("✅ Volume fix appears to be working")
            print("Recent successful price checks:")
            for success in volume_successes[-3:]:  # Show last 3 successes
                print(f"    {success}")
        else:
            print("⚠️ No volume-related activity detected")
    
    async def _generate_comprehensive_report(self):
        """Generate final comprehensive report"""
        test_duration = (datetime.now() - self.test_start).total_seconds()
        
        print("📄 COMPREHENSIVE SYSTEM REPORT")
        print("="*60)
        print(f"⏰ Test Duration: {test_duration:.1f} seconds")
        print(f"🏥 Service ID: {self.service_id}")
        print(f"🌐 Base URL: {self.tester.base_url}")
        
        # Get final system status
        logs = self.log_fetcher.fetch_logs(lines=20)
        if logs:
            print(f"\n📈 Final System Status:")
            print("Recent activity (last 20 log lines):")
            for log in logs[-5:]:  # Show last 5 logs
                print(f"  {log}")
        
        # Save comprehensive report
        report_data = {
            "test_session": {
                "start_time": self.test_start.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration_seconds": test_duration,
                "service_id": self.service_id
            },
            "test_results": self.tester.test_results,
            "final_logs": logs[-20:] if logs else []
        }
        
        filename = f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Comprehensive report saved: {filename}")

def main():
    """Main execution with CLI arguments"""
    parser = argparse.ArgumentParser(description="Run comprehensive system tests with log monitoring")
    parser.add_argument("--service-id", default="srv-d1rm3dfgi27c73cioohg", 
                       help="Render service ID")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick test without extensive log analysis")
    
    args = parser.parse_args()
    
    runner = SystemTestRunner(args.service_id)
    
    try:
        if args.quick:
            print("🏃 Running quick test mode...")
            asyncio.run(runner.tester.run_all_tests())
        else:
            print("🔬 Running comprehensive test with log monitoring...")
            asyncio.run(runner.run_comprehensive_test())
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()
