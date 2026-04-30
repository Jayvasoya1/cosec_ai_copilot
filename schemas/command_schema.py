from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema


class CommandSchema(BaseSchema):
    """Schema for /device.cgi/command API group"""

    group_name = "command"

    actions = {
        "getusercount": {
            "description": "Get total number of users configured in the device",
            # action itself is required but handled internally
            "required": [],
            "optional": [],
        }
    }

    FIELD_CONSTRAINTS = {
        # No additional parameters for this API
    }

    def get_required_fields(self, action: str) -> List[str]:
        return self.actions[action]["required"]

    def get_optional_fields(self, action: str) -> List[str]:
        return self.actions[action]["optional"]

    def validate_field_values(self, field_name: str, value: Any) -> bool:
        # No fields to validate
        return True

    def transform_params(self, action: str, params: Dict) -> Dict:
        return params


# Global instance
command_schema = CommandSchema()