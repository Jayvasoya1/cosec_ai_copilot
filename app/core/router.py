"""
Router - Routes tasks to appropriate handlers based on intent
Dynamic routing using handler registry
"""

from app.exceptions import RouterError, SchemaError
from app.logger import logger
from handlers.user_handler import handle_user_intent
from handlers.enroll_options_handler import handle_enroll_options_intent
from handlers.access_setting_handler import handle_access_setting_intent

class HandlerRegistry:
    """Registry for intent handlers"""
    
    def __init__(self):
        self._handlers = {}
        self._entity_handlers = {}  # Entity-based routing
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register built-in handlers"""
        # Map entity types to handlers
        # Intents like: add_user, delete_user, update_user → all use user_entity handler
        self.register_entity("user", handle_user_intent)
        self.register_entity("enroll_options", handle_enroll_options_intent)
        self.register_entity("access_setting", handle_access_setting_intent)
        logger.info("Handler registry initialized with default handlers")
    
    def register_entity(self, entity_name: str, handler):
        """
        Register handler for entity type
        
        Args:
            entity_name: Entity name (e.g., "user", "device")
            handler: Handler function
            
        Example:
            register_entity("user", handle_user_intent)
            # Will match: add_user, delete_user, update_user, get_user, etc.
        """
        self._entity_handlers[entity_name] = handler
        logger.debug(f"Registered handler for entity: {entity_name}")
    
    #not use currently
    def register_pattern(self, pattern: str, handler):
        """
        Register handler for exact intent match
        
        Args:
            pattern: Intent name to match exactly
            handler: Handler function
        """
        self._handlers[pattern] = handler
        logger.debug(f"Registered handler for pattern: {pattern}")
    
    def get_handler(self, intent: str):
        """
        Get handler for intent
        
        Args:
            intent: Intent name (e.g., "add_user")
            
        Returns:
            Handler function
            
        Raises:
            RouterError: If no handler found
        """
        # Try exact match first (highest priority) 
        #not use currently
        if intent in self._handlers:
            logger.debug(f"Found exact handler for intent: {intent}")
            return self._handlers[intent]
        
        # Try entity match (second priority)
        # Intent format: {action}_{entity} or {action}_{entity}_{extra}
        # Examples: add_user, delete_user, get_access_group
        for entity_name, handler in self._entity_handlers.items():
            if f"_{entity_name}" in intent:
                logger.debug(f"Found entity handler for {entity_name} in intent: {intent}")
                return handler
        
        # Try pattern match (fallback)
        for pattern, handler in self._handlers.items():
            if intent.startswith(pattern):
                logger.debug(f"Found pattern handler for {pattern} in intent: {intent}")
                return handler
        
        logger.warning(f"No handler found for intent: {intent}")
        raise RouterError(intent)


# Global handler registry
handler_registry = HandlerRegistry()


def route_intent(task: dict) -> dict:
    """
    Route task to appropriate handler
    
    Args:
        task: Task dict with "intent" and "parameters"
        
    Returns:
        Handler response dict
        
    Raises:
        RouterError: If no handler found for intent
    """
    intent = task.get("intent")
    params = task.get("parameters", {})
    
    if not intent:
        raise RouterError("Missing intent in task")
    
    logger.debug(f"Routing intent: {intent} with params: {params}")
    
    try:
        # Get handler for intent
        handler = handler_registry.get_handler(intent)
        
        # Call handler
        result = handler(intent, params)
        
        logger.debug(f"Handler returned: {result}")
        return result
        
    except RouterError:
        raise
        
    except Exception as e:
        logger.error(f"Error in handler for intent '{intent}': {str(e)}")
        raise RouterError(intent.split("_")[0]) from e