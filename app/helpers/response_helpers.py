"""
Response helper utilities for consistent API response formatting.
"""

from typing import Any, Optional, Dict, Union
from fastapi.responses import JSONResponse
from datetime import datetime

def create_success_response(
    data: Any, 
    message: str = "Success", 
    status_code: int = 200
) -> JSONResponse:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
        
    Returns:
        JSONResponse with standardized format
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    )

def create_error_response(
    message: str, 
    error_code: Optional[str] = None,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Optional error code
        status_code: HTTP status code
        details: Optional additional error details
        
    Returns:
        JSONResponse with standardized error format
    """
    content: Dict[str, Any] = {
        "status": "error",
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        content["error_code"] = error_code
    
    if details:
        content["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )

def create_paginated_response(
    data: list,
    page: int = 1,
    limit: int = 50,
    total_count: Optional[int] = None,
    message: str = "Success"
) -> JSONResponse:
    """
    Create a standardized paginated response.
    
    Args:
        data: List of data items
        page: Current page number
        limit: Items per page
        total_count: Total number of items (if known)
        message: Response message
        
    Returns:
        JSONResponse with paginated format
    """
    response_data = {
        "items": data,
        "page": page,
        "limit": limit,
        "count": len(data)
    }
    
    if total_count is not None:
        response_data["total_count"] = total_count
        response_data["total_pages"] = (total_count + limit - 1) // limit
        response_data["has_next"] = page * limit < total_count
        response_data["has_previous"] = page > 1
    
    return create_success_response(response_data, message)

class ResponseHelper:
    """
    Helper class for creating consistent API responses.
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "Success") -> dict:
        """Create success response data"""
        return {
            "status": "success",
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def error(message: str, error_code: Optional[str] = None) -> dict:
        """Create error response data"""
        response = {
            "status": "error",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        if error_code:
            response["error_code"] = error_code
        
        return response
    
    @staticmethod
    def validation_error(field: str, message: str) -> dict:
        """Create validation error response"""
        return ResponseHelper.error(
            message=f"Validation error: {message}",
            error_code="VALIDATION_ERROR"
        )
    
    @staticmethod
    def not_found(resource: str) -> dict:
        """Create not found error response"""
        return ResponseHelper.error(
            message=f"{resource} not found",
            error_code="NOT_FOUND"
        )
    
    @staticmethod
    def unauthorized(message: str = "Unauthorized access") -> dict:
        """Create unauthorized error response"""
        return ResponseHelper.error(
            message=message,
            error_code="UNAUTHORIZED"
        )
    
    @staticmethod
    def rate_limited(message: str = "Rate limit exceeded") -> dict:
        """Create rate limit error response"""
        return ResponseHelper.error(
            message=message,
            error_code="RATE_LIMITED"
        )
    
    @staticmethod
    def service_unavailable(service: str) -> dict:
        """Create service unavailable error response"""
        return ResponseHelper.error(
            message=f"{service} service is currently unavailable",
            error_code="SERVICE_UNAVAILABLE"
        )
    
    @staticmethod
    def wrap_data(data: Any, metadata: Optional[Dict[str, Any]] = None) -> dict:
        """
        Wrap data with optional metadata.
        
        Args:
            data: Main response data
            metadata: Optional metadata to include
            
        Returns:
            Dictionary with wrapped data
        """
        result = {"data": data}
        
        if metadata:
            result["metadata"] = metadata
        
        return result
