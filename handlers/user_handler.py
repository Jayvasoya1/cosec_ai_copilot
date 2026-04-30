"""
User Handler - Handles all user-related intents (add, delete, update)
Validates parameters and routes to executor
"""

from typing import Dict
from app.core.param_resolver import resolve_user_params
from app.exceptions import ValidationError
from app.logger import logger


def handle_user_intent(intent: str, params: Dict) -> Dict:
    """
    Handle user-related intents
    
    Supported intents:
    - add_user: Create new user
    - delete_user: Delete existing user
    - update_user: Update user information
    
    Args:
        intent: Intent type (add_user, delete_user, update_user)
        params: Parameters from LLM parsing
        
    Returns:
        Dict with group, params, or need_input/error
    """
    
    logger.debug(f"Handling user intent: {intent} with params: {params}")
    
    try:
        # Map intent to API action
        intent_to_action = {
            "add_user":    "set",
            "create_user": "set",
            "update_user": "set",
            "delete_user": "delete",
            "remove_user": "delete",
            "get_user":    "get",
        }
        
        if intent not in intent_to_action:
            raise ValidationError(
                f"Unknown user intent: {intent}",
                {"intent": intent}
            )
        
        action = intent_to_action[intent]
        logger.debug(f"Mapped intent '{intent}' to action '{action}'")
        
        # Map LLM parameter names to API parameter names
        param_mapping = {
            "user_id": "user-id",
            "ref_user_id": "ref-user-id",
            "user_name": "name",
            "name": "name",
            "user_pin": "user-pin",
            "bypass_finger": "by-pass-finger",
            "bypass_palm": "by-pass-palm",
            "bypass_face": "by-pass-face",
        }
        
        # Transform parameters
        mapped_params = {}
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            mapped_params[api_key] = value
        
        logger.debug(f"Mapped parameters: {mapped_params}")
        
        # Resolve missing parameters using schema and memory
        is_resolved, result = resolve_user_params(action, mapped_params)
        
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
            "group": "users",
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
        logger.error(f"Error handling user intent: {str(e)}")
        return {
            "error": f"Failed to process user intent: {str(e)}",
            "code": "USER_HANDLER_ERROR",
            "intent": intent
        }