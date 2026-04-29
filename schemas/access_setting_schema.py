"""
Access-Setting group schema - handles access timing configuration
API Group: access-setting
"""

from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema
from app.exceptions import ValidationError


class AccessSettingSchema(BaseSchema):
    """Schema for /device.cgi/access-setting API group"""
    
    group_name = "access-setting"
    
    actions = {
        "get": {
            "description": "Get current access settings",
            "required": [],
            "optional": [
                "week-day",
                "work-start-hh",
                "work-start-mm",
                "work-end-hh",
                "work-end-mm",
                "format"
            ]
        },
        "set": {
            "description": "Set access settings",
            "required": [],
            "optional": [
                "week-day",
                "work-start-hh",
                "work-start-mm",
                "work-end-hh",
                "work-end-mm",
                "format"
            ]
        },
        "getdefault": {
            "description": "Get default access settings",
            "required": [],
            "optional": ["format"]
        },
        "setdefault": {
            "description": "Set default access settings",
            "required": [],
            "optional": [
                "week-day",
                "work-start-hh",
                "work-start-mm",
                "work-end-hh",
                "work-end-mm",
                "format"
            ]
        }
    }
    
    # Field constraints and valid values
    FIELD_CONSTRAINTS = {
        "week-day": {"type": "int", "min": 0, "max": 6},  # 0=Sunday, 6=Saturday
        "work-start-hh": {"type": "int", "min": 0, "max": 23},
        "work-start-mm": {"type": "int", "min": 0, "max": 59},
        "work-end-hh": {"type": "int", "min": 0, "max": 23},
        "work-end-mm": {"type": "int", "min": 0, "max": 59},
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
        
        param_mapping = {
            "week_day": "week-day",
            "work_start_hh": "work-start-hh",
            "work_start_mm": "work-start-mm",
            "work_end_hh": "work-end-hh",
            "work_end_mm": "work-end-mm",
        }
        
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            transformed[api_key] = value
        
        return transformed


# Global instances for registry and backwards compatibility
ACCESS_SETTING_SCHEMA = AccessSettingSchema().actions
access_setting_schema = AccessSettingSchema()




