# """
# Parameter Resolver - Resolves missing parameters using context and memory
# Ensures all required parameters are available before API execution
# """

# from typing import Tuple, Dict, List
# from schemas.user_schema import user_schema
# from app.core.memory import memory
# from app.exceptions import MissingParametersError, ValidationError
# from app.logger import logger, log_parameter_resolution


# def resolve_user_params(action: str, params: Dict) -> Tuple[bool, Dict]:
#     """
#     Resolve user parameters for action
#     Uses user_schema and memory for context
    
#     Args:
#         action: API action (set, get, delete)
#         params: Provided parameters
        
#     Returns:
#         (all_required_resolved, result_dict)
#         result_dict = {
#             "missing": list of missing fields if not resolved,
#             "partial": partial parameters with memory context,
#             "resolved": final resolved parameters if all required found
#         }
#     """
    
#     logger.debug(f"Resolving parameters for user.{action}")
    
#     try:
#         # Get required and optional fields for this action
#         required = user_schema.get_required_fields(action)
#         optional = user_schema.get_optional_fields(action)
#         all_valid_fields = required + optional
        
#         logger.debug(f"Required: {required}, Optional: {optional}")
        
#         # Get last user context from memory
#         last_user = memory.get("last_user") or {}
#         logger.debug(f"Memory context: {last_user}")
        
#         # Only use fields from memory that are valid for this action
#         # This prevents invalid fields from being included
#         memory_context = {
#             k: v for k, v in last_user.items() 
#             if k in all_valid_fields
#         }
        
#         # Merge: memory_context + provided params (provided takes precedence)
#         merged = {**memory_context, **params}
        
#         logger.debug(f"Merged parameters: {merged}")
        
#         # Find missing required fields
#         missing = [field for field in required if field not in merged]
        
#         if missing:
#             log_parameter_resolution(params, missing, merged)
#             logger.info(f"Missing required parameters: {missing}")
            
#             return False, {
#                 "missing": missing,
#                 "partial": merged,
#                 "resolved": None
#             }
        
#         # Validate all parameters against schema
#         try:
#             is_valid, validation_result = user_schema.validate_parameters(action, merged)
            
#             if not is_valid:
#                 raise ValidationError(
#                     f"Invalid parameters for user.{action}",
#                     validation_result
#                 )
            
#         except ValidationError as e:
#             logger.error(f"Validation failed: {str(e)}")
#             raise
        
#         # All required parameters resolved and valid
#         logger.info(f"All parameters resolved for user.{action}")
        
#         # Save to memory for future context (only save valid fields)
#         memory.set("last_user", merged)
#         logger.debug("Saved to memory context")
        
#         return True, {
#             "missing": [],
#             "partial": merged,
#             "resolved": merged
#         }
        
#     except (MissingParametersError, ValidationError):
#         raise
        
#     except Exception as e:
#         logger.error(f"Error resolving parameters: {str(e)}")
#         raise ValidationError(
#             f"Failed to resolve parameters: {str(e)}",
#             {"error_type": type(e).__name__}
#         )


# def resolve_parameters_for_group(group: str, action: str, params: Dict) -> Tuple[bool, Dict]:
#     """
#     Generic parameter resolver for any group
#     To be extended as more groups are added
    
#     Args:
#         group: API group name (e.g., "users")
#         action: API action
#         params: Parameters to resolve
        
#     Returns:
#         (resolved, result_dict)
#     """
    
#     logger.debug(f"Resolving parameters for {group}.{action}")
    
#     if group == "users":
#         return resolve_user_params(action, params)
    
#     else:
#         raise ValidationError(
#             f"No resolver for group: {group}",
#             {"group": group}
#         )


"""
Parameter Resolver - Resolves missing parameters using context and memory
Ensures all required parameters are available before API execution
"""

