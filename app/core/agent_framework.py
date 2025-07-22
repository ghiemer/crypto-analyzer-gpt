"""
Agent Framework Base Classes and Registry
Vorbereitung für die Integration von Agent Tools
"""

import logging
from typing import Dict, Any, List, Optional, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import inspect
import asyncio

logger = logging.getLogger(__name__)


class ToolParameterType(str, Enum):
    """Supported parameter types for agent tools"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    DATAFRAME = "dataframe"
    ANY = "any"


@dataclass
class ToolParameter:
    """Tool parameter definition"""
    name: str
    type: ToolParameterType
    required: bool = True
    description: str = ""
    default: Any = None
    choices: Optional[List[Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        param_dict = {
            "type": self.type.value,
            "required": self.required,
            "description": self.description
        }
        
        if self.default is not None:
            param_dict["default"] = self.default
        
        if self.choices:
            param_dict["choices"] = self.choices
        
        return param_dict


@dataclass
class ToolMethod:
    """Tool method definition"""
    name: str
    description: str
    parameters: List[ToolParameter]
    async_method: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                param.name: param.to_dict() 
                for param in self.parameters
            },
            "async": self.async_method
        }


class BaseAgentTool(ABC):
    """
    Base class for Agent Framework Tools
    
    All service classes that should be available to agents must inherit from this class
    """
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.tool.{name}")
    
    @abstractmethod
    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get tool definition for Agent Framework
        
        Returns:
            Dict with tool metadata and available methods
        """
        pass
    
    @abstractmethod
    def get_available_methods(self) -> List[str]:
        """
        Get list of available methods for this tool
        
        Returns:
            List of method names
        """
        pass
    
    async def execute_method(self, method_name: str, **kwargs) -> Any:
        """
        Execute a specific method with parameters
        
        Args:
            method_name: Name of the method to execute
            **kwargs: Method parameters
            
        Returns:
            Method result
            
        Raises:
            ValueError: If method is not available
            Exception: If method execution fails
        """
        if method_name not in self.get_available_methods():
            available = ", ".join(self.get_available_methods())
            raise ValueError(f"Method '{method_name}' not available. Available methods: {available}")
        
        method = getattr(self, method_name, None)
        if method is None:
            raise ValueError(f"Method '{method_name}' not implemented")
        
        try:
            # Check if method is async
            if inspect.iscoroutinefunction(method):
                result = await method(**kwargs)
            else:
                result = method(**kwargs)
            
            self.logger.debug(f"Method {method_name} executed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Method {method_name} execution failed: {e}")
            raise
    
    def get_method_signature(self, method_name: str) -> Dict[str, Any]:
        """
        Get method signature information
        
        Args:
            method_name: Name of the method
            
        Returns:
            Dict with method signature details
        """
        method = getattr(self, method_name, None)
        if method is None:
            return {}
        
        sig = inspect.signature(method)
        return {
            "name": method_name,
            "parameters": {
                name: {
                    "type": param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
                for name, param in sig.parameters.items()
                if name != "self"
            },
            "async": inspect.iscoroutinefunction(method)
        }


class AgentToolRegistry:
    """
    Registry for managing Agent Framework Tools
    
    Provides centralized management of all available tools for agents
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseAgentTool] = {}
        self.categories: Dict[str, List[str]] = {
            "market_data": [],
            "technical_analysis": [],
            "alerts": [],
            "cache": [],
            "database": [],
            "communication": [],
            "monitoring": [],
            "other": []
        }
    
    def register_tool(self, tool: BaseAgentTool, category: str = "other"):
        """
        Register a tool in the registry
        
        Args:
            tool: Tool instance to register
            category: Tool category for organization
        """
        if not isinstance(tool, BaseAgentTool):
            raise TypeError("Tool must inherit from BaseAgentTool")
        
        self.tools[tool.name] = tool
        
        if category not in self.categories:
            self.categories[category] = []
        
        if tool.name not in self.categories[category]:
            self.categories[category].append(tool.name)
        
        logger.info(f"Registered agent tool: {tool.name} in category {category}")
    
    def unregister_tool(self, tool_name: str):
        """
        Unregister a tool from the registry
        
        Args:
            tool_name: Name of the tool to unregister
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            
            # Remove from all categories
            for category_tools in self.categories.values():
                if tool_name in category_tools:
                    category_tools.remove(tool_name)
            
            logger.info(f"Unregistered agent tool: {tool_name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseAgentTool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    def get_available_tools(self, category: Optional[str] = None) -> List[str]:
        """
        Get list of available tools
        
        Args:
            category: Optional category filter
            
        Returns:
            List of tool names
        """
        if category:
            return self.categories.get(category, [])
        return list(self.tools.keys())
    
    def get_tool_definitions(self, category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get tool definitions for all tools or specific category
        
        Args:
            category: Optional category filter
            
        Returns:
            Dict mapping tool names to their definitions
        """
        tool_names = self.get_available_tools(category)
        
        definitions = {}
        for tool_name in tool_names:
            tool = self.tools.get(tool_name)
            if tool:
                definitions[tool_name] = tool.get_tool_definition()
        
        return definitions
    
    async def execute_tool_method(self, tool_name: str, method_name: str, **kwargs) -> Any:
        """
        Execute a method on a specific tool
        
        Args:
            tool_name: Name of the tool
            method_name: Name of the method
            **kwargs: Method parameters
            
        Returns:
            Method result
            
        Raises:
            ValueError: If tool or method is not available
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            available = ", ".join(self.get_available_tools())
            raise ValueError(f"Tool '{tool_name}' not available. Available tools: {available}")
        
        return await tool.execute_method(method_name, **kwargs)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics
        
        Returns:
            Dict with registry statistics
        """
        stats = {
            "total_tools": len(self.tools),
            "categories": {
                category: len(tools) 
                for category, tools in self.categories.items()
                if tools
            },
            "tools_by_category": dict(self.categories)
        }
        
        return stats
    
    def export_tool_schemas(self) -> Dict[str, Any]:
        """
        Export all tool schemas for external agent frameworks
        
        Returns:
            Dict with complete tool schemas
        """
        return {
            "registry_info": {
                "total_tools": len(self.tools),
                "categories": list(self.categories.keys()),
                "version": "1.0.0"
            },
            "tools": self.get_tool_definitions()
        }


# Global registry instance
_agent_tool_registry: Optional[AgentToolRegistry] = None

def get_agent_tool_registry() -> AgentToolRegistry:
    """Get global AgentToolRegistry instance"""
    global _agent_tool_registry
    if _agent_tool_registry is None:
        _agent_tool_registry = AgentToolRegistry()
    return _agent_tool_registry


class AgentServiceManager:
    """
    Manager for Agent Framework Service integration
    
    Handles initialization and lifecycle of all agent tools
    """
    
    def __init__(self):
        self.registry = get_agent_tool_registry()
        self.initialized_tools: List[str] = []
        
    async def initialize_all_tools(self):
        """Initialize all registered agent tools"""
        logger.info("Initializing Agent Framework tools...")
        
        from ..services.bitget_client import get_bitget_client
        from ..core.indicators_service import get_indicator_service
        from ..services.feargreed_service import get_fear_greed_service
        from ..services.telegram_service import get_telegram_service
        from .settings import settings
        
        # Initialize and register tools
        try:
            # Market Data Tools
            bitget_client = get_bitget_client()
            if hasattr(bitget_client, 'get_tool_definition'):
                # Create adapter for BitgetAPIClient
                bitget_tool = BitgetAgentTool(bitget_client)
                self.registry.register_tool(bitget_tool, "market_data")
                self.initialized_tools.append("BitgetAPIClient")
            
            # Technical Analysis Tools
            indicator_service = get_indicator_service()
            if hasattr(indicator_service, 'get_tool_definition'):
                indicator_tool = IndicatorAgentTool(indicator_service)
                self.registry.register_tool(indicator_tool, "technical_analysis")
                self.initialized_tools.append("TechnicalIndicatorService")
            
            # Cache Tools - Only if cache is enabled
            if settings.CACHE_ENABLED:
                from ..core.cache_manager import get_cache_manager
                cache_manager = get_cache_manager()
                await cache_manager.initialize()
                if hasattr(cache_manager, 'get_tool_definition'):
                    cache_tool = CacheAgentTool(cache_manager)
                    self.registry.register_tool(cache_tool, "cache")
                    self.initialized_tools.append("CacheManager")
            
            # Fear & Greed Tools
            fear_greed_service = get_fear_greed_service()
            if hasattr(fear_greed_service, 'get_tool_definition'):
                fear_greed_tool = FearGreedAgentTool(fear_greed_service)
                self.registry.register_tool(fear_greed_tool, "market_data")
                self.initialized_tools.append("FearGreedIndexService")
            
            # Telegram Tools
            telegram_service = get_telegram_service()
            if hasattr(telegram_service, 'get_tool_definition'):
                telegram_tool = TelegramAgentTool(telegram_service)
                self.registry.register_tool(telegram_tool, "communication")
                self.initialized_tools.append("TelegramBotService")
            
            logger.info(f"Initialized {len(self.initialized_tools)} agent tools: {', '.join(self.initialized_tools)}")
            
        except Exception as e:
            logger.error(f"Error initializing agent tools: {e}")
    
    async def shutdown_all_tools(self):
        """Shutdown all initialized agent tools"""
        logger.info("Shutting down Agent Framework tools...")
        
        # Simple cleanup - just clear the list
        logger.info(f"Cleaned up {len(self.initialized_tools)} agent tools")
        self.initialized_tools.clear()


# Tool Adapters - Wrap existing services for Agent Framework

class BitgetAgentTool(BaseAgentTool):
    """Agent tool adapter for BitgetAPIClient"""
    
    def __init__(self, client):
        super().__init__("BitgetAPIClient")
        self.client = client
    
    def get_tool_definition(self) -> Dict[str, Any]:
        return self.client.get_tool_definition()
    
    def get_available_methods(self) -> List[str]:
        return ["get_candles", "get_orderbook", "get_funding_rate", "get_open_interest"]
    
    async def get_candles(self, **kwargs):
        return await self.client.get_candles(**kwargs)
    
    async def get_orderbook(self, **kwargs):
        return await self.client.get_orderbook(**kwargs)
    
    async def get_funding_rate(self, **kwargs):
        return await self.client.get_funding_rate(**kwargs)
    
    async def get_open_interest(self, **kwargs):
        return await self.client.get_open_interest(**kwargs)


class IndicatorAgentTool(BaseAgentTool):
    """Agent tool adapter for TechnicalIndicatorService"""
    
    def __init__(self, service):
        super().__init__("TechnicalIndicatorService")
        self.service = service
    
    def get_tool_definition(self) -> Dict[str, Any]:
        return self.service.get_tool_definition()
    
    def get_available_methods(self) -> List[str]:
        return ["calculate_indicator", "calculate_multiple", "get_available_indicators"]
    
    def calculate_indicator(self, **kwargs):
        return self.service.calculate_indicator(**kwargs)
    
    def calculate_multiple(self, **kwargs):
        return self.service.calculate_multiple(**kwargs)
    
    def get_available_indicators(self, **kwargs):
        return self.service.get_available_indicators()


class CacheAgentTool(BaseAgentTool):
    """Agent tool adapter for CacheManager"""
    
    def __init__(self, manager):
        super().__init__("CacheManager")
        self.manager = manager
    
    def get_tool_definition(self) -> Dict[str, Any]:
        return self.manager.get_tool_definition()
    
    def get_available_methods(self) -> List[str]:
        return ["get", "set", "delete", "get_stats"]
    
    async def get(self, **kwargs):
        return await self.manager.get(**kwargs)
    
    async def set(self, **kwargs):
        return await self.manager.set(**kwargs)
    
    async def delete(self, **kwargs):
        return await self.manager.delete(**kwargs)
    
    async def get_stats(self, **kwargs):
        return await self.manager.get_stats()


class FearGreedAgentTool(BaseAgentTool):
    """Agent tool adapter for FearGreedIndexService"""
    
    def __init__(self, service):
        super().__init__("FearGreedIndexService")
        self.service = service
    
    def get_tool_definition(self) -> Dict[str, Any]:
        return self.service.get_tool_definition()
    
    def get_available_methods(self) -> List[str]:
        return ["get_current_index", "get_historical_data", "get_market_sentiment_analysis"]
    
    async def get_current_index(self, **kwargs):
        return await self.service.get_current_index(**kwargs)
    
    async def get_historical_data(self, **kwargs):
        return await self.service.get_historical_data(**kwargs)
    
    async def get_market_sentiment_analysis(self, **kwargs):
        return await self.service.get_market_sentiment_analysis(**kwargs)


class TelegramAgentTool(BaseAgentTool):
    """Agent tool adapter for TelegramBotService"""
    
    def __init__(self, service):
        super().__init__("TelegramBotService")
        self.service = service
    
    def get_tool_definition(self) -> Dict[str, Any]:
        return self.service.get_tool_definition()
    
    def get_available_methods(self) -> List[str]:
        return ["send_message", "send_photo", "get_bot_info", "create_inline_keyboard"]
    
    async def send_message(self, **kwargs):
        return await self.service.send_message(**kwargs)
    
    async def send_photo(self, **kwargs):
        return await self.service.send_photo(**kwargs)
    
    async def get_bot_info(self, **kwargs):
        return await self.service.get_bot_info(**kwargs)
    
    def create_inline_keyboard(self, **kwargs):
        return self.service.create_inline_keyboard(**kwargs)


# Global service manager instance
_agent_service_manager: Optional[AgentServiceManager] = None

def get_agent_service_manager() -> AgentServiceManager:
    """Get global AgentServiceManager instance"""
    global _agent_service_manager
    if _agent_service_manager is None:
        _agent_service_manager = AgentServiceManager()
    return _agent_service_manager
