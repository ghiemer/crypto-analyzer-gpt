#!/usr/bin/env python3
"""
Log Fetcher Script
Fetch and analyze production logs from Render using CLI commands
"""

import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import argparse
import time

class LogFetcher:
    def __init__(self, service_id: str = "srv-d1rm3dfgi27c73cioohg"):
        self.service_id = service_id
        self.log_patterns = {
            "errors": r"ERROR|❌|CRITICAL|Exception|Traceback",
            "warnings": r"WARNING|⚠️|WARN",
            "alerts": r"🔍|📊 Monitoring|alert",
            "volume_issues": r"volume|vol_base|vol_quote|vol_usdt",
            "stream_activity": r"Universal Stream|price stream|subscription",
            "api_calls": r"GET|POST|PUT|DELETE|HTTP",
            "startup": r"startup|started|Application startup complete"
        }
        
    def fetch_logs(self, lines: int = 100, follow: bool = False, filter_pattern: Optional[str] = None) -> List[str]:
        """Fetch logs using Render CLI"""
        cmd = ["render", "logs", self.service_id, "--tail", str(lines)]
        
        if follow:
            cmd.append("--follow")
            
        print(f"🔍 Fetching logs: {' '.join(cmd)}")
        
        try:
            if follow:
                # For follow mode, we need to handle streaming
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                         universal_newlines=True, bufsize=1)
                
                logs = []
                print("📡 Following logs (Ctrl+C to stop)...")
                try:
                    for line in iter(process.stdout.readline, ''):
                        if line.strip():
                            logs.append(line.strip())
                            if not filter_pattern or re.search(filter_pattern, line, re.IGNORECASE):
                                print(line.strip())
                except KeyboardInterrupt:
                    print("\n⏹️ Stopped following logs")
                    process.terminate()
                
                return logs
            else:
                # For static fetch
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    print(f"❌ Error fetching logs: {result.stderr}")
                    return []
                
                logs = result.stdout.strip().split('\n')
                return [log for log in logs if log.strip()]
                
        except subprocess.TimeoutExpired:
            print("⏰ Timeout waiting for logs")
            return []
        except Exception as e:
            print(f"❌ Error executing render command: {e}")
            return []
    
    def analyze_logs(self, logs: List[str]) -> Dict:
        """Analyze logs for patterns and issues"""
        analysis = {
            "total_lines": len(logs),
            "timestamp": datetime.now().isoformat(),
            "patterns_found": {},
            "error_details": [],
            "volume_fix_status": "unknown",
            "system_health": {},
            "recent_activity": []
        }
        
        # Pattern analysis
        for pattern_name, pattern in self.log_patterns.items():
            matches = [log for log in logs if re.search(pattern, log, re.IGNORECASE)]
            analysis["patterns_found"][pattern_name] = {
                "count": len(matches),
                "examples": matches[:3]  # First 3 examples
            }
        
        # Error analysis
        error_logs = analysis["patterns_found"]["errors"]["examples"]
        for error in error_logs:
            analysis["error_details"].append({
                "timestamp": self._extract_timestamp(error),
                "message": error
            })
        
        # Volume fix status
        volume_errors = [log for log in logs if "Error getting enhanced price data" in log and "volume" in log]
        if volume_errors:
            analysis["volume_fix_status"] = "❌ Volume errors still present"
            analysis["volume_errors_count"] = len(volume_errors)
        else:
            volume_successes = [log for log in logs if "checking" in log and "alerts" in log]
            if volume_successes:
                analysis["volume_fix_status"] = "✅ Volume fix working - price monitoring active"
            else:
                analysis["volume_fix_status"] = "⚠️ No volume activity detected"
        
        # System health indicators
        startup_logs = analysis["patterns_found"]["startup"]["examples"]
        if startup_logs:
            analysis["system_health"]["last_startup"] = startup_logs[-1]
            analysis["system_health"]["startup_count"] = len(startup_logs)
        
        api_logs = analysis["patterns_found"]["api_calls"]["examples"]
        if api_logs:
            analysis["system_health"]["api_activity"] = len(api_logs)
            analysis["system_health"]["recent_api_calls"] = api_logs[-3:]
        
        # Recent activity (last 10 logs)
        analysis["recent_activity"] = logs[-10:] if logs else []
        
        return analysis
    
    def _extract_timestamp(self, log_line: str) -> Optional[str]:
        """Extract timestamp from log line"""
        # Pattern for Render logs: 2025-07-20 10:59:42
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log_line)
        return timestamp_match.group(1) if timestamp_match else None
    
    def generate_report(self, analysis: Dict):
        """Generate human-readable report"""
        print("\n" + "="*60)
        print("📊 LOG ANALYSIS REPORT")
        print("="*60)
        print(f"⏰ Analysis Time: {analysis['timestamp']}")
        print(f"📄 Total Log Lines: {analysis['total_lines']}")
        
        # Volume fix status
        print(f"\n🔧 Volume Fix Status: {analysis['volume_fix_status']}")
        
        # Pattern summary
        print(f"\n🔍 Pattern Analysis:")
        for pattern_name, data in analysis["patterns_found"].items():
            if data["count"] > 0:
                print(f"  • {pattern_name.title()}: {data['count']} matches")
        
        # Error details
        if analysis["error_details"]:
            print(f"\n❌ Error Details ({len(analysis['error_details'])}):")
            for error in analysis["error_details"][:5]:  # Show max 5 errors
                print(f"  • {error['timestamp']}: {error['message'][:100]}...")
        else:
            print(f"\n✅ No errors detected in recent logs")
        
        # System health
        if analysis["system_health"]:
            print(f"\n🏥 System Health:")
            for key, value in analysis["system_health"].items():
                if isinstance(value, list):
                    print(f"  • {key}: {len(value)} entries")
                else:
                    print(f"  • {key}: {value}")
        
        # Recent activity
        if analysis["recent_activity"]:
            print(f"\n📈 Recent Activity (last 10 logs):")
            for log in analysis["recent_activity"]:
                print(f"  {log}")
    
    def save_report(self, analysis: Dict, filename: Optional[str] = None):
        """Save analysis report to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"log_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n💾 Report saved: {filename}")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description="Fetch and analyze production logs")
    parser.add_argument("--lines", "-n", type=int, default=100, 
                       help="Number of log lines to fetch (default: 100)")
    parser.add_argument("--follow", "-f", action="store_true", 
                       help="Follow logs in real-time")
    parser.add_argument("--filter", type=str, 
                       help="Filter logs by pattern")
    parser.add_argument("--service-id", default="srv-d1rm3dfgi27c73cioohg", 
                       help="Render service ID")
    parser.add_argument("--save", action="store_true", 
                       help="Save analysis to file")
    
    args = parser.parse_args()
    
    # Initialize log fetcher
    fetcher = LogFetcher(args.service_id)
    
    # Fetch logs
    print(f"🚀 Fetching {args.lines} log lines from Render service...")
    logs = fetcher.fetch_logs(lines=args.lines, follow=args.follow, filter_pattern=args.filter)
    
    if not logs:
        print("❌ No logs retrieved")
        return
    
    if not args.follow:  # Only analyze if not in follow mode
        # Analyze logs
        print(f"🔍 Analyzing {len(logs)} log lines...")
        analysis = fetcher.analyze_logs(logs)
        
        # Generate report
        fetcher.generate_report(analysis)
        
        # Save if requested
        if args.save:
            fetcher.save_report(analysis)

if __name__ == "__main__":
    main()
