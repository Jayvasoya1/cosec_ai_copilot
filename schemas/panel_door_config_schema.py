"""
Panel Door Config schema - handles door configuration
API Group: panel-door-config
"""

from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema


class PanelDoorConfigSchema(BaseSchema):
    """Schema for /device.cgi/panel-door-config API group"""
    
    group_name = "panel-door-config"
    
    actions = {
        "get": {
            "description": "Get door configuration",
            "required": ["pdid"],
            "optional": ["format"]
        },
        "set": {
            "description": "Set door configuration",
            "required": [
                "door-name",
                "door-type",
                "ip-address",
                "mac-address",
                ],
            "optional": [
                "format"
            ]
        },
        "getdefault": {
            "description": "Get default door configuration",
            "required": [],
            "optional": ["format"]
        },
        "setdefault": {
            "description": "Set default door configuration",
            "required": [],
            "optional": [
                "door-name",
                "door-type",
                "communication-type",
                "ip-address",
                "mac-address",
                "format"
            ]
        }
    }
    
    # Field constraints
    FIELD_CONSTRAINTS = {
        "door-name": {"type": "string"},
        "door-type": {"type": "string"},  # device-specific enum
        "ip-address": {"type": "string"},  # could add regex if needed
        "mac-address": {"type": "string"},  # could validate MAC format
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
        """
        transformed = {}
        
        param_mapping = {
            "door_name": "door-name",
            "door_type": "door-type",
            "ip_address": "ip-address",
            "mac_address": "mac-address",
        }
        
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            transformed[api_key] = value
        
        return transformed


# Global instance
PANEL_DOOR_CONFIG_SCHEMA = PanelDoorConfigSchema().actions
panel_door_config_schema = PanelDoorConfigSchema()