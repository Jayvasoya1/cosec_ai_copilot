from typing import Dict, Any
from app.core.param_resolver import resolve_params_for_group
from app.exceptions import ValidationError
from app.logger import logger


def handle_panel_details_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug(f"Handling panel-details intent: {intent} with params: {params}")

    try:
        intent_to_action = {
            "get_panel_details": "get",
        }

        if intent not in intent_to_action:
            raise ValidationError(f"Unknown panel-details intent: {intent}", {"intent": intent})

        action = intent_to_action[intent]

        # LLM returns underscore names → map to API hyphenated names
        # Filter flags: user/door/alarm/io-link are passed as presence flags (value=1)
        param_mapping = {
            "include_user":    "user",
            "include_door":    "door",
            "include_alarm":   "alarm",
            "include_io_link": "io-link",
            "io_link":         "io-link",
        }

        mapped_params = {param_mapping.get(k, k): v for k, v in params.items()}
        logger.debug(f"Mapped parameters: {mapped_params}")

        is_resolved, result = resolve_params_for_group("panel-details", action, mapped_params)

        if not is_resolved:
            logger.info(f"Need user input: {result.get('missing')}")
            return {
                "need_input": True,
                "missing":    result.get("missing", []),
                "partial":    result.get("partial", {}),
            }

        logger.info(f"All parameters resolved for {intent}")
        return {
            "group":  "panel-details",
            "params": {"action": action, **result.get("resolved", {})},
        }

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {"error": str(e), "code": e.code, "details": e.details}

    except Exception as e:
        logger.error(f"Error handling panel-details intent: {str(e)}")
        return {"error": f"Failed to process panel-details intent: {str(e)}", "code": "PANEL_DETAILS_HANDLER_ERROR"}
