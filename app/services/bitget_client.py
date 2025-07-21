"""
Klassenbasierte Bitget API Client Implementation
Ersetzt die funktionalen Services durch eine strukturierte Klasse
Behält Backward Compatibility durch Wrapper-Funktionen
"""

import httpx
import pandas as pd
import datetime as dt
from typing import Optional, Dict, Any, List
from fastapi_cache import FastAPICache

from ..core.errors import BAD_ARGUMENT, UPSTREAM
from ..core.settings import settings


class BitgetAPIClient:
    """
    Klassenbasierte Bitget API Client für Agent Framework Integration
    
    Bietet strukturierte Methoden für:
    - Kerzendaten (OHLCV)
    - Orderbook Daten
    - Funding Rates
    - Open Interest
    - HTTP Caching
    """
    
    BASE_URL = "https://api.bitget.com/api/v2"
    ALLOWED_GRANULARITIES = {
        "1min", "3min", "5min", "15min", "30min", "1h", "2h", 
        "4h", "6h", "12h", "1day", "3day", "1week", "1M"
    }
    
    def __init__(self, cache_enabled: Optional[bool] = None, timeout: int = 10):
        """
        Initialize Bitget API Client
        
        Args:
            cache_enabled: Enable/disable caching (defaults to settings.CACHE_ENABLED)
            timeout: HTTP request timeout in seconds
        """
        self.cache_enabled = cache_enabled if cache_enabled is not None else settings.CACHE_ENABLED
        self.timeout = timeout
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    def _normalize_granularity(self, granularity: str) -> str:
        """
        Normalize granularity string to Bitget format
        
        Args:
            granularity: Time granularity (e.g., "1m", "1min", "1h")
            
        Returns:
            Normalized granularity string
            
        Raises:
            BAD_ARGUMENT: If granularity is not supported
        """
        granularity = granularity.lower()
        if granularity.endswith("m") and not granularity.endswith("min"):
            granularity = granularity.replace("m", "min")
        
        if granularity not in self.ALLOWED_GRANULARITIES:
            raise BAD_ARGUMENT(f"Granularity '{granularity}' not supported. Allowed: {sorted(self.ALLOWED_GRANULARITIES)}")
        
        return granularity
    
    def _timestamp_to_ms(self, timestamp: dt.datetime) -> int:
        """Convert datetime to milliseconds timestamp"""
        return int(timestamp.replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
    
    async def _make_request(self, path: str, params: Dict[str, Any], ttl: int = 15) -> Any:
        """
        Make HTTP request to Bitget API with caching
        
        Args:
            path: API endpoint path
            params: Query parameters
            ttl: Cache TTL in seconds
            
        Returns:
            API response data
            
        Raises:
            BAD_ARGUMENT: For 400-level errors
            UPSTREAM: For API or network errors
        """
        cache_key = f"bitget:{path}:{str(sorted(params.items()))}"
        
        # Try cache first
        if self.cache_enabled:
            cached_data = await self._get_from_cache(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Make HTTP request
        try:
            if not self.session:
                self.session = httpx.AsyncClient(timeout=self.timeout)
            
            response = await self.session.get(f"{self.BASE_URL}{path}", params=params)
            
            # Handle HTTP errors
            if response.status_code >= 400:
                await self._handle_http_error(response)
            
            # Parse JSON response
            data = response.json()
            if "data" not in data:
                raise UPSTREAM(f"Unexpected Bitget API response format: {data}")
            
            result = data["data"]
            
            # Cache successful response
            if self.cache_enabled and result:
                await self._save_to_cache(cache_key, result, ttl)
            
            return result
            
        except httpx.RequestError as e:
            raise UPSTREAM(f"Bitget API request failed: {str(e)}")
        except Exception as e:
            from ..core.errors import ApiError
            if isinstance(e, ApiError):
                raise
            raise UPSTREAM(f"Bitget API error: {str(e)}")
    
    async def _handle_http_error(self, response: httpx.Response):
        """Handle HTTP error responses"""
        try:
            error_data = response.json()
            error_msg = error_data.get("msg", response.text)
            
            if "not found" in error_msg.lower():
                raise BAD_ARGUMENT(f"Symbol or parameter not found: {error_msg}")
            elif "limit" in error_msg.lower():
                raise BAD_ARGUMENT(f"Invalid limit parameter: {error_msg}")
            else:
                raise UPSTREAM(f"Bitget API error: {response.status_code} - {error_msg}")
                
        except ValueError:
            # Response is not JSON
            raise UPSTREAM(f"Bitget API error: {response.status_code} - {response.text}")
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if available"""
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cache_backend = FastAPICache._backend
                return await cache_backend.get(key)
        except Exception:
            pass
        return None
    
    async def _save_to_cache(self, key: str, data: Any, ttl: int):
        """Save data to cache if available"""
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cache_backend = FastAPICache._backend
                await cache_backend.set(key, data, expire=ttl)
        except Exception:
            pass
    
    async def get_candles(
        self,
        symbol: str,
        granularity: str = "1h",
        limit: int = 200,
        product_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get OHLCV candle data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            granularity: Time granularity (e.g., "1h", "1min", "1day")
            limit: Number of candles to retrieve (max 1000)
            product_type: Product type for derivatives ("usdt-futures")
            start_time: Start time (ISO format or timestamp)
            end_time: End time (ISO format or timestamp)
            
        Returns:
            DataFrame with columns: ts, open, high, low, close, vol_base, vol_quote, vol_usdt
        """
        granularity = self._normalize_granularity(granularity)
        path = "/mix/market/candles" if product_type else "/spot/market/candles"
        
        params = {
            "symbol": symbol,
            "granularity": granularity,
            "limit": min(limit, 1000)  # Bitget limit
        }
        
        if product_type:
            params["productType"] = product_type
            
        if start_time:
            params["startTime"] = (
                int(start_time) if start_time.isdigit() 
                else self._timestamp_to_ms(dt.datetime.fromisoformat(start_time))
            )
            
        if end_time:
            params["endTime"] = (
                int(end_time) if end_time.isdigit()
                else self._timestamp_to_ms(dt.datetime.fromisoformat(end_time))
            )
        
        raw_data = await self._make_request(path, params)
        
        # Convert to DataFrame
        columns = ["ts", "open", "high", "low", "close", "vol_base", "vol_quote", "vol_usdt"]
        df = (
            pd.DataFrame(raw_data, columns=columns)
            .astype({
                "open": float, "high": float, "low": float, "close": float,
                "vol_base": float, "vol_quote": float, "vol_usdt": float
            })
            .assign(ts=lambda d: pd.to_datetime(pd.to_numeric(d.ts, errors='coerce'), unit="ms", utc=True))
            .sort_values("ts")
            .reset_index(drop=True)
        )
        
        return df
    
    async def get_orderbook(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get orderbook data for a symbol
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
            limit: Number of bids/asks to retrieve (1-100)
            
        Returns:
            Dict with bestBid, bestAsk, spread, bids, asks
        """
        # Validate and clamp limit
        limit = max(1, min(limit, 100))
        
        raw_data = await self._make_request(
            "/spot/market/merge-depth",
            {"symbol": symbol, "limit": limit}
        )
        
        bids = [(float(price), float(quantity)) for price, quantity in raw_data["bids"]]
        asks = [(float(price), float(quantity)) for price, quantity in raw_data["asks"]]
        
        if not bids or not asks:
            raise UPSTREAM("Empty orderbook data received")
        
        spread = asks[0][0] - bids[0][0]
        
        return {
            "bestBid": bids[0][0],
            "bestAsk": asks[0][0],
            "spread": spread,
            "bids": bids,
            "asks": asks,
            "symbol": symbol
        }
    
    async def get_funding_rate(self, symbol: str, product_type: str = "usdt-futures") -> Dict[str, Any]:
        """
        Get current funding rate for a futures symbol
        
        Args:
            symbol: Futures symbol (e.g., "BTCUSDT")
            product_type: Product type (default: "usdt-futures")
            
        Returns:
            Dict with funding rate information
        """
        return await self._make_request(
            "/mix/market/current-fund-rate",
            {"symbol": symbol, "productType": product_type}
        )
    
    async def get_open_interest(self, symbol: str, product_type: str = "usdt-futures") -> Dict[str, Any]:
        """
        Get open interest for a futures symbol
        
        Args:
            symbol: Futures symbol (e.g., "BTCUSDT")
            product_type: Product type (default: "usdt-futures")
            
        Returns:
            Dict with open interest information
        """
        return await self._make_request(
            "/mix/market/open-interest",
            {"symbol": symbol, "productType": product_type}
        )
    
    def get_supported_granularities(self) -> List[str]:
        """Get list of supported granularities"""
        return sorted(self.ALLOWED_GRANULARITIES)
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for Agent Framework
        
        Returns:
            Dict with tool metadata and available methods
        """
        return {
            "name": "BitgetAPIClient",
            "description": "Bitget API Client for cryptocurrency market data",
            "methods": {
                "get_candles": {
                    "description": "Get OHLCV candle data",
                    "parameters": {
                        "symbol": {"type": "string", "required": True},
                        "granularity": {"type": "string", "default": "1h"},
                        "limit": {"type": "integer", "default": 200}
                    }
                },
                "get_orderbook": {
                    "description": "Get orderbook data",
                    "parameters": {
                        "symbol": {"type": "string", "required": True},
                        "limit": {"type": "integer", "default": 5}
                    }
                },
                "get_funding_rate": {
                    "description": "Get funding rate for futures",
                    "parameters": {
                        "symbol": {"type": "string", "required": True}
                    }
                },
                "get_open_interest": {
                    "description": "Get open interest for futures",
                    "parameters": {
                        "symbol": {"type": "string", "required": True}
                    }
                }
            }
        }


# Singleton instance for global access
_bitget_client_instance: Optional[BitgetAPIClient] = None

def get_bitget_client() -> BitgetAPIClient:
    """Get global BitgetAPIClient instance"""
    global _bitget_client_instance
    if _bitget_client_instance is None:
        _bitget_client_instance = BitgetAPIClient()
    return _bitget_client_instance


# Backward compatibility wrapper functions
async def candles(symbol: str, granularity="1h", limit=200, product_type=None, start=None, end=None):
    """Backward compatibility wrapper for candles function"""
    client = get_bitget_client()
    return await client.get_candles(
        symbol=symbol,
        granularity=granularity,
        limit=limit,
        product_type=product_type,
        start_time=start,
        end_time=end
    )

async def orderbook(symbol: str, limit=5):
    """Backward compatibility wrapper for orderbook function"""
    client = get_bitget_client()
    return await client.get_orderbook(symbol, limit)

async def funding(symbol: str):
    """Backward compatibility wrapper for funding function"""
    client = get_bitget_client()
    return await client.get_funding_rate(symbol)

async def open_interest(symbol: str):
    """Backward compatibility wrapper for open_interest function"""
    client = get_bitget_client()
    return await client.get_open_interest(symbol)
