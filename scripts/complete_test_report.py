#!/usr/bin/env python3
"""
Complete System Test Report
Runs all tests and generates comprehensive report
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

def run_all_tests():
    """Run all test suites and compile results"""
    
    print("🚀 COMPLETE SYSTEM TEST SUITE")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {}
    }
    
    # Test 1: Production API Tests
    print("\n📋 TEST 1: PRODUCTION API ENDPOINTS")
    print("-" * 40)
    try:
        result = subprocess.run([
            "python3", "scripts/production_test_suite.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Production tests completed")
            # Extract success rate from output
            lines = result.stdout.split('\n')
            for line in lines:
                if "Success Rate:" in line:
                    success_rate = line.split("Success Rate:")[1].strip()
                    test_results["tests"]["production_api"] = {
                        "status": "completed",
                        "success_rate": success_rate
                    }
                    print(f"📊 Success Rate: {success_rate}")
                    break
        else:
            print("❌ Production tests failed")
            test_results["tests"]["production_api"] = {"status": "failed"}
            
    except Exception as e:
        print(f"❌ Error running production tests: {e}")
        test_results["tests"]["production_api"] = {"status": "error", "error": str(e)}
    
    # Test 2: API-based System Analysis
    print("\n📋 TEST 2: SYSTEM STATUS ANALYSIS")
    print("-" * 40)
    try:
        result = subprocess.run([
            "python3", "scripts/api_log_analyzer.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ System analysis completed")
            # Check for volume fix status
            if "VOLUME COLUMN FIX: FULLY OPERATIONAL!" in result.stdout:
                volume_status = "FULLY_OPERATIONAL"
                print("✅ Volume fix: FULLY OPERATIONAL")
            elif "PARTIALLY WORKING" in result.stdout:
                volume_status = "PARTIALLY_WORKING"
                print("⚠️ Volume fix: PARTIALLY WORKING")
            else:
                volume_status = "NEEDS_ATTENTION"
                print("❌ Volume fix: NEEDS ATTENTION")
            
            test_results["tests"]["system_analysis"] = {
                "status": "completed",
                "volume_fix_status": volume_status
            }
        else:
            print("❌ System analysis failed")
            test_results["tests"]["system_analysis"] = {"status": "failed"}
            
    except Exception as e:
        print(f"❌ Error running system analysis: {e}")
        test_results["tests"]["system_analysis"] = {"status": "error", "error": str(e)}
    
    # Test 3: Direct Health Check
    print("\n📋 TEST 3: DIRECT HEALTH CHECK")
    print("-" * 40)
    try:
        result = subprocess.run([
            "curl", "-s", "https://crypto-analyzer-gpt.onrender.com/health"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            health_data = json.loads(result.stdout)
            print(f"✅ Health check successful")
            print(f"📊 Status: {health_data.get('status')}")
            print(f"🔢 Version: {health_data.get('version')}")
            
            test_results["tests"]["health_check"] = {
                "status": "completed",
                "api_status": health_data.get('status'),
                "version": health_data.get('version')
            }
        else:
            print("❌ Health check failed")
            test_results["tests"]["health_check"] = {"status": "failed"}
            
    except Exception as e:
        print(f"❌ Error running health check: {e}")
        test_results["tests"]["health_check"] = {"status": "error", "error": str(e)}
    
    # Generate Final Report
    print("\n" + "="*60)
    print("📊 FINAL TEST REPORT")
    print("="*60)
    
    total_tests = len(test_results["tests"])
    successful_tests = sum(1 for test in test_results["tests"].values() if test.get("status") == "completed")
    
    print(f"📈 Overall Results:")
    print(f"  • Total Tests: {total_tests}")
    print(f"  • Successful: {successful_tests}")
    print(f"  • Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Volume Fix Summary
    volume_status = test_results["tests"].get("system_analysis", {}).get("volume_fix_status", "UNKNOWN")
    print(f"\n🔧 Volume Column Fix Status: {volume_status}")
    
    # API Health Summary
    api_status = test_results["tests"].get("health_check", {}).get("api_status", "UNKNOWN")
    print(f"🏥 API Health Status: {api_status}")
    
    # Production API Summary
    prod_success = test_results["tests"].get("production_api", {}).get("success_rate", "UNKNOWN")
    print(f"🔌 Production API Tests: {prod_success}")
    
    # Save detailed report
    report_file = f"complete_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"\n💾 Detailed report saved: {report_file}")
    
    # Final Status
    if successful_tests == total_tests and volume_status == "FULLY_OPERATIONAL":
        print(f"\n🎉 ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL!")
        return 0
    elif successful_tests >= total_tests * 0.8:  # 80% success rate
        print(f"\n✅ MOST TESTS PASSED - SYSTEM OPERATIONAL WITH MINOR ISSUES")
        return 0
    else:
        print(f"\n❌ MULTIPLE TEST FAILURES - SYSTEM NEEDS ATTENTION")
        return 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
