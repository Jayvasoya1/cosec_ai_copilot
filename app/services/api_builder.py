"""
API Builder - Constructs API URLs from group and parameters
Validates parameters against schema before building
"""

from typing import Dict
from urllib.parse import urlencode, quote
from app.exceptions import APIBuildError
from app.schemas.registry import schema_registry
from app.logger import logger
import app.config as config

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
        base = f"/192.168.103.184/device.cgi/{group}"
        
        # Add hardcoded parameters for specific actions
        params_to_encode = params.copy()
        
        # For "set user" action, add hardcoded parameters
        if group == "users" and params.get("action") == "set":
            # ref-user-id should reference the user-id being set
            if "user-id" in params_to_encode:
                params_to_encode["ref-user-id"] = params_to_encode["user-id"]
            # user-active defaults to 1 (active)
            if "user-active" not in params_to_encode:
                params_to_encode["user-active"] = "1"
        
        if group == "panel-door-config" and params.get("action") == "set":
            # ref-user-id should reference the user-id being set
            logger.info(f"Building URL for panel-door-config set with params: {params_to_encode}")
            if "door-name" not in params_to_encode:
                params_to_encode["door-name"] = params_to_encode["door-type"] + str(config.PDID + 1)
            if "door-type" in params_to_encode:
                if params_to_encode["door-type"].lower() == "argo face":
                     params_to_encode["door-type"] = "21"
                elif params_to_encode["door-type"].lower() == "vega":
                     params_to_encode["door-type"] = "9"
            params_to_encode["communication-type"] = "ethernet"
            params_to_encode["pdid"] = config.PDID + 1
            config.PDID += 1
            # user-active defaults to 1 (active)
            params_to_encode["active"] = "1"
        
        # URL encode parameters
        query_parts = []
        for key, value in params_to_encode.items():
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