#!/usr/bin/env python3
"""
Database Alert Verification - Direct database queries to verify alert storage
Tests the database layer for alert persistence and retrieval
"""

import os
import sys
import json
import psycopg2
import redis
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Optional, Dict, List, Any

class DatabaseAlertVerifier:
    def __init__(self):
        # Load environment variables
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        
        # Get database configuration
        self.database_url = os.getenv('DATABASE_URL')
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        self.test_results = []
    
    def log_test(self, step: str, status: str, details: str = ""):
        """Log test step with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        result = {
            'timestamp': timestamp,
            'step': step,
            'status': status,
            'details': details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
        print(f"[{timestamp}] {status_icon} {step}: {details}")
    
    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL database connection"""
        if not self.database_url:
            self.log_test("POSTGRES_CONN", "SKIP", "DATABASE_URL not configured")
            return True
        
        self.log_test("POSTGRES_CONN", "INFO", "Testing PostgreSQL connection...")
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            self.log_test("POSTGRES_CONN", "PASS", f"Connected to PostgreSQL: {version[:50]}...")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.log_test("POSTGRES_CONN", "FAIL", f"Connection error: {e}")
            return False
    
    def check_database_tables(self) -> Dict[str, bool]:
        """Check which tables exist in the database"""
        if not self.database_url:
            self.log_test("DB_TABLES", "SKIP", "DATABASE_URL not configured")
            return {}
        
        self.log_test("DB_TABLES", "INFO", "Checking database table structure...")
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Check for tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check specific tables we care about
            table_status = {
                'candle': 'candle' in tables,
                'alert': 'alert' in tables,
                'alerts': 'alerts' in tables,
            }
            
            found_tables = [name for name, exists in table_status.items() if exists]
            self.log_test("DB_TABLES", "PASS", f"Found tables: {found_tables}")
            
            cursor.close()
            conn.close()
            return table_status
            
        except Exception as e:
            self.log_test("DB_TABLES", "FAIL", f"Error checking tables: {e}")
            return {}
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection and alert storage"""
        self.log_test("REDIS_CONN", "INFO", "Testing Redis connection...")
        
        try:
            # Parse Redis URL
            if self.redis_url.startswith('redis://'):
                # Extract host and port from URL
                from urllib.parse import urlparse
                parsed = urlparse(self.redis_url)
                host = parsed.hostname or 'localhost'
                port = parsed.port or 6379
                db = int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0
            else:
                host, port, db = 'localhost', 6379, 0
            
            # Connect to Redis
            r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            
            # Test connection
            r.ping()
            
            self.log_test("REDIS_CONN", "PASS", f"Connected to Redis: {host}:{port}/{db}")
            return True
            
        except Exception as e:
            self.log_test("REDIS_CONN", "FAIL", f"Redis connection error: {e}")
            return False
    
    def check_redis_alert_keys(self) -> int:
        """Check Redis for alert-related keys"""
        self.log_test("REDIS_ALERTS", "INFO", "Scanning Redis for alert keys...")
        
        try:
            # Parse Redis URL and connect
            from urllib.parse import urlparse
            parsed = urlparse(self.redis_url)
            host = parsed.hostname or 'localhost'
            port = parsed.port or 6379
            db = int(parsed.path[1:]) if parsed.path and len(parsed.path) > 1 else 0
            
            r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            
            # Look for alert-related keys
            alert_keys = []
            patterns = ['alert:*', 'alerts:*', 'simple_alerts:*']
            
            for pattern in patterns:
                keys = r.keys(pattern)
                alert_keys.extend(keys)
            
            # Get some sample data
            sample_data = {}
            for key in alert_keys[:5]:  # Sample first 5 keys
                key_type = r.type(key)
                if key_type == 'string':
                    sample_data[key] = r.get(key)[:100] + "..." if len(r.get(key) or "") > 100 else r.get(key)
                elif key_type == 'hash':
                    sample_data[key] = dict(list(r.hgetall(key).items())[:3])
                elif key_type == 'list':
                    sample_data[key] = r.lrange(key, 0, 2)
            
            self.log_test("REDIS_ALERTS", "PASS", f"Found {len(alert_keys)} alert keys")
            if sample_data:
                self.log_test("REDIS_SAMPLE", "INFO", f"Sample data: {json.dumps(sample_data, indent=2)[:200]}...")
            
            return len(alert_keys)
            
        except Exception as e:
            self.log_test("REDIS_ALERTS", "FAIL", f"Error scanning Redis: {e}")
            return 0
    
    def verify_candle_data(self) -> int:
        """Check if candle data exists in database"""
        if not self.database_url:
            self.log_test("CANDLE_DATA", "SKIP", "DATABASE_URL not configured")
            return 0
        
        self.log_test("CANDLE_DATA", "INFO", "Checking candle data in database...")
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Check if candle table exists and has data
            cursor.execute("""
                SELECT COUNT(*), 
                       MIN(ts) as earliest, 
                       MAX(ts) as latest,
                       COUNT(DISTINCT symbol) as symbols
                FROM candle 
                LIMIT 1000;
            """)
            
            result = cursor.fetchone()
            count, earliest, latest, symbols = result
            
            if count > 0:
                self.log_test("CANDLE_DATA", "PASS", 
                    f"Found {count} candles, {symbols} symbols, {earliest} to {latest}")
            else:
                self.log_test("CANDLE_DATA", "INFO", "No candle data found (empty table)")
            
            cursor.close()
            conn.close()
            return count
            
        except Exception as e:
            self.log_test("CANDLE_DATA", "FAIL", f"Error checking candle data: {e}")
            return 0
    
    def run_verification(self):
        """Run complete database verification"""
        print("🔍 Database Alert Verification")
        print("=" * 40)
        print(f"🗄️  Database: {'✅ Configured' if self.database_url else '❌ Not configured'}")
        print(f"🔴 Redis: {self.redis_url}")
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test PostgreSQL
        postgres_ok = self.test_postgres_connection()
        if postgres_ok:
            table_status = self.check_database_tables()
            candle_count = self.verify_candle_data()
        
        # Test Redis
        redis_ok = self.test_redis_connection()
        if redis_ok:
            alert_key_count = self.check_redis_alert_keys()
        
        # Summary
        print("\n📊 Verification Summary:")
        print("-" * 30)
        
        passed = sum(1 for r in self.test_results if r['status'] == 'PASS')
        failed = sum(1 for r in self.test_results if r['status'] == 'FAIL')
        skipped = sum(1 for r in self.test_results if r['status'] == 'SKIP')
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️ Skipped: {skipped}")
        
        if failed == 0:
            print("\n🎉 Database verification completed successfully!")
        else:
            print(f"\n⚠️ {failed} verification(s) failed.")
        
        print("\n💡 Key Findings:")
        if postgres_ok:
            print("• PostgreSQL database is accessible")
        if redis_ok:
            print("• Redis connection is working")
            if 'alert_key_count' in locals():
                print(f"• Found {alert_key_count} alert-related keys in Redis")
        if 'candle_count' in locals() and candle_count > 0:
            print(f"• Database contains {candle_count} candle records")

def main():
    verifier = DatabaseAlertVerifier()
    
    try:
        verifier.run_verification()
    except KeyboardInterrupt:
        print("\n🛑 Verification interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
