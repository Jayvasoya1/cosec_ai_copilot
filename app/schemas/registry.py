"""
Schema Registry - Centralized management of all API group schemas
Enables dynamic routing and handler selection
"""

from typing import Dict, Optional
from app.schemas.base_schema import BaseSchema
from schemas.user_schema import user_schema
from schemas.enroll_options_schema import enroll_options_schema
from schemas.access_setting_schema import access_setting_schema
from schemas.panel_details_schema import panel_details_schema
from schemas.panel_door_list_schema import panel_door_list_schema
from schemas.command_schema import command_schema
from schemas.panel_door_config_schema import panel_door_config_schema
from app.exceptions import SchemaError
from app.logger import logger


class SchemaRegistry:
    """
    Centralized registry for all API group schemas
    
    Features:
    - Dynamic schema registration
    - Schema lookup by group name
    - Validation against registered schemas
    - Extensible for future groups
    """
    
    def __init__(self):
        self._schemas: Dict[str, BaseSchema] = {}
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register built-in schemas"""
        self.register("users", user_schema)
        self.register("enroll-options", enroll_options_schema)
        self.register("access-setting", access_setting_schema)
        self.register("panel-details", panel_details_schema)
        self.register("panel-door-list",panel_door_list_schema)
        self.register("panel-door-config", panel_door_config_schema)
        self.register("command",command_schema)
        logger.info("Schema registry initialized with default schemas")
    
    def register(self, group_name: str, schema: BaseSchema):
        """
        Register a new schema
        
        Args:
            group_name: API group name
            schema: Schema instance
        """
        if group_name in self._schemas:
            logger.warning(f"Overwriting existing schema for group: {group_name}")
        
        if not isinstance(schema, BaseSchema):
            raise SchemaError(
                f"Schema must inherit from BaseSchema",
                group_name
            )
        
        self._schemas[group_name] = schema
        logger.info(f"Registered schema for group: {group_name}")
    
    def get(self, group_name: str) -> BaseSchema:
        """
        Get schema by group name
        
        Args:
            group_name: API group name
            
        Returns:
            Schema instance
            
        Raises:
            SchemaError: If schema not found
        """
        if group_name not in self._schemas:
            raise SchemaError(
                f"No schema registered for group: {group_name}",
                group_name
            )
        
        return self._schemas[group_name]
    
    def get_optional(self, group_name: str) -> Optional[BaseSchema]:
        """Get schema by group name, return None if not found"""
        return self._schemas.get(group_name)
    
    def list_groups(self) -> list:
        """Return list of all registered group names"""
        return list(self._schemas.keys())
    
    def is_registered(self, group_name: str) -> bool:
        """Check if group schema is registered"""
        return group_name in self._schemas
    
    def get_actions(self, group_name: str) -> Dict:
        """Get available actions for a group"""
        schema = self.get(group_name)
        return schema.actions
    
    def get_action_description(self, group_name: str, action: str) -> str:
        """Get description of specific action"""
        schema = self.get(group_name)
        if action not in schema.actions:
            raise SchemaError(
                f"Action '{action}' not found in group '{group_name}'",
                group_name
            )
        return schema.actions[action].get("description", "No description")
    
    def get_all_schemas_info(self) -> Dict:
        """Get information about all registered schemas"""
        return {
            group: schema.get_schema_info()
            for group, schema in self._schemas.items()
        }


# Global registry instance
schema_registry = SchemaRegistry()
