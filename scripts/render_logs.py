#!/usr/bin/env python3
"""
Render Log Monitor - Automated log streaming without CLI interaction
Reads configuration from .env file and provides real-time log monitoring
"""

import os
import subprocess
import sys
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

class RenderLogMonitor:
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Get service configuration from environment
        self.service_id = os.getenv('RENDER_SERVICE_ID')
        self.service_name = os.getenv('RENDER_SERVICE_NAME', 'crypto-analyzer-gpt')
        self.auto_scroll = True
        self.running = False
        
        if not self.service_id:
            print("❌ RENDER_SERVICE_ID not found in .env file")
            print("📝 Please add RENDER_SERVICE_ID=your-service-id to your .env file")
            sys.exit(1)
    
    def start_monitoring(self, tail_lines=50, follow=True):
        """Start log monitoring with automatic output handling"""
        print(f"🚀 Starting Render log monitoring for {self.service_name}")
        print(f"📊 Service ID: {self.service_id}")
        print(f"⏰ Monitoring started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Build render logs command
        cmd = ['render', 'logs', self.service_id]
        if follow:
            cmd.append('--tail')
        
        try:
            # Start the process without shell interaction
            self.running = True
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Start threads for output handling
            stdout_thread = threading.Thread(
                target=self._handle_output,
                args=(process.stdout, "📊 LOG")
            )
            stderr_thread = threading.Thread(
                target=self._handle_output,
                args=(process.stderr, "⚠️  ERR")
            )
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for process or user interrupt
            try:
                while self.running and process.poll() is None:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                self.running = False
                process.terminate()
            
            # Wait for threads to finish
            stdout_thread.join(timeout=2)
            stderr_thread.join(timeout=2)
            
        except FileNotFoundError:
            print("❌ Render CLI not found. Please install it first:")
            print("   npm install -g @render/cli")
            print("   render auth login")
        except Exception as e:
            print(f"❌ Error starting log monitor: {e}")
    
    def _handle_output(self, pipe, prefix):
        """Handle output from subprocess without blocking"""
        try:
            for line in iter(pipe.readline, ''):
                if not self.running:
                    break
                if line.strip():
                    timestamp = time.strftime('%H:%M:%S')
                    print(f"[{timestamp}] {prefix} | {line.rstrip()}")
        except Exception as e:
            if self.running:
                print(f"❌ Output handler error: {e}")
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.running = False

def main():
    monitor = RenderLogMonitor()
    
    print("🔧 Render Log Monitor")
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        monitor.start_monitoring()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
