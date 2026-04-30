from typing import Dict, Any
from app.core.param_resolver import resolve_params_for_group
from app.exceptions import ValidationError
from app.logger import logger


def handle_command_intent(intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
    logger.debug(f"Handling command intent: {intent} with params: {params}")

    try:
        intent_to_action = {
            "get_user_count": "getusercount",
        }

        if intent not in intent_to_action:
            raise ValidationError(
                f"Unknown command intent: {intent}",
                {"intent": intent}
            )

        action = intent_to_action[intent]

        # No params expected, but keep mapping for extensibility
        param_mapping = {}

        mapped_params = {param_mapping.get(k, k): v for k, v in params.items()}
        logger.debug(f"Mapped parameters: {mapped_params}")

        is_resolved, result = resolve_params_for_group(
            "command",
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
            "group": "command",
            "params": {"action": action},
        }

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "error": str(e),
            "code": e.code,
            "details": e.details
        }

    except Exception as e:
        logger.error(f"Error handling command intent: {str(e)}")
        return {
            "error": f"Failed to process command intent: {str(e)}",
            "code": "COMMAND_HANDLER_ERROR"
        }