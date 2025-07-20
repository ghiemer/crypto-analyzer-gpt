#!/usr/bin/env python3
"""
Simple Log Fetcher
Gets recent logs from Render service without interactive interface
"""

import subprocess
import json
import sys
from datetime import datetime

def fetch_logs_simple(lines=50):
    """Fetch logs using render CLI in non-interactive mode"""
    
    print(f"🔍 Fetching last {lines} log lines from production...")
    
    # Use render logs with json output to avoid interactive mode
    cmd = [
        "/opt/homebrew/bin/render", "logs", "srv-d1rm3dfgi27c73cioohg", 
        "--tail", str(lines),
        "--no-color"  # Disable colors for cleaner output
    ]
    
    try:
        # Run with timeout and capture output
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=15,
            env={"RENDER_NON_INTERACTIVE": "1"}  # Force non-interactive mode
        )
        
        if result.returncode == 0:
            logs = result.stdout.strip().split('\n')
            logs = [log for log in logs if log.strip()]  # Filter empty lines
            
            print(f"✅ Retrieved {len(logs)} log lines")
            return logs
        else:
            print(f"❌ Error fetching logs: {result.stderr}")
            return []
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - trying alternative method...")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def analyze_logs(logs):
    """Analyze logs for key patterns"""
    if not logs:
        print("❌ No logs to analyze")
        return
    
    print(f"\n📊 LOG ANALYSIS")
    print("="*50)
    
    # Count different types of log entries
    errors = [log for log in logs if any(x in log.lower() for x in ['error', '❌', 'exception', 'traceback'])]
    warnings = [log for log in logs if any(x in log.lower() for x in ['warning', '⚠️', 'warn'])]
    alerts = [log for log in logs if any(x in log.lower() for x in ['alert', '🔍', 'checking', 'monitoring'])]
    volume_issues = [log for log in logs if 'volume' in log.lower()]
    api_calls = [log for log in logs if any(x in log for x in ['GET', 'POST', 'HTTP'])]
    
    print(f"📈 Log Statistics:")
    print(f"  • Total lines: {len(logs)}")
    print(f"  • Errors: {len(errors)}")
    print(f"  • Warnings: {len(warnings)}")
    print(f"  • Alert activity: {len(alerts)}")
    print(f"  • Volume-related: {len(volume_issues)}")
    print(f"  • API calls: {len(api_calls)}")
    
    # Volume fix status
    volume_errors = [log for log in logs if "Error getting enhanced price data" in log and "'volume'" in log]
    if volume_errors:
        print(f"\n❌ Volume Fix Status: ERRORS DETECTED ({len(volume_errors)} errors)")
        print("Recent volume errors:")
        for error in volume_errors[-3:]:
            print(f"  {error}")
    else:
        volume_successes = [log for log in logs if "checking" in log and "alerts" in log]
        if volume_successes:
            print(f"\n✅ Volume Fix Status: WORKING CORRECTLY")
            print("Recent successful activities:")
            for success in volume_successes[-3:]:
                print(f"  {success}")
        else:
            print(f"\n⚠️ Volume Fix Status: NO ACTIVITY DETECTED")
    
    # Recent activity
    print(f"\n📋 Recent Activity (last 5 entries):")
    for log in logs[-5:]:
        print(f"  {log}")
    
    # Error details
    if errors:
        print(f"\n❌ Error Details:")
        for error in errors[-3:]:  # Show last 3 errors
            print(f"  {error}")
    else:
        print(f"\n✅ No errors detected in recent logs")

def main():
    """Main execution"""
    lines = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    print("🚀 SIMPLE LOG ANALYSIS")
    print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
    print("="*50)
    
    logs = fetch_logs_simple(lines)
    analyze_logs(logs)
    
    print(f"\n💾 Analysis complete at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    main()
