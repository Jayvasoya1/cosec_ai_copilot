from typing import Dict, Any
from app.core.param_resolver import resolve_params_for_group
from app.exceptions import ValidationError
from app.logger import logger


def handle_panel_door_list_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug(f"Handling panel-door-list intent: {intent} with params: {params}")

    try:
        intent_to_action = {
            "get_panel_door_list": "get",
        }

        if intent not in intent_to_action:
            raise ValidationError(
                f"Unknown panel-door-list intent: {intent}",
                {"intent": intent}
            )

        action = intent_to_action[intent]

        # Map LLM-friendly names → API parameter names
        param_mapping = {
            # Keep pdid same, but allow flexibility if LLM changes naming
            "panel_door_id": "pdid",
        }

        mapped_params = {param_mapping.get(k, k): v for k, v in params.items()}
        logger.debug(f"Mapped parameters: {mapped_params}")

        is_resolved, result = resolve_params_for_group(
            "panel-door-list",
            action,
            mapped_params
        )

        if not is_resolved:
            logger.info(f"Need user input: {result.get('missing')}")
            return {
                "need_input": True,
                "missing": result.get("missing", []),
                "partial": result.get("partial", {}),
            }

        logger.info(f"All parameters resolved for {intent}")
        return {
            "group": "panel-door-list",
            "params": {"action": action, **result.get("resolved", {})},
        }

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "error": str(e),
            "code": e.code,
            "details": e.details
        }

    except Exception as e:
        logger.error(f"Error handling panel-door-list intent: {str(e)}")
        return {
            "error": f"Failed to process panel-door-list intent: {str(e)}",
            "code": "PANEL_DOOR_LIST_HANDLER_ERROR"
        }