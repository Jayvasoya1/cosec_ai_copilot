



"""
Access Setting Handler - Handles access-setting related intents
Validates parameters and routes to executor
"""

from typing import Dict
from app.core.param_resolver import resolve_access_setting_params
from app.exceptions import ValidationError
from app.logger import logger


def handle_access_setting_intent(intent: str, params: Dict) -> Dict:
    """
    Handle access-setting related intents
    
    Supported intents:
    - get_access_setting: Get current access settings
    - set_access_setting: Set access settings
    - get_default_access_setting: Get default access settings
    - set_default_access_setting: Set default access settings
    
    Args:
        intent: Intent type
        params: Parameters from LLM parsing
        
    Returns:
        Dict with group, params, or need_input/error
    """
    
    logger.debug(f"Handling access-setting intent: {intent} with params: {params}")
    
    try:
        # Map intent to API action
        intent_to_action = {
            "get_access_setting": "get",
            "set_access_setting": "set",
            "get_default_access_setting": "getdefault",
            "set_default_access_setting": "setdefault"
        }
        
        if intent not in intent_to_action:
            raise ValidationError(
                f"Unknown access-setting intent: {intent}",
                {"intent": intent}
            )
        
        action = intent_to_action[intent]
        logger.debug(f"Mapped intent '{intent}' to action '{action}'")
        
        # Map LLM parameter names to API parameter names
        param_mapping = {
            "week_day": "week-day",
            "work_start_hh": "work-start-hh",
            "work_start_mm": "work-start-mm",
            "work_end_hh": "work-end-hh",
            "work_end_mm": "work-end-mm",
        }
        
        # Transform parameters
        mapped_params = {}
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            mapped_params[api_key] = value
        
        logger.debug(f"Mapped parameters: {mapped_params}")
        
        # Resolve missing parameters using schema and memory
        is_resolved, result = resolve_access_setting_params(action, mapped_params)
        
        if not is_resolved:
            # Need more input
            logger.info(f"Need user input: {result.get('missing')}")
            return {
                "need_input": True,
                "missing": result.get("missing", []),
                "partial": result.get("partial", {})
            }
        
        # All parameters resolved
        logger.info(f"All parameters resolved for {intent}")
        
        return {
            "group": "access-setting",
            "params": {
                "action": action,
                **result.get("resolved", {})
            }
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "error": str(e),
            "code": e.code,
            "details": e.details
        }
        
    except Exception as e:
        logger.error(f"Error handling access-setting intent: {str(e)}")
        return {
            "error": f"Failed to process access-setting intent: {str(e)}",
            "code": "ACCESS_SETTING_HANDLER_ERROR",
            "intent": intent
        }

