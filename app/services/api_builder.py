"""
API Builder - Constructs API URLs from group and parameters
Validates parameters against schema before building
"""

from typing import Dict
from urllib.parse import urlencode, quote
from app.exceptions import APIBuildError
from app.schemas.registry import schema_registry
from app.logger import logger


def build_url(group: str, params: Dict) -> str:
    """
    Build API URL for COSEC device
    
    Args:
        group: API group name (e.g., "users")
        params: Parameters dict (must include 'action')
        
    Returns:
        URL string (e.g., "/device.cgi/users?action=set&user-id=101")
        
    Raises:
        APIBuildError: If URL building fails
    """
    
    if not group:
        raise APIBuildError("Group name is required")
    
    # if not params:
    #     raise APIBuildError("Parameters must not be empty")
    
    # if "action" not in params:
    #     raise APIBuildError("'action' parameter is required", params)
    
    logger.debug(f"Building URL for group: {group}, params: {params}")
    
    try:
        # Extract action from params
        action = params.get("action")
        
        # Create a copy of params without action for validation
        params_without_action = {k: v for k, v in params.items() if k != "action"}
        
        # Validate against schema
        schema = schema_registry.get(group)
        
        # Validate parameters against schema (without action)
        is_valid, result = schema.validate_parameters(action, params_without_action)
        
        if not is_valid:
            raise APIBuildError(
                f"Invalid parameters for {group}.{action}: {result.get('missing')}",
                params
            )
        
        # Build base URL
        base = f"/device.cgi/{group}"
        
        # URL encode parameters
        query_parts = []
        for key, value in params.items():
            encoded_value = quote(str(value), safe='')
            query_parts.append(f"{key}={encoded_value}")
        
        query_string = "&".join(query_parts)
        full_url = f"{base}?{query_string}"
        
        logger.debug(f"Built URL: {full_url}")
        return full_url
        
    except APIBuildError:
        raise
        
    except Exception as e:
        logger.error(f"Error building URL: {str(e)}")
        raise APIBuildError(
            f"Failed to build URL: {str(e)}",
            params
        )


def encode_param(value) -> str:
    """Safely encode parameter value for URL"""
    return quote(str(value), safe='=&')