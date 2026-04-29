"""
Enroll-Options group schema - handles enrollment configuration
API Group: enroll-options
"""

from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema


class EnrollOptionsSchema(BaseSchema):
    """Schema for /device.cgi/enroll-options API group"""
    
    group_name = "enroll-options"
    
    actions = {
        "get": {
            "description": "Get current enrollment options",
            "required": [],
            "optional": ["format"]
        },
        "set": {
            "description": "Set enrollment options",
            "required": ["action"],  # Only action required, rest optional
            "optional": [
                "enroll-on-device",
                "enroll-using",
                "enroll-finger-count",
                "enroll-palm-count",
                "enroll-card-count",
                "enroll-mode",
                "format"
            ]
        },
        "getdefault": {
            "description": "Get default enrollment options",
            "required": [],
            "optional": ["format"]
        },
        "setdefault": {
            "description": "Set default enrollment options",
            "required": [],
            "optional": [
                "enroll-on-device",
                "enroll-using",
                "enroll-finger-count",
                "enroll-palm-count",
                "enroll-card-count",
                "enroll-mode",
                "format"
            ]
        }
    }
    
    # Field constraints and valid values
    FIELD_CONSTRAINTS = {
        "enroll-on-device": {"type": "int", "values": [0, 1]},
        "enroll-using": {"type": "int", "values": [0, 1]},  # 0=numeric, 1=alphanumeric
        "enroll-finger-count": {"type": "int", "min": 1, "max": 10},
        "enroll-palm-count": {"type": "int", "min": 1, "max": 2},
        "enroll-card-count": {"type": "int", "min": 1, "max": 5},
        "enroll-mode": {"type": "int", "values": [0, 1]},  # 0=single template, 1=dual template
        "format": {"type": "string", "values": ["text", "xml"]},
    }
    
    def get_required_fields(self, action: str) -> List[str]:
        return self.actions[action]["required"]
    
    def get_optional_fields(self, action: str) -> List[str]:
        return self.actions[action]["optional"]
    
    def validate_field_values(self, field_name: str, value: Any) -> bool:
        """Validate field values against constraints"""
        
        if field_name not in self.FIELD_CONSTRAINTS:
            return True
        
        constraint = self.FIELD_CONSTRAINTS[field_name]
        constraint_type = constraint.get("type", "string")
        
        try:
            if constraint_type == "int":
                int_value = int(value)
                
                if "values" in constraint:
                    return int_value in constraint["values"]
                
                if "min" in constraint and int_value < constraint["min"]:
                    return False
                if "max" in constraint and int_value > constraint["max"]:
                    return False
                
                return True
            
            elif constraint_type == "string":
                if "values" in constraint:
                    return str(value).lower() in constraint["values"]
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
            "enroll_on_device": "enroll-on-device",
            "enroll_using": "enroll-using",
            "enroll_finger_count": "enroll-finger-count",
            "enroll_palm_count": "enroll-palm-count",
            "enroll_card_count": "enroll-card-count",
            "enroll_mode": "enroll-mode",
        }
        
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            transformed[api_key] = value
        
        return transformed


# Global instance for registry
enroll_options_schema = EnrollOptionsSchema()
