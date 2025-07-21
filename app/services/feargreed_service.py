"""
Klassenbasierte Fear & Greed Index Service Implementation
Ersetzt die funktionale feargreed.py durch eine strukturierte Klasse
Behält Backward Compatibility durch Wrapper-Funktionen
"""

import httpx
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi_cache import FastAPICache
from ..core.settings import settings

logger = logging.getLogger(__name__)


class FearGreedIndexService:
    """
    Klassenbasierte Service für Fear & Greed Index
    
    Bietet strukturierte Methoden für:
    - Fear & Greed Index Daten
    - Historische Daten
    - Cache Management
    - Agent Framework Integration
    """
    
    def __init__(self, cache_enabled: Optional[bool] = None, timeout: int = 10):
        """
        Initialize Fear & Greed Index Service
        
        Args:
            cache_enabled: Enable/disable caching (defaults to settings.CACHE_ENABLED)
            timeout: HTTP request timeout in seconds
        """
        self.cache_enabled = cache_enabled if cache_enabled is not None else settings.CACHE_ENABLED
        self.timeout = timeout
        self.base_url = "https://api.alternative.me/fng"
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
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if available"""
        if not self.cache_enabled:
            return None
        
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cache_backend = FastAPICache._backend
                return await cache_backend.get(key)
        except Exception as e:
            logger.debug(f"Cache get failed for key {key}: {e}")
        return None
    
    async def _save_to_cache(self, key: str, data: Any, ttl: int):
        """Save data to cache if available"""
        if not self.cache_enabled:
            return
        
        try:
            if hasattr(FastAPICache, '_backend') and FastAPICache._backend:
                cache_backend = FastAPICache._backend
                await cache_backend.set(key, data, expire=ttl)
        except Exception as e:
            logger.debug(f"Cache set failed for key {key}: {e}")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make HTTP request to Fear & Greed API
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            httpx.RequestError: For network errors
            httpx.HTTPStatusError: For HTTP errors
        """
        if not self.session:
            self.session = httpx.AsyncClient(timeout=self.timeout)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = await self.session.get(url, params=params or {})
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except httpx.RequestError as e:
            logger.error(f"Fear & Greed API request failed: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Fear & Greed API HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"Fear & Greed API error: {e}")
            raise
    
    async def get_current_index(self) -> Dict[str, Any]:
        """
        Get current Fear & Greed Index value
        
        Returns:
            Dict with current fear & greed data
        """
        cache_key = "fng:current"
        
        # Try cache first
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            logger.debug("Returning cached Fear & Greed data")
            return cached_data
        
        # Fetch from API
        try:
            response = await self._make_request("/")
            
            if "data" not in response or not response["data"]:
                raise ValueError("Invalid Fear & Greed API response format")
            
            current_data = response["data"][0]
            
            # Enhance data with additional info
            enhanced_data = {
                **current_data,
                "fetched_at": datetime.now().isoformat(),
                "classification": self._classify_fear_greed_value(int(current_data.get("value", 0)))
            }
            
            # Cache for 1 hour
            await self._save_to_cache(cache_key, enhanced_data, ttl=3600)
            
            logger.info(f"Fear & Greed Index: {enhanced_data.get('value')} ({enhanced_data.get('value_classification')})")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"Failed to fetch Fear & Greed Index: {e}")
            raise
    
    async def get_historical_data(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical Fear & Greed Index data
        
        Args:
            days: Number of days to fetch (1-200)
            
        Returns:
            List of historical fear & greed data
        """
        # Validate days parameter
        days = max(1, min(days, 200))  # API limit is 200 days
        
        cache_key = f"fng:historical:{days}"
        
        # Try cache first (shorter cache time for historical data)
        cached_data = await self._get_from_cache(cache_key)
        if cached_data:
            logger.debug(f"Returning cached historical Fear & Greed data ({days} days)")
            return cached_data
        
        try:
            response = await self._make_request("/", params={"limit": days})
            
            if "data" not in response or not response["data"]:
                raise ValueError("Invalid Fear & Greed API response format")
            
            historical_data = response["data"]
            
            # Enhance each data point
            for data_point in historical_data:
                data_point["classification"] = self._classify_fear_greed_value(int(data_point.get("value", 0)))
            
            # Cache for 30 minutes
            await self._save_to_cache(cache_key, historical_data, ttl=1800)
            
            logger.info(f"Fetched {len(historical_data)} days of Fear & Greed historical data")
            return historical_data
            
        except Exception as e:
            logger.error(f"Failed to fetch historical Fear & Greed data: {e}")
            raise
    
    def _classify_fear_greed_value(self, value: int) -> Dict[str, Any]:
        """
        Classify Fear & Greed value into categories
        
        Args:
            value: Fear & Greed value (0-100)
            
        Returns:
            Dict with classification info
        """
        if value <= 25:
            category = "Extreme Fear"
            color = "🔴"
            signal = "potential_buy"
            description = "Market shows extreme fear, potential buying opportunity"
        elif value <= 45:
            category = "Fear"
            color = "🟠"
            signal = "cautious_buy"
            description = "Market shows fear, consider cautious buying"
        elif value <= 55:
            category = "Neutral"
            color = "🟡"
            signal = "neutral"
            description = "Market sentiment is neutral"
        elif value <= 75:
            category = "Greed"
            color = "🟢"
            signal = "cautious_sell"
            description = "Market shows greed, consider taking some profits"
        else:
            category = "Extreme Greed"
            color = "🔴"
            signal = "potential_sell"
            description = "Market shows extreme greed, potential selling opportunity"
        
        return {
            "category": category,
            "color": color,
            "signal": signal,
            "description": description,
            "value": value
        }
    
    async def get_market_sentiment_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive market sentiment analysis
        
        Returns:
            Dict with detailed sentiment analysis
        """
        try:
            current = await self.get_current_index()
            historical = await self.get_historical_data(7)  # Last 7 days
            
            # Calculate trends
            values = [int(d["value"]) for d in historical]
            avg_7d = sum(values) / len(values) if values else 0
            
            # Trend analysis
            trend = "stable"
            if len(values) >= 2:
                recent_avg = sum(values[:3]) / 3  # Last 3 days
                older_avg = sum(values[3:]) / len(values[3:]) if len(values) > 3 else recent_avg
                
                if recent_avg > older_avg + 5:
                    trend = "increasing_greed"
                elif recent_avg < older_avg - 5:
                    trend = "increasing_fear"
            
            analysis = {
                "current": current,
                "seven_day_average": round(avg_7d, 1),
                "trend": trend,
                "trend_strength": abs(round(values[0] - avg_7d, 1)) if values else 0,
                "recommendation": self._get_trading_recommendation(current, trend),
                "analysis_timestamp": datetime.now().isoformat(),
                "data_points": len(historical)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to generate sentiment analysis: {e}")
            raise
    
    def _get_trading_recommendation(self, current: Dict[str, Any], trend: str) -> Dict[str, Any]:
        """Generate trading recommendation based on current data and trend"""
        value = int(current.get("value", 50))
        classification = current.get("classification", {})
        
        # Base recommendation from classification
        base_signal = classification.get("signal", "neutral")
        
        # Modify based on trend
        if trend == "increasing_fear" and value < 30:
            recommendation = "strong_buy"
            description = "Extreme fear with increasing trend - strong buying opportunity"
            confidence = "high"
        elif trend == "increasing_greed" and value > 70:
            recommendation = "strong_sell"
            description = "Extreme greed with increasing trend - consider taking profits"
            confidence = "high"
        elif base_signal == "potential_buy" and trend != "increasing_greed":
            recommendation = "buy"
            description = "Fear levels suggest buying opportunity"
            confidence = "medium"
        elif base_signal == "potential_sell" and trend != "increasing_fear":
            recommendation = "sell"
            description = "Greed levels suggest taking profits"
            confidence = "medium"
        else:
            recommendation = "hold"
            description = "Mixed signals, consider holding current positions"
            confidence = "low"
        
        return {
            "action": recommendation,
            "description": description,
            "confidence": confidence,
            "based_on": f"Value: {value}, Trend: {trend}"
        }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for Agent Framework
        
        Returns:
            Dict with tool metadata and available methods
        """
        return {
            "name": "FearGreedIndexService",
            "description": "Fear & Greed Index sentiment analysis service",
            "methods": {
                "get_current_index": {
                    "description": "Get current Fear & Greed Index value",
                    "parameters": {}
                },
                "get_historical_data": {
                    "description": "Get historical Fear & Greed Index data",
                    "parameters": {
                        "days": {"type": "integer", "default": 30, "description": "Number of days (1-200)"}
                    }
                },
                "get_market_sentiment_analysis": {
                    "description": "Get comprehensive market sentiment analysis",
                    "parameters": {}
                }
            },
            "data_source": "alternative.me Fear & Greed Index API",
            "update_frequency": "Daily",
            "cache_ttl": 3600
        }


# Singleton instance for global access
_fear_greed_service_instance: Optional[FearGreedIndexService] = None

def get_fear_greed_service() -> FearGreedIndexService:
    """Get global FearGreedIndexService instance"""
    global _fear_greed_service_instance
    if _fear_greed_service_instance is None:
        _fear_greed_service_instance = FearGreedIndexService()
    return _fear_greed_service_instance


# Backward compatibility wrapper function
async def fear_greed():
    """Backward compatibility wrapper for fear_greed function"""
    service = get_fear_greed_service()
    current_data = await service.get_current_index()
    
    # Return in old format for backward compatibility
    return {
        "value": current_data.get("value"),
        "value_classification": current_data.get("value_classification"),
        "timestamp": current_data.get("timestamp")
    }
