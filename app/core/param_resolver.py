from typing import Tuple, Dict
from app.core.memory import memory
from app.schemas.registry import schema_registry
from app.exceptions import MissingParametersError, ValidationError
from app.logger import logger, log_parameter_resolution


MEMORY_KEY_MAP = {
    "users": "last_user",
    "enroll-options": "last_enroll_options",
    "access-setting": "last_access_setting",
}


def resolve_params_for_group(group: str, action: str, params: Dict) -> Tuple[bool, Dict]:
    logger.debug(f"Resolving parameters for {group}.{action}")
    try:
        schema = schema_registry.get(group)
        required = schema.get_required_fields(action)
        optional = schema.get_optional_fields(action)
        all_valid_fields = required + optional

        memory_key = MEMORY_KEY_MAP.get(group, f"last_{group}")
        last_context = memory.get(memory_key) or {}
        memory_context = {k: v for k, v in last_context.items() if k in all_valid_fields}

        merged = {**memory_context, **params}
        missing = [field for field in required if field not in merged]

        if missing:
            log_parameter_resolution(params, missing, merged)
            logger.info(f"Missing required parameters: {missing}")
            memory.set(memory_key, merged)  # save partial so next turn can complete it
            return False, {"missing": missing, "partial": merged, "resolved": None}

        is_valid, validation_result = schema.validate_parameters(action, merged)
        if not is_valid:
            raise ValidationError(f"Invalid parameters for {group}.{action}", validation_result)

        logger.info(f"All parameters resolved for {group}.{action}")
        memory.set(memory_key, merged)
        return True, {"missing": [], "partial": merged, "resolved": merged}

    except (MissingParametersError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Error resolving {group} parameters: {str(e)}")
        raise ValidationError(
            f"Failed to resolve parameters: {str(e)}",
            {"group": group, "error_type": type(e).__name__}
        )


def resolve_user_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    return resolve_params_for_group("users", action, params)


def resolve_enroll_options_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    return resolve_params_for_group("enroll-options", action, params)


def resolve_access_setting_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    return resolve_params_for_group("access-setting", action, params)
