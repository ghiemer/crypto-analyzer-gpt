# Alert System Fix - PostgreSQL Implementation

## Create alerts table in your PostgreSQL database

```sql
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL DEFAULT 'default',
    symbol VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    target_price DECIMAL(20,8),
    expression TEXT,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_alerts_user_symbol ON alerts(user_id, symbol);
CREATE INDEX idx_alerts_status ON alerts(status);
```

## Modified alerts.py implementation

```python
import asyncio
import pandas as pd
import asyncpg
from typing import Dict, Any, Optional, List
from .settings import settings
from .database import get_connection
from ..services.telegram_bot import send as tg_send

# PostgreSQL-based Alert System
class PostgreSQLAlertSystem:
    """Alert system using PostgreSQL instead of Redis."""
    
    def __init__(self):
        self._monitoring = False
        
    async def add_alert(self, user: str, symbol: str, expr: str, 
                       alert_type: str = 'expression', target_price: float = None, 
                       description: str = None):
        """Add new alert to PostgreSQL."""
        conn = await get_connection()
        try:
            await conn.execute("""
                INSERT INTO alerts (user_id, symbol, expression, alert_type, target_price, description)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user, symbol, expr, alert_type, target_price, description)
        finally:
            await conn.close()
    
    async def delete_alert(self, user: str, symbol: str):
        """Delete alert from PostgreSQL."""
        conn = await get_connection()
        try:
            await conn.execute("""
                DELETE FROM alerts WHERE user_id = $1 AND symbol = $2
            """, user, symbol)
        finally:
            await conn.close()
    
    async def list_alerts(self, user: str) -> List[Dict[str, Any]]:
        """List all alerts for user from PostgreSQL."""
        conn = await get_connection()
        try:
            rows = await conn.fetch("""
                SELECT id, symbol, alert_type, target_price, expression, 
                       description, status, created_at
                FROM alerts 
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC
            """, user)
            
            return [dict(row) for row in rows]
        finally:
            await conn.close()

# Global instance
pg_alert_system = PostgreSQLAlertSystem()

# Compatibility functions for existing code
async def add_alert(user: str, symbol: str, expr: str):
    await pg_alert_system.add_alert(user, symbol, expr)

async def delete_alert(user: str, symbol: str):
    await pg_alert_system.delete_alert(user, symbol)

async def list_alerts(user: str):
    return await pg_alert_system.list_alerts(user)
```

Would you like me to implement this PostgreSQL solution?
