"""
Enroll-Options Intent Handler - Handles enrollment configuration intents
"""

from typing import Dict, Any
from app.logger import logger
from app.exceptions import ValidationError


def handle_enroll_options_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle enroll-options related intents
    
    Supported intents:
    - get_enroll_options: Get current enrollment configuration
    - set_enroll_options: Set enrollment configuration
    - get_default_enroll_options: Get default settings
    - set_default_enroll_options: Set default settings
    """
    
    # Map intent names to actions
    INTENT_TO_ACTION = {
        "get_enroll_options": "get",
        "set_enroll_options": "set",
        "get_default_enroll_options": "getdefault",
        "set_default_enroll_options": "setdefault",
    }
    
    # Map intent parameter names to API field names
    PARAM_MAPPING = {
        "finger_count": "enroll-finger-count",
        "palm_count": "enroll-palm-count",
        "card_count": "enroll-card-count",
        "on_device": "enroll-on-device",
        "using": "enroll-using",
        "mode": "enroll-mode",
        "id_format": "format",
    }
    
    logger.debug(f"Handling enroll-options intent: {intent}")
    
    # Get action from intent
    action = INTENT_TO_ACTION.get(intent)
    if not action:
        raise ValidationError(f"Unknown enroll-options intent: {intent}")
    
    logger.debug(f"Mapped intent '{intent}' to action '{action}'")
    
    # Transform parameters
    transformed_params = {}
    
    for intent_param, api_param in PARAM_MAPPING.items():
        if intent_param in params:
            transformed_params[api_param] = params[intent_param]
    
    # Add action parameter
    transformed_params["action"] = action
    
    logger.debug(f"Transformed parameters: {transformed_params}")
    
    return {
        "group": "enroll-options",
        "action": action,
        **transformed_params
    }
