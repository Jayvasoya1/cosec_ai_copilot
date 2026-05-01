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
from app.services.device_api import call_device_api

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
            logger.info(f"Building URL for panel-door-config set with params: {params_to_encode}")

            # Normalize door-type string to numeric device code (if provided)
            if "door-type" in params_to_encode:
                dtype = str(params_to_encode["door-type"]).lower()
                if dtype == "argo face":
                    params_to_encode["door-type"] = "21"
                elif dtype == "vega":
                    params_to_encode["door-type"] = "9"

            # Auto-generate door-name only when not provided AND door-type is known
            if "door-name" not in params_to_encode and "door-type" in params_to_encode:
                params_to_encode["door-name"] = (
                    params_to_encode["door-type"] + str(params_to_encode.get("pdid", ""))
                )

            # Apply defaults only for fields not already specified by the user
            if "communication-type" not in params_to_encode:
                params_to_encode["communication-type"] = "0"
            if "active" not in params_to_encode:
                params_to_encode["active"] = "1"

            # Respect user-provided pdid; fall back to auto-counter only if absent
            if "pdid" not in params_to_encode:
                params_to_encode["pdid"] = config.PDID + 1
                config.PDID += 1
                
        if group == "enrolluser" and params.get("action") == "enroll":
            logger.info(f"Building URL for enrolluser enroll with params: {params_to_encode}")


            params_to_encode["face-count"] = "1"


            if not params_to_encode["type"]:
                params_to_encode["type"] = "7"
                logger.info("Defaulting to 7")

        if group == "enrolluser" and params.get("action") == "enroll" and params_to_encode.get("type") == "7":
            resp = call_device_api( f"/192.168.103.184/device.cgi/users?action=set&user-id={params_to_encode['user-id']}&enable-fr=1")
            resp = call_device_api(f"/192.168.103.184/device.cgi/fr-settings?action=set&pdid={params_to_encode['pdid']}&enable=1")
        
        # URL encode parameters
        query_parts = []
        for key, value in params_to_encode.items():
            # Keep colons safe for MAC addresses (e.g., 00:11:22:33:44:55)
            encoded_value = quote(str(value), safe=':')
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