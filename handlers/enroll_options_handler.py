from typing import Dict, Any
from app.core.param_resolver import resolve_enroll_options_params
from app.exceptions import ValidationError
from app.logger import logger


def handle_enroll_options_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug(f"Handling enroll-options intent: {intent} with params: {params}")

    try:
        intent_to_action = {
            "get_enroll_options":         "get",
            "set_enroll_options":         "set",
            "get_default_enroll_options": "getdefault",
            "set_default_enroll_options": "setdefault",
        }

        if intent not in intent_to_action:
            raise ValidationError(f"Unknown enroll-options intent: {intent}", {"intent": intent})

        action = intent_to_action[intent]

        # LLM returns names with enroll_ prefix (enroll_finger_count, enroll_mode …)
        # Also accept short aliases the mock parser may use (finger_count, mode …)
        param_mapping = {
            "enroll_finger_count": "enroll-finger-count",
            "enroll_palm_count":   "enroll-palm-count",
            "enroll_card_count":   "enroll-card-count",
            "enroll_on_device":    "enroll-on-device",
            "enroll_using":        "enroll-using",
            "enroll_mode":         "enroll-mode",
            # short aliases
            "finger_count":        "enroll-finger-count",
            "palm_count":          "enroll-palm-count",
            "card_count":          "enroll-card-count",
            "on_device":           "enroll-on-device",
            "using":               "enroll-using",
            "mode":                "enroll-mode",
            "id_format":           "format",
        }

        mapped_params = {param_mapping.get(k, k): v for k, v in params.items()}
        logger.debug(f"Mapped parameters: {mapped_params}")

        is_resolved, result = resolve_enroll_options_params(action, mapped_params)

        if not is_resolved:
            logger.info(f"Need user input: {result.get('missing')}")
            return {
                "need_input": True,
                "missing":    result.get("missing", []),
                "partial":    result.get("partial", {}),
            }

        logger.info(f"All parameters resolved for {intent}")
        return {
            "group":  "enroll-options",
            "params": {"action": action, **result.get("resolved", {})},
        }

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {"error": str(e), "code": e.code, "details": e.details}

    except Exception as e:
        logger.error(f"Error handling enroll-options intent: {str(e)}")
        return {"error": f"Failed to process enroll-options intent: {str(e)}", "code": "ENROLL_OPTIONS_HANDLER_ERROR"}
