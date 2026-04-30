"""
EnrollUser group schema - handles enrollment configuration
API Group: enrolluser
"""

from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema


class EnrollOptionsSchema(BaseSchema):
    """Schema for /device.cgi/enrolluser API group"""
    
    group_name = "enrolluser"
    
    actions = {
        "enroll": {
            "description": "enroll user",
            "required": ["pdid", "user-id"],
            "optional": []
        }
    }
    
    # Field constraints and valid values
    FIELD_CONSTRAINTS = {
        "pdid": {"type": "int"},
        "user-id": {"type": "int"}
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
            "user_id": "user-id",
        }
        
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            transformed[api_key] = value
        
        return transformed


# Global instance for registry
enroll_options_schema = EnrollOptionsSchema()
