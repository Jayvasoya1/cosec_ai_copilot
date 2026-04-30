from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema


class PanelDoorListSchema(BaseSchema):
    """Schema for /device.cgi/panel-door-list API"""

    group_name = "panel-door-list"

    actions = {
        "get": {
            "description": "Get list of configured panel doors or specific door details",
            # action=get is required but handled internally
            "required": [],
            # pdid is optional filter, format defines response type
            "optional": ["pdid", "format"],
        }
    }

    # Field constraints based on API documentation
    FIELD_CONSTRAINTS = {
        "format": {"type": "string", "values": ["text", "xml"]},
        # pdid values come from external configuration → no strict validation here
    }

    def get_required_fields(self, action: str) -> List[str]:
        return self.actions[action]["required"]

    def get_optional_fields(self, action: str) -> List[str]:
        return self.actions[action]["optional"]

    def validate_field_values(self, field_name: str, value: Any) -> bool:
        if field_name not in self.FIELD_CONSTRAINTS:
            return True

        constraint = self.FIELD_CONSTRAINTS[field_name]

        if constraint.get("type") == "string" and "values" in constraint:
            return str(value).lower() in constraint["values"]

        return True

    def transform_params(self, action: str, params: Dict) -> Dict:
        # No transformation required; handled in handler layer
        return params


# Global instance used by registry
panel_door_list_schema = PanelDoorListSchema()