from typing import Tuple, Dict, List
from schemas.user_schema import user_schema
from schemas.enroll_options_schema import enroll_options_schema
from  schemas.access_setting_schema import access_setting_schema
# from schemas.enroll_options_schema import en
from app.core.memory import memory
from app.exceptions import MissingParametersError, ValidationError
from app.logger import logger, log_parameter_resolution


def resolve_user_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    """
    Resolve user parameters for action
    Uses user_schema and memory for context
    
    Args:
        action: API action (set, get, delete)
        params: Provided parameters
        
    Returns:
        (all_required_resolved, result_dict)
        result_dict = {
            "missing": list of missing fields if not resolved,
            "partial": partial parameters with memory context,
            "resolved": final resolved parameters if all required found
        }
    """
    
    logger.debug(f"Resolving parameters for user.{action}")
    
    try:
        # Get required and optional fields for this action
        required = user_schema.get_required_fields(action)
        optional = user_schema.get_optional_fields(action)
        all_valid_fields = required + optional
        
        logger.debug(f"Required: {required}, Optional: {optional}")
        
        # Get last user context from memory
        last_user = memory.get("last_user") or {}
        logger.debug(f"Memory context: {last_user}")
        
        # Only use fields from memory that are valid for this action
        # This prevents invalid fields from being included
        memory_context = {
            k: v for k, v in last_user.items() 
            if k in all_valid_fields
        }
        
        # Merge: memory_context + provided params (provided takes precedence)
        merged = {**memory_context, **params}
        
        logger.debug(f"Merged parameters: {merged}")
        
        # Find missing required fields
        missing = [field for field in required if field not in merged]
        
        if missing:
            log_parameter_resolution(params, missing, merged)
            logger.info(f"Missing required parameters: {missing}")
            
            return False, {
                "missing": missing,
                "partial": merged,
                "resolved": None
            }
        
        # Validate all parameters against schema
        try:
            is_valid, validation_result = user_schema.validate_parameters(action, merged)
            
            if not is_valid:
                raise ValidationError(
                    f"Invalid parameters for user.{action}",
                    validation_result
                )
            
        except ValidationError as e:
            logger.error(f"Validation failed: {str(e)}")
            raise
        
        # All required parameters resolved and valid
        logger.info(f"All parameters resolved for user.{action}")
        
        # Save to memory for future context (only save valid fields)
        memory.set("last_user", merged)
        logger.debug("Saved to memory context")
        
        return True, {
            "missing": [],
            "partial": merged,
            "resolved": merged
        }
        
    except (MissingParametersError, ValidationError):
        raise
        
    except Exception as e:
        logger.error(f"Error resolving parameters: {str(e)}")
        raise ValidationError(
            f"Failed to resolve parameters: {str(e)}",
            {"error_type": type(e).__name__}
        )


def resolve_enroll_options_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    
    
    logger.debug(f"Resolving parameters for enrolling.{action}")
    
    try:
        # Get required and optional fields for this action
        required = enroll_options_schema.get_required_fields(action)
        optional = enroll_options_schema.get_optional_fields(action)
        all_valid_fields = required + optional
        
        logger.debug(f"Required: {required}, Optional: {optional}")
        
        # Get last user context from memory
        last_enroll = memory.get("last_enroll") or {}
        logger.debug(f"Memory context: {last_enroll}")
        
        # Only use fields from memory that are valid for this action
        # This prevents invalid fields from being included
        memory_context = {
            k: v for k, v in last_enroll.items() 
            if k in all_valid_fields
        }
        
        # Merge: memory_context + provided params (provided takes precedence)
        merged = {**memory_context, **params}
        
        logger.debug(f"Merged parameters: {merged}")
        
        # Find missing required fields
        missing = [field for field in required if field not in merged]
        
        if missing:
            log_parameter_resolution(params, missing, merged)
            logger.info(f"Missing required parameters: {missing}")
            
            return False, {
                "missing": missing,
                "partial": merged,
                "resolved": None
            }
        
        # Validate all parameters against schema
        try:
            is_valid, validation_result = enroll_options_schema.validate_parameters(action, merged)
            
            if not is_valid:
                raise ValidationError(
                    f"Invalid parameters for enroll.{action}",
                    validation_result
                )
            
        except ValidationError as e:
            logger.error(f"Validation failed: {str(e)}")
            raise
        
        # All required parameters resolved and valid
        logger.info(f"All parameters resolved for enroll.{action}")
        
        # Save to memory for future context (only save valid fields)
        memory.set("last_enroll", merged)
        logger.debug("Saved to memory context")
        
        return True, {
            "missing": [],
            "partial": merged,
            "resolved": merged
        }
        
    except (MissingParametersError, ValidationError):
        raise
        
    except Exception as e:
        logger.error(f"Error resolving parameters: {str(e)}")
        raise ValidationError(
            f"Failed to resolve parameters: {str(e)}",
            {"error_type": type(e).__name__}
        )


