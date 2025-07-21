"""
Agent Framework Test Routes
Neue Endpoints für das klassenbasierte System
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

from ..core.agent_framework import get_agent_tool_registry, get_agent_service_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent Framework"])


@router.get("/tools")
async def get_available_tools(category: Optional[str] = Query(None, description="Tool category filter")):
    """
    Get list of available agent tools
    
    Args:
        category: Optional category filter (market_data, technical_analysis, etc.)
        
    Returns:
        Dict with available tools and their metadata
    """
    try:
        registry = get_agent_tool_registry()
        
        tools = registry.get_available_tools(category)
        definitions = registry.get_tool_definitions(category)
        stats = registry.get_registry_stats()
        
        return {
            "status": "success",
            "data": {
                "tools": tools,
                "definitions": definitions,
                "stats": stats,
                "category_filter": category
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting agent tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools/{tool_name}")
async def get_tool_definition(tool_name: str):
    """
    Get detailed definition for a specific tool
    
    Args:
        tool_name: Name of the tool
        
    Returns:
        Dict with tool definition and methods
    """
    try:
        registry = get_agent_tool_registry()
        tool = registry.get_tool(tool_name)
        
        if not tool:
            available = ", ".join(registry.get_available_tools())
            raise HTTPException(
                status_code=404, 
                detail=f"Tool '{tool_name}' not found. Available tools: {available}"
            )
        
        definition = tool.get_tool_definition()
        methods = tool.get_available_methods()
        
        # Get method signatures
        method_signatures = {}
        for method in methods:
            try:
                method_signatures[method] = tool.get_method_signature(method)
            except Exception as e:
                logger.warning(f"Could not get signature for {method}: {e}")
        
        return {
            "status": "success",
            "data": {
                "tool_name": tool_name,
                "definition": definition,
                "methods": methods,
                "method_signatures": method_signatures
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool definition for {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/{tool_name}/{method_name}")
async def execute_tool_method(
    tool_name: str, 
    method_name: str, 
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Execute a method on a specific tool
    
    Args:
        tool_name: Name of the tool
        method_name: Name of the method to execute
        parameters: Method parameters as JSON
        
    Returns:
        Dict with method execution result
    """
    try:
        if parameters is None:
            parameters = {}
        
        registry = get_agent_tool_registry()
        result = await registry.execute_tool_method(tool_name, method_name, **parameters)
        
        return {
            "status": "success",
            "data": {
                "tool_name": tool_name,
                "method_name": method_name,
                "parameters": parameters,
                "result": result
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing {tool_name}.{method_name}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/registry/stats")
async def get_registry_stats():
    """
    Get Agent Tool Registry statistics
    
    Returns:
        Dict with registry statistics
    """
    try:
        registry = get_agent_tool_registry()
        stats = registry.get_registry_stats()
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting registry stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/export")
async def export_tool_schemas():
    """
    Export all tool schemas for external agent frameworks
    
    Returns:
        Complete tool schemas for agent integration
    """
    try:
        registry = get_agent_tool_registry()
        schemas = registry.export_tool_schemas()
        
        return {
            "status": "success",
            "data": schemas
        }
        
    except Exception as e:
        logger.error(f"Error exporting tool schemas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/bitget")
async def test_bitget_client(
    symbol: str = Query("BTCUSDT", description="Trading symbol"),
    granularity: str = Query("1h", description="Time granularity")
):
    """
    Test the new BitgetAPIClient through Agent Framework
    
    Args:
        symbol: Trading symbol
        granularity: Time granularity
        
    Returns:
        Test results comparing old and new implementations
    """
    try:
        registry = get_agent_tool_registry()
        
        # Test new class-based implementation
        new_result = await registry.execute_tool_method(
            "BitgetAPIClient", 
            "get_candles", 
            symbol=symbol, 
            granularity=granularity, 
            limit=10
        )
        
        # Test old functional implementation for comparison
        from ..services.bitget import candles as old_candles
        old_result = await old_candles(symbol, granularity, limit=10)
        
        # Compare results
        comparison = {
            "new_result_type": str(type(new_result)),
            "old_result_type": str(type(old_result)),
            "new_result_shape": getattr(new_result, 'shape', None),
            "old_result_shape": getattr(old_result, 'shape', None),
            "results_equal": str(new_result.equals(old_result)) if hasattr(new_result, 'equals') else "N/A"
        }
        
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "granularity": granularity,
                "new_result": new_result.to_dict('records') if hasattr(new_result, 'to_dict') else str(new_result)[:500],
                "old_result": old_result.to_dict('records') if hasattr(old_result, 'to_dict') else str(old_result)[:500],
                "comparison": comparison
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing Bitget client: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/indicators")
async def test_indicator_service(
    symbol: str = Query("BTCUSDT", description="Trading symbol"),
    indicators: List[str] = Query(["sma_50", "rsi_14"], description="Indicators to test")
):
    """
    Test the new TechnicalIndicatorService through Agent Framework
    
    Args:
        symbol: Trading symbol for getting candle data
        indicators: List of indicators to calculate
        
    Returns:
        Test results for indicator calculations
    """
    try:
        registry = get_agent_tool_registry()
        
        # First get candle data
        candle_data = await registry.execute_tool_method(
            "BitgetAPIClient", 
            "get_candles", 
            symbol=symbol, 
            granularity="1h", 
            limit=100
        )
        
        # Test new indicator service
        indicator_results = await registry.execute_tool_method(
            "TechnicalIndicatorService",
            "calculate_multiple",
            df=candle_data,
            indicator_names=indicators
        )
        
        # Get available indicators
        available_indicators = await registry.execute_tool_method(
            "TechnicalIndicatorService",
            "get_available_indicators"
        )
        
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "indicators_requested": indicators,
                "available_indicators": available_indicators,
                "candle_data_shape": getattr(candle_data, 'shape', None),
                "indicator_results": indicator_results.to_dict('records')[:5] if hasattr(indicator_results, 'to_dict') else str(indicator_results)[:500],
                "indicator_columns": list(indicator_results.columns) if hasattr(indicator_results, 'columns') else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing indicator service: {e}")
        raise HTTPException(status_code=500, detail=str(e))
