"""
User group schema - handles all user-related API operations
Following BaseSchema pattern for consistency and extensibility
"""

from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema
from app.exceptions import ValidationError


class UserSchema(BaseSchema):
    """Schema for /device.cgi/users API group"""
    
    group_name = "users"
    
    actions = {
        "set": {
            "description": "Create or update user",
            "required": ["user-id", "name"],
            "optional": [
                "ref-user-id",
                "user-active",
                "vip",
                "user-pin",
                "card1",
                "card2",
                "user-group",
                "restrict-access",
                "route-id",
                "by-pass-finger",
                "by-pass-palm",
                "by-pass-face",
                "validity-enable",
                "validity-date-dd",
                "validity-date-mm",
                "validity-date-yyyy",
                "validity-time-hh",
                "validity-time-mm"
            ]
        },
        "get": {
            "description": "Retrieve user information",
            "required": [],  # At least one of user-id or ref-user-id needed
            "optional": [
                "user-id",
                "ref-user-id",
                "name",
                "user-active",
                "vip",
                "user-pin",
                "card1",
                "card2",
                "user-group"
            ]
        },
        "delete": {
            "description": "Delete user and associated credentials",
            "required": ["user-id"],
            "optional": []
        }
    }
    
    # Field constraints and valid values
    FIELD_CONSTRAINTS = {
        "user-active": {"type": "int", "values": [0, 1]},
        "vip": {"type": "int", "values": [0, 1]},
        "by-pass-finger": {"type": "int", "values": [0, 1]},
        "by-pass-palm": {"type": "int", "values": [0, 1]},
        "by-pass-face": {"type": "int", "values": [0, 1]},
        "restrict-access": {"type": "int", "values": [0, 1]},
        "validity-enable": {"type": "int", "values": [0, 1]},
        "user-group": {"type": "int", "min": 0, "max": 999},
        "validity-date-dd": {"type": "int", "min": 1, "max": 31},
        "validity-date-mm": {"type": "int", "min": 1, "max": 12},
        "validity-date-yyyy": {"type": "int", "min": 2000, "max": 2099},
        "validity-time-hh": {"type": "int", "min": 0, "max": 23},
        "validity-time-mm": {"type": "int", "min": 0, "max": 59},
    }
    
    def get_required_fields(self, action: str) -> List[str]:
        return self.actions[action]["required"]
    
    def get_optional_fields(self, action: str) -> List[str]:
        return self.actions[action]["optional"]
    
    def validate_field_values(self, field_name: str, value: Any) -> bool:
        """Validate field values against constraints"""
        
        if field_name not in self.FIELD_CONSTRAINTS:
            # No constraints defined, assume valid
            return True
        
        constraint = self.FIELD_CONSTRAINTS[field_name]
        constraint_type = constraint.get("type", "string")
        
        try:
            # Type check
            if constraint_type == "int":
                int_value = int(value)
                
                # Check valid values list
                if "values" in constraint:
                    return int_value in constraint["values"]
                
                # Check min/max range
                if "min" in constraint and int_value < constraint["min"]:
                    return False
                if "max" in constraint and int_value > constraint["max"]:
                    return False
                
                return True
            
            elif constraint_type == "string":
                return isinstance(value, str) and len(value) > 0
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def transform_params(self, action: str, params: Dict) -> Dict:
        """
        Transform parameters from intent format to API format
        Maps Python/intent names to API parameter names
        """
        transformed = {}
        
        # Map common parameter names
        param_mapping = {
            "user_id": "user-id",
            "ref_user_id": "ref-user-id",
            "user_name": "name",
            "user_pin": "user-pin",
            "bypass_finger": "by-pass-finger",
            "bypass_palm": "by-pass-palm",
            "bypass_face": "by-pass-face",
        }
        
        for key, value in params.items():
            # Use mapping if available, otherwise use key as-is
            api_key = param_mapping.get(key, key)
            transformed[api_key] = value
        
        return transformed


# Global instance for backwards compatibility
USER_SCHEMA = UserSchema().actions
user_schema = UserSchema()
