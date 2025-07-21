"""
Klassenbasierte Technical Indicator Service Implementation
Ersetzt die funktionalen Indicator Services durch eine strukturierte Klasse
Behält Backward Compatibility durch Wrapper-Funktionen
"""

import pandas as pd
import pandas_ta as ta
from typing import Callable, Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicatorService:
    """
    Klassenbasierte Service für technische Indikatoren
    
    Bietet strukturierte Methoden für:
    - Standard Indikatoren (SMA, RSI, MACD, Bollinger Bands, etc.)
    - Batch Berechnungen
    - Custom Indicator Registration
    - Agent Framework Integration
    """
    
    def __init__(self):
        """Initialize Technical Indicator Service"""
        self._indicators: Dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}
        self._register_default_indicators()
    
    def _safe_series_wrap(self, series: Union[pd.Series, None], name: str) -> pd.DataFrame:
        """
        Safely wrap a Series into a DataFrame with proper name
        
        Args:
            series: Pandas Series or None
            name: Column name for the resulting DataFrame
            
        Returns:
            DataFrame with the series data or empty DataFrame if None
        """
        if series is None:
            return pd.DataFrame({name: pd.Series(dtype=float)})
        
        if isinstance(series, pd.Series):
            return series.rename(name).to_frame()
        
        return pd.DataFrame({name: series})
    
    def _safe_indicator_wrapper(self, indicator_func: Callable, name: str) -> Callable:
        """
        Create a safe wrapper around indicator functions that might fail
        
        Args:
            indicator_func: Function that calculates the indicator
            name: Name of the indicator for error reporting
            
        Returns:
            Wrapped function that handles errors gracefully
        """
        def wrapper(df: pd.DataFrame) -> pd.DataFrame:
            try:
                result = indicator_func(df)
                if result is None:
                    logger.warning(f"Indicator {name} returned None")
                    return pd.DataFrame({name: pd.Series(dtype=float)})
                
                if isinstance(result, pd.DataFrame):
                    return result
                
                return self._safe_series_wrap(result, name)
                
            except Exception as e:
                logger.warning(f"Indicator {name} calculation failed: {e}")
                return pd.DataFrame({name: pd.Series(dtype=float)})
        
        return wrapper
    
    def _register_default_indicators(self):
        """Register all default technical indicators"""
        
        # Moving Averages
        self._indicators["sma_20"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.sma(df['close'], length=20), "sma_20"), "sma_20"
        )
        self._indicators["sma_50"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.sma(df['close'], length=50), "sma_50"), "sma_50"
        )
        self._indicators["sma_200"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.sma(df['close'], length=200), "sma_200"), "sma_200"
        )
        
        self._indicators["ema_12"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.ema(df['close'], length=12), "ema_12"), "ema_12"
        )
        self._indicators["ema_26"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.ema(df['close'], length=26), "ema_26"), "ema_26"
        )
        
        # Momentum Indicators
        self._indicators["rsi_14"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.rsi(df['close'], length=14), "rsi_14"), "rsi_14"
        )
        
        # MACD - returns DataFrame with multiple columns
        self._indicators["macd"] = self._safe_indicator_wrapper(
            lambda df: ta.macd(df['close']) or pd.DataFrame(), "macd"
        )
        
        # Stochastic
        self._indicators["stoch"] = self._safe_indicator_wrapper(
            lambda df: ta.stoch(df['high'], df['low'], df['close']) or pd.DataFrame(), "stoch"
        )
        
        # Volatility Indicators
        # Bollinger Bands
        self._indicators["bbands"] = self._safe_indicator_wrapper(
            lambda df: ta.bbands(df['close'], length=20) or pd.DataFrame(), "bbands"
        )
        
        # Individual Bollinger Band lines
        self._indicators["bb_upper"] = self._safe_indicator_wrapper(
            lambda df: self._get_bollinger_band(df, "upper"), "bb_upper"
        )
        self._indicators["bb_lower"] = self._safe_indicator_wrapper(
            lambda df: self._get_bollinger_band(df, "lower"), "bb_lower"
        )
        self._indicators["bb_middle"] = self._safe_indicator_wrapper(
            lambda df: self._get_bollinger_band(df, "middle"), "bb_middle"
        )
        
        # ATR (Average True Range)
        self._indicators["atr_14"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.atr(df['high'], df['low'], df['close'], length=14), "atr_14"), "atr_14"
        )
        
        # Volume Indicators
        self._indicators["volume_sma"] = self._safe_indicator_wrapper(
            lambda df: self._safe_series_wrap(ta.sma(df.get('volume', df.get('vol_base', pd.Series())), length=20), "volume_sma"), "volume_sma"
        )
        
        # Support/Resistance
        self._indicators["pivot_points"] = self._safe_indicator_wrapper(
            lambda df: self._calculate_pivot_points(df), "pivot_points"
        )
    
    def _get_bollinger_band(self, df: pd.DataFrame, band_type: str) -> pd.DataFrame:
        """Extract specific Bollinger Band line"""
        try:
            bbands = ta.bbands(df['close'], length=20)
            if bbands is None:
                return pd.DataFrame({f"bb_{band_type}": pd.Series(dtype=float)})
            
            if band_type == "upper":
                col = [col for col in bbands.columns if "BBU" in col]
            elif band_type == "lower":
                col = [col for col in bbands.columns if "BBL" in col]
            else:  # middle
                col = [col for col in bbands.columns if "BBM" in col]
            
            if col:
                return self._safe_series_wrap(bbands[col[0]], f"bb_{band_type}")
            
            return pd.DataFrame({f"bb_{band_type}": pd.Series(dtype=float)})
            
        except Exception:
            return pd.DataFrame({f"bb_{band_type}": pd.Series(dtype=float)})
    
    def _calculate_pivot_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate pivot points from OHLC data"""
        try:
            if len(df) < 1:
                return pd.DataFrame()
            
            # Standard pivot point calculation
            pivot = (df['high'] + df['low'] + df['close']) / 3
            support1 = 2 * pivot - df['high']
            resistance1 = 2 * pivot - df['low']
            support2 = pivot - (df['high'] - df['low'])
            resistance2 = pivot + (df['high'] - df['low'])
            
            return pd.DataFrame({
                'pivot': pivot,
                'support1': support1,
                'resistance1': resistance1,
                'support2': support2,
                'resistance2': resistance2
            })
        except Exception:
            return pd.DataFrame()
    
    def get_available_indicators(self) -> List[str]:
        """
        Get list of all available indicators
        
        Returns:
            List of indicator names
        """
        return sorted(self._indicators.keys())
    
    def register_indicator(self, name: str, func: Callable[[pd.DataFrame], pd.DataFrame]):
        """
        Register a custom indicator function
        
        Args:
            name: Name of the indicator
            func: Function that takes DataFrame and returns DataFrame with indicator data
        """
        self._indicators[name] = self._safe_indicator_wrapper(func, name)
        logger.info(f"Registered custom indicator: {name}")
    
    def calculate_indicator(self, df: pd.DataFrame, indicator_name: str, **kwargs) -> pd.DataFrame:
        """
        Calculate a specific indicator
        
        Args:
            df: OHLCV DataFrame
            indicator_name: Name of the indicator to calculate
            **kwargs: Additional parameters (currently not used, reserved for future)
            
        Returns:
            DataFrame with indicator data
            
        Raises:
            ValueError: If indicator is not available
        """
        if indicator_name not in self._indicators:
            available = ", ".join(self.get_available_indicators())
            raise ValueError(f"Indicator '{indicator_name}' not available. Available indicators: {available}")
        
        try:
            return self._indicators[indicator_name](df)
        except Exception as e:
            logger.error(f"Failed to calculate indicator {indicator_name}: {e}")
            return pd.DataFrame({indicator_name: pd.Series(dtype=float)})
    
    def calculate_multiple(self, df: pd.DataFrame, indicator_names: List[str]) -> pd.DataFrame:
        """
        Calculate multiple indicators at once
        
        Args:
            df: OHLCV DataFrame
            indicator_names: List of indicator names to calculate
            
        Returns:
            DataFrame with all requested indicators
        """
        if not indicator_names:
            return pd.DataFrame()
        
        results = []
        
        for indicator_name in indicator_names:
            try:
                indicator_df = self.calculate_indicator(df, indicator_name)
                results.append(indicator_df)
            except Exception as e:
                logger.warning(f"Failed to calculate {indicator_name}: {e}")
                # Add empty column to maintain structure
                results.append(pd.DataFrame({indicator_name: pd.Series(dtype=float)}))
        
        # Combine all results
        if results:
            combined = pd.concat(results, axis=1, join='outer')
            return combined
        
        return pd.DataFrame()
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all available indicators
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with all indicators
        """
        return self.calculate_multiple(df, self.get_available_indicators())
    
    def get_indicator_info(self, indicator_name: str) -> Dict[str, Any]:
        """
        Get information about a specific indicator
        
        Args:
            indicator_name: Name of the indicator
            
        Returns:
            Dict with indicator metadata
        """
        if indicator_name not in self._indicators:
            return {}
        
        # Basic indicator categorization
        category = "unknown"
        if any(x in indicator_name for x in ["sma", "ema", "ma"]):
            category = "moving_average"
        elif any(x in indicator_name for x in ["rsi", "stoch", "macd"]):
            category = "momentum"
        elif any(x in indicator_name for x in ["bb", "atr"]):
            category = "volatility"
        elif any(x in indicator_name for x in ["volume"]):
            category = "volume"
        elif any(x in indicator_name for x in ["pivot"]):
            category = "support_resistance"
        
        return {
            "name": indicator_name,
            "category": category,
            "available": True,
            "description": f"{indicator_name.replace('_', ' ').title()} indicator"
        }
    
    def get_all_indicators_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available indicators
        
        Returns:
            Dict with all indicators metadata
        """
        return {
            name: self.get_indicator_info(name) 
            for name in self.get_available_indicators()
        }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for Agent Framework
        
        Returns:
            Dict with tool metadata and available methods
        """
        return {
            "name": "TechnicalIndicatorService",
            "description": "Technical analysis indicator calculation service",
            "methods": {
                "calculate_indicator": {
                    "description": "Calculate a specific technical indicator",
                    "parameters": {
                        "df": {"type": "dataframe", "required": True, "description": "OHLCV DataFrame"},
                        "indicator_name": {"type": "string", "required": True, "description": "Name of the indicator"}
                    }
                },
                "calculate_multiple": {
                    "description": "Calculate multiple indicators at once",
                    "parameters": {
                        "df": {"type": "dataframe", "required": True, "description": "OHLCV DataFrame"},
                        "indicator_names": {"type": "array", "required": True, "description": "List of indicator names"}
                    }
                },
                "get_available_indicators": {
                    "description": "Get list of available indicators",
                    "parameters": {}
                }
            },
            "available_indicators": self.get_available_indicators()
        }


# Singleton instance for global access
_indicator_service_instance: Optional[TechnicalIndicatorService] = None

def get_indicator_service() -> TechnicalIndicatorService:
    """Get global TechnicalIndicatorService instance"""
    global _indicator_service_instance
    if _indicator_service_instance is None:
        _indicator_service_instance = TechnicalIndicatorService()
    return _indicator_service_instance


# Backward compatibility wrapper functions
def available() -> List[str]:
    """Backward compatibility wrapper for available indicators"""
    service = get_indicator_service()
    return service.get_available_indicators()

def compute(df: pd.DataFrame, names: List[str]) -> pd.DataFrame:
    """Backward compatibility wrapper for compute function"""
    service = get_indicator_service()
    return service.calculate_multiple(df, names)
