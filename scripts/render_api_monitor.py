#!/usr/bin/env python3
"""
Render API Log Monitor - Direct API access without CLI interaction
Uses Render API directly to stream logs without CLI interface
"""

import os
import sys
import time
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

class RenderAPIMonitor:
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Get configuration from environment
        self.service_id = os.getenv('RENDER_SERVICE_ID')
        self.service_name = os.getenv('RENDER_SERVICE_NAME', 'crypto-analyzer-gpt')
        
        # Note: Render API token would need to be set up separately
        # This is a conceptual implementation - Render's API might be different
        self.api_token = os.getenv('RENDER_API_TOKEN')
        
        if not self.service_id:
            print("❌ RENDER_SERVICE_ID not found in .env file")
            print("📝 Please add RENDER_SERVICE_ID=your-service-id to your .env file")
            sys.exit(1)
        
        self.base_url = "https://api.render.com"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json"
        } if self.api_token else {}
    
    def fetch_recent_logs(self, limit: int = 100) -> Optional[List[Dict]]:
        """Fetch recent logs from Render API"""
        if not self.api_token:
            print("⚠️ RENDER_API_TOKEN not configured - using alternative method")
            return self._fetch_via_curl()
        
        try:
            url = f"{self.base_url}/v1/services/{self.service_id}/logs"
            params = {"limit": limit}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json().get('logs', [])
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return None
    
    def _fetch_via_curl(self) -> Optional[List[Dict]]:
        """Alternative: Use curl to get logs without interactive mode"""
        print("🔄 Attempting to fetch logs via alternative method...")
        
        # Try to use render logs with output capture
        import subprocess
        
        try:
            # Use timeout and capture output
            if self.service_id:
                result = subprocess.run([
                    'timeout', '10s', 'render', 'logs', self.service_id
                ], capture_output=True, text=True, timeout=15)
            else:
                return None
            
            if result.stdout:
                # Parse the output into log entries
                lines = result.stdout.strip().split('\n')
                logs = []
                for line in lines:
                    if line.strip():
                        logs.append({
                            'timestamp': datetime.now(timezone.utc).isoformat(),
                            'message': line.strip(),
                            'level': 'INFO'
                        })
                return logs
            else:
                print("❌ No log output received")
                return None
                
        except subprocess.TimeoutExpired:
            print("⏱️ Log fetch timeout - render CLI might be in interactive mode")
            return None
        except FileNotFoundError:
            print("❌ Render CLI not found")
            return None
        except Exception as e:
            print(f"❌ Error fetching logs: {e}")
            return None
    
    def start_monitoring_simple(self, interval: int = 5):
        """Simple polling-based log monitoring"""
        print(f"🚀 Starting simple log monitoring for {self.service_name}")
        print(f"📊 Service ID: {self.service_id}")
        print(f"🔄 Refresh interval: {interval}s")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("💡 Press Ctrl+C to stop")
        print()
        
        last_seen_logs = set()
        
        try:
            while True:
                logs = self.fetch_recent_logs(limit=50)
                
                if logs:
                    new_logs = []
                    for log in logs:
                        log_id = f"{log.get('timestamp', '')}-{hash(log.get('message', ''))}"
                        if log_id not in last_seen_logs:
                            new_logs.append(log)
                            last_seen_logs.add(log_id)
                    
                    # Display new logs
                    for log in new_logs[-10:]:  # Show last 10 new logs
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        message = log.get('message', '')
                        level = log.get('level', 'INFO')
                        
                        # Color coding
                        if 'ERROR' in message.upper() or level == 'ERROR':
                            prefix = "🔴 ERR"
                        elif 'WARN' in message.upper() or level == 'WARN':
                            prefix = "🟡 WARN"
                        elif 'INFO' in message.upper() or level == 'INFO':
                            prefix = "🔵 INFO"
                        else:
                            prefix = "📊 LOG"
                        
                        print(f"[{timestamp}] {prefix} | {message}")
                    
                    # Keep only recent log IDs to prevent memory growth
                    if len(last_seen_logs) > 1000:
                        last_seen_logs = set(list(last_seen_logs)[-500:])
                
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 No new logs...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")

def main():
    print("🔧 Render API Log Monitor")
    print("==========================")
    
    monitor = RenderAPIMonitor()
    
    try:
        monitor.start_monitoring_simple()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
