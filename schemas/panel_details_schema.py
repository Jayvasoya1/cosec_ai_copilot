from typing import Dict, List, Any
from app.schemas.base_schema import BaseSchema


class PanelDetailsSchema(BaseSchema):
    """Schema for /device.cgi/panel-details API group"""

    group_name = "panel-details"

    actions = {
        "get": {
            "description": "Get panel summary — users, doors, alarms, IO-links",
            # action=get is always required but handled by the action itself, not as a param
            "required": [],
            # Passing user/door/alarm/io-link as filter flags; omit all → returns full summary
            "optional": ["user", "door", "alarm", "io-link", "format"],
        }
    }

    # Manually-defined constraints (per API manual)
    # user / door / alarm / io-link are presence flags — no value constraint
    FIELD_CONSTRAINTS = {
        "format": {"type": "string", "values": ["text", "xml"]},
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
        return params   # mapping is done in the handler


# Global instance used by registry
panel_details_schema = PanelDetailsSchema()
