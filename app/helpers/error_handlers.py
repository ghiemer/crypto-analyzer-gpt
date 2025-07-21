"""
Error handling helpers for consistent error management across routes.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from ..core.errors import ApiError, BAD_ARGUMENT, UPSTREAM
from ..utils.data_formatters import format_error_response

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Helper class for consistent error handling across the application.
    Consolidates duplicate error handling patterns found in routes.
    """
    
    @staticmethod
    def handle_validation_error(error: Exception) -> HTTPException:
        """
        Handle validation errors and convert to appropriate HTTP exceptions.
        
        Args:
            error: Validation error
            
        Returns:
            HTTPException with appropriate status code and message
        """
        if isinstance(error, ApiError):
            return HTTPException(status_code=400, detail=str(error))
        else:
            logger.error(f"Validation error: {error}", exc_info=True)
            return HTTPException(status_code=400, detail="Invalid request parameters")
    
    @staticmethod
    def handle_upstream_error(error: Exception) -> HTTPException:
        """
        Handle upstream API errors and convert to appropriate HTTP exceptions.
        
        Args:
            error: Upstream error
            
        Returns:
            HTTPException with appropriate status code and message
        """
        if isinstance(error, ApiError):
            return HTTPException(status_code=502, detail=str(error))
        else:
            logger.error(f"Upstream error: {error}", exc_info=True)
            return HTTPException(status_code=502, detail="External service unavailable")
    
    @staticmethod
    def handle_generic_error(error: Exception, default_message: str = "Internal server error") -> HTTPException:
        """
        Handle generic errors and convert to HTTP exceptions.
        
        Args:
            error: Generic error
            default_message: Default error message
            
        Returns:
            HTTPException with 500 status code
        """
        logger.error(f"Generic error: {error}", exc_info=True)
        return HTTPException(status_code=500, detail=default_message)
    
    @staticmethod
    def create_error_response(
        error: Exception,
        default_status: int = 500,
        default_message: str = "Internal server error"
    ) -> JSONResponse:
        """
        Create a formatted JSON error response.
        
        Args:
            error: Exception that occurred
            default_status: Default HTTP status code
            default_message: Default error message
            
        Returns:
            JSONResponse with formatted error
        """
        if isinstance(error, HTTPException):
            status_code = error.status_code
            message = error.detail
        elif isinstance(error, ApiError):
            status_code = error.status_code
            message = str(error.detail)
        else:
            status_code = default_status
            message = default_message
            logger.error(f"Unhandled error: {error}", exc_info=True)
        
        return JSONResponse(
            status_code=status_code,
            content=format_error_response(message, str(type(error).__name__))
        )

def handle_api_errors(default_message: str = "Internal server error"):
    """
    Decorator for consistent API error handling in route functions.
    
    Args:
        default_message: Default error message for unhandled exceptions
        
    Usage:
        @handle_api_errors("Failed to fetch data")
        async def my_route():
            # Route logic here
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ApiError:
                # Re-raise API errors as-is (they're already HTTPExceptions)
                raise
            except HTTPException:
                # Re-raise other HTTP exceptions as-is
                raise
            except Exception as e:
                logger.error(f"Unhandled error in {func.__name__}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=default_message)
        
        return wrapper
    return decorator

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for the FastAPI application.
    
    Args:
        request: FastAPI request object
        exc: Exception that occurred
        
    Returns:
        JSONResponse with formatted error
    """
    logger.error(f"Global exception handler: {exc}", exc_info=True)
    
    return ErrorHandler.create_error_response(
        exc, 
        default_message="An unexpected error occurred"
    )

def setup_error_handlers(app):
    """
    Set up global error handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return JSONResponse(
            status_code=exc.status_code,
            content=format_error_response(str(exc.detail), str(type(exc).__name__))
        )
    
    @app.exception_handler(Exception)
    async def global_handler(request: Request, exc: Exception):
        return await global_exception_handler(request, exc)