def resolve_parameters_for_group(group: str, action: str, params: Dict) -> Tuple[bool, Dict]:
    """
    Generic parameter resolver for any group
    To be extended as more groups are added
    
    Args:
        group: API group name (e.g., "users")
        action: API action
        params: Parameters to resolve
        
    Returns:
        (resolved, result_dict)
    """
    
    logger.debug(f"Resolving parameters for {group}.{action}")
    
    if group == "users":
        return resolve_user_params(action, params)
    
    else:
        raise ValidationError(
            f"No resolver for group: {group}",
            {"group": group}
        )
    



def resolve_access_setting_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    """
    Resolve access-setting parameters for action
    Uses access_setting_schema and memory for context
    
    Args:
        action: API action (get, set, getdefault, setdefault)
        params: Provided parameters
        
    Returns:
        (all_required_resolved, result_dict)
        result_dict = {
            "missing": list of missing fields if not resolved,
            "partial": partial parameters with memory context,
            "resolved": final resolved parameters if all required found
        }
    """
    
    logger.debug(f"Resolving parameters for access-setting.{action}")
    
    try:
        # Get required and optional fields for this action
        required = access_setting_schema.get_required_fields(action)
        optional = access_setting_schema.get_optional_fields(action)
        all_valid_fields = required + optional
        
        logger.debug(f"Required: {required}, Optional: {optional}")
        
        # Get last access-setting context from memory
        last_access_setting = memory.get("last_access_setting") or {}
        logger.debug(f"Memory context: {last_access_setting}")
        
        # Only use fields from memory that are valid for this action
        memory_context = {
            k: v for k, v in last_access_setting.items()
            if k in all_valid_fields
        }
        
        # Merge: memory_context + provided params (provided takes precedence)
        merged = {**memory_context, **params}
        
        logger.debug(f"Merged parameters: {merged}")
        
        # Find missing required fields
        missing = [field for field in required if field not in merged]
        
        if missing:
            log_parameter_resolution(params, missing, merged)
            logger.info(f"Missing required parameters: {missing}")
            
            return False, {
                "missing": missing,
                "partial": merged,
                "resolved": None
            }
        
        # Validate all parameters against schema
        try:
            is_valid, validation_result = access_setting_schema.validate_parameters(action, merged)
            
            if not is_valid:
                raise ValidationError(
                    f"Invalid parameters for access-setting.{action}",
                    validation_result
                )
            
        except ValidationError as e:
            logger.error(f"Validation failed: {str(e)}")
            raise
        
        # All required parameters resolved and valid
        logger.info(f"All parameters resolved for access-setting.{action}")
        
        # Save to memory for future context (only save valid fields)
        memory.set("last_access_setting", merged)
        logger.debug("Saved to memory context")
        
        return True, {
            "missing": [],
            "partial": merged,
            "resolved": merged
        }
        
    except (MissingParametersError, ValidationError):
        raise
        
    except Exception as e:
        logger.error(f"Error resolving parameters: {str(e)}")
        raise ValidationError(
            f"Failed to resolve parameters: {str(e)}",
            {"error_type": type(e).__name__}
        )


