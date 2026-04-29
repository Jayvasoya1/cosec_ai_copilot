# """
# Enroll-Options Intent Handler - Handles enrollment configuration intents
# """

# from typing import Dict, Any
# from app.logger import logger
# from app.exceptions import ValidationError


# def handle_enroll_options_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Handle enroll-options related intents
    
#     Supported intents:
#     - get_enroll_options: Get current enrollment configuration
#     - set_enroll_options: Set enrollment configuration
#     - get_default_enroll_options: Get default settings
#     - set_default_enroll_options: Set default settings
#     """
    
#     # Map intent names to actions
#     INTENT_TO_ACTION = {
#         "get_enroll_options": "get",
#         "set_enroll_options": "set",
#         "get_default_enroll_options": "getdefault",
#         "set_default_enroll_options": "setdefault",
#     }
    
#     # Map intent parameter names to API field names
#     PARAM_MAPPING = {
#         "finger_count": "enroll-finger-count",
#         "palm_count": "enroll-palm-count",
#         "card_count": "enroll-card-count",
#         "on_device": "enroll-on-device",
#         "using": "enroll-using",
#         "mode": "enroll-mode",
#         "id_format": "format",
#     }

#     logger.info(f"jay-{intent}")
    
#     logger.debug(f"Handling enroll-options intent: {intent}")
    
#     # Get action from intent
#     action = INTENT_TO_ACTION.get(intent)
#     logger.info(f"ali-{action}")
#     if not action:
#         raise ValidationError(f"Unknown enroll-options intent: {intent}")
    
#     logger.debug(f"Mapped intent '{intent}' to action '{action}'")
    
#     # Transform parameters
#     transformed_params = {}
    
#     for intent_param, api_param in PARAM_MAPPING.items():
#         if intent_param in params:
#             transformed_params[api_param] = params[intent_param]
    
#     # Add action parameter
#     transformed_params["action"] = action
    
#     logger.debug(f"Transformed parameters: {transformed_params}")
    
#     return {
#             "group": "users",
#             "params": {
#                 "action": action,
#                 **transformed_params
#             }
#         }
"""
Enroll-Options Intent Handler - Handles enrollment configuration intents
Validates parameters and routes to executor
"""

from typing import Dict, Any
from app.core.param_resolver import resolve_enroll_options_params
from app.exceptions import ValidationError
from app.logger import logger


def handle_enroll_options_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle enroll-options related intents
    
    Supported intents:
    - get_enroll_options
    - set_enroll_options
    - get_default_enroll_options
    - set_default_enroll_options
    
    Args:
        intent: Intent type
        params: Parameters from LLM parsing
        
    Returns:
        Dict with group, params, or need_input/error
    """
    
    logger.debug(f"Handling enroll-options intent: {intent} with params: {params}")
    
    try:
        # Map intent to API action
        intent_to_action = {
            "get_enroll_options": "get",
            "set_enroll_options": "set",
            "get_default_enroll_options": "getdefault",
            "set_default_enroll_options": "setdefault",
        }
        
        if intent not in intent_to_action:
            raise ValidationError(
                f"Unknown enroll-options intent: {intent}",
                {"intent": intent}
            )
        
        action = intent_to_action[intent]
        logger.debug(f"Mapped intent '{intent}' to action '{action}'")
        
        # Map LLM parameter names to API parameter names
        param_mapping = {
            "finger_count": "enroll-finger-count",
            "palm_count": "enroll-palm-count",
            "card_count": "enroll-card-count",
            "on_device": "enroll-on-device",
            "using": "enroll-using",
            "mode": "enroll-mode",
            "id_format": "format",
        }
        
        # Transform parameters
        mapped_params = {}
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            mapped_params[api_key] = value
        
        logger.debug(f"Mapped parameters: {mapped_params}")
        
        # Resolve missing parameters using schema and memory
        is_resolved, result = resolve_enroll_options_params(action, mapped_params)
        
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
            "group": "enroll-options",
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
        logger.error(f"Error handling enroll-options intent: {str(e)}")
        return {
            "error": f"Failed to process enroll-options intent: {str(e)}",
            "code": "ENROLL_OPTIONS_HANDLER_ERROR",
            "intent": intent
        }