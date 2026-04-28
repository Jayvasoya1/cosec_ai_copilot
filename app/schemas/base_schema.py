"""
Base schema handler class for all API groups
Provides consistent pattern for validation, parameter resolution, and API building
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
from app.exceptions import ValidationError, MissingParametersError, SchemaError
from app.logger import logger


class BaseSchema(ABC):
    """
    Abstract base class for API group schemas
    
    Subclasses should define:
    - group_name: API group name (e.g., "users", "devices")
    - actions: Dict of action configurations
    - required_fields_per_action: Dict mapping actions to required fields
    - optional_fields_per_action: Dict mapping actions to optional fields
    """
    
    group_name: str
    actions: Dict[str, Dict[str, Any]] = {}
    
    @abstractmethod
    def get_required_fields(self, action: str) -> List[str]:
        """Return list of required fields for action"""
        pass
    
    @abstractmethod
    def get_optional_fields(self, action: str) -> List[str]:
        """Return list of optional fields for action"""
        pass
    
    @abstractmethod
    def validate_field_values(self, field_name: str, value: Any) -> bool:
        """Validate if field value is acceptable"""
        pass
    
    @abstractmethod
    def transform_params(self, action: str, params: Dict) -> Dict:
        """Transform/map parameters from intent format to API format"""
        pass
    
    def validate_action(self, action: str) -> bool:
        """Check if action is supported"""
        return action in self.actions
    
    def validate_parameters(self, action: str, params: Dict) -> Tuple[bool, Dict]:
        """
        Validate parameters against schema
        
        Returns:
            (is_valid, result_dict)
            result_dict = {
                "valid": bool,
                "missing": List of missing required fields,
                "partial": Partial parameters dict
            }
        """
        if not self.validate_action(action):
            raise SchemaError(
                f"Action '{action}' not supported for group '{self.group_name}'",
                self.group_name
            )
        
        required = self.get_required_fields(action)
        optional = self.get_optional_fields(action)
        
        # Check for missing required fields
        missing = [f for f in required if f not in params]
        
        if missing:
            logger.debug(f"Missing fields for {self.group_name}.{action}: {missing}")
            return False, {
                "valid": False,
                "missing": missing,
                "partial": params
            }
        
        # Check if all provided fields are valid
        all_valid_fields = required + optional
        invalid_fields = [f for f in params.keys() if f not in all_valid_fields]
        
        if invalid_fields:
            logger.warning(f"Invalid fields for {self.group_name}.{action}: {invalid_fields}")
            raise ValidationError(
                f"Invalid fields: {invalid_fields}",
                {"schema": self.group_name, "invalid_fields": invalid_fields}
            )
        
        # Validate field values
        for field, value in params.items():
            if not self.validate_field_values(field, value):
                raise ValidationError(
                    f"Invalid value for field '{field}': {value}",
                    {"schema": self.group_name, "field": field, "value": value}
                )
        
        logger.debug(f"Parameters valid for {self.group_name}.{action}")
        return True, {"valid": True, "params": params}
    
    def build_api_request(self, action: str, params: Dict) -> Dict:
        """
        Build API request parameters
        
        Returns dict with API-formatted parameters ready for URL building
        """
        # Validate first
        is_valid, result = self.validate_parameters(action, params)
        
        if not is_valid:
            raise MissingParametersError(
                result.get("missing", []),
                result.get("partial", {})
            )
        
        # Transform parameters to API format
        api_params = self.transform_params(action, params)
        
        # Add action
        api_params["action"] = action
        
        logger.debug(f"Built API request for {self.group_name}: {api_params}")
        return api_params
    
    def get_schema_info(self) -> Dict:
        """Return schema information for debugging/documentation"""
        return {
            "group": self.group_name,
            "actions": self.actions
        }
