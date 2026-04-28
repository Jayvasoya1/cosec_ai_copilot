# Next Steps - Expanding Your CoSec AI Copilot

## 🎯 Quick Start with Improvements

Your codebase has been upgraded with production-quality error handling, logging, and scalability. Here's how to use it:

### 1. **Setup Environment**
```bash
# Copy configuration template
cp .env.example .env

# Install dependencies (if not already done)
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload
```

### 2. **Test the System**
```bash
# Test endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Add user John with id 101"}'

# Check health
curl http://localhost:8000/health
```

### 3. **Enable Debug Logging**
```bash
# In .env
DEBUG_MODE=True

# Now you'll see detailed logs showing:
# - Intent parsing steps
# - Parameter resolution
# - Schema validation
# - API calls
# - Memory context usage
```

---

## 📚 Adding Your Next API Group

Follow this step-by-step guide to add another COSEC API group.

### Example: Adding "Access Groups"

**Step 1: Create Schema** (`schemas/access_group_schema.py`)

```python
from app.schemas.base_schema import BaseSchema
from typing import Dict, List, Any

class AccessGroupSchema(BaseSchema):
    """Schema for /device.cgi/accessgroup API"""
    
    group_name = "accessgroup"
    
    actions = {
        "set": {
            "description": "Create or update access group",
            "required": ["groupid", "name"],
            "optional": [
                "access-level",
                "zones",
                "validity-enable",
                "validity-start-date",
                "validity-end-date"
            ]
        },
        "get": {
            "description": "Retrieve access group info",
            "required": [],
            "optional": ["groupid", "name", "access-level"]
        },
        "delete": {
            "description": "Delete access group",
            "required": ["groupid"],
            "optional": []
        }
    }
    
    FIELD_CONSTRAINTS = {
        "groupid": {"type": "int", "min": 1, "max": 999},
        "name": {"type": "string"},
        "access-level": {"type": "int", "values": [1, 2, 3]},
        "validity-enable": {"type": "int", "values": [0, 1]},
    }
    
    def get_required_fields(self, action: str) -> List[str]:
        return self.actions[action]["required"]
    
    def get_optional_fields(self, action: str) -> List[str]:
        return self.actions[action]["optional"]
    
    def validate_field_values(self, field_name: str, value: Any) -> bool:
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
                return isinstance(value, str) and len(value) > 0
            
            return True
        except (ValueError, TypeError):
            return False
    
    def transform_params(self, action: str, params: Dict) -> Dict:
        """Transform parameter names from intent to API format"""
        param_mapping = {
            "group_id": "groupid",
            "group_name": "name",
            "access_level": "access-level",
        }
        
        transformed = {}
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            transformed[api_key] = value
        
        return transformed

# Create instance for registry
access_group_schema = AccessGroupSchema()
```

**Step 2: Register Schema** (Update `app/schemas/registry.py`)

```python
# At the top with other imports
from schemas.access_group_schema import access_group_schema

class SchemaRegistry:
    def _register_default_schemas(self):
        """Register built-in schemas"""
        self.register("users", user_schema)
        self.register("accessgroup", access_group_schema)  # NEW
        logger.info("Schema registry initialized with default schemas")
```

**Step 3: Create Handler** (`handlers/access_group_handler.py`)

```python
from typing import Dict
from app.core.param_resolver import resolve_parameters_for_group
from app.exceptions import ValidationError
from app.logger import logger

def handle_access_group_intent(intent: str, params: Dict) -> Dict:
    """Handle access group-related intents"""
    
    logger.debug(f"Handling access group intent: {intent}")
    
    try:
        # Map intents to actions
        intent_to_action = {
            "add_access_group": "set",
            "delete_access_group": "delete",
            "update_access_group": "set",
            "get_access_group": "get",
        }
        
        if intent not in intent_to_action:
            raise ValidationError(f"Unknown access group intent: {intent}")
        
        action = intent_to_action[intent]
        
        # Transform parameters
        param_mapping = {
            "group_id": "groupid",
            "group_name": "name",
            "access_level": "access-level",
        }
        
        mapped_params = {}
        for key, value in params.items():
            api_key = param_mapping.get(key, key)
            mapped_params[api_key] = value
        
        # Resolve parameters
        is_resolved, result = resolve_parameters_for_group(
            "accessgroup",
            action,
            mapped_params
        )
        
        if not is_resolved:
            return {
                "need_input": True,
                "missing": result.get("missing", []),
                "partial": result.get("partial", {})
            }
        
        return {
            "group": "accessgroup",
            "params": {
                "action": action,
                **result.get("resolved", {})
            }
        }
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return {
            "error": str(e),
            "code": e.code,
            "details": e.details
        }
    except Exception as e:
        logger.error(f"Error handling access group intent: {str(e)}")
        return {
            "error": f"Failed to process: {str(e)}",
            "code": "ACCESSGROUP_HANDLER_ERROR"
        }
```

**Step 4: Register Handler** (Update `app/core/router.py`)

```python
from handlers.access_group_handler import handle_access_group_intent

class HandlerRegistry:
    def _register_default_handlers(self):
        """Register built-in handlers"""
        self.register_pattern("user_", handle_user_intent)
        self.register_pattern("access_group_", handle_access_group_intent)  # NEW
        logger.info("Handler registry initialized with default handlers")
```

**Step 5: Update LLM Prompt** (Update `app/llm/openai_client.py`)

```python
SYSTEM_PROMPT = """
You are an intent detection engine for a security system.

Return ONLY valid JSON. No explanation, no markdown, just pure JSON.

Format:
{
  "tasks": [
    {
      "intent": "",
      "parameters": {}
    }
  ]
}

Supported intents:
- add_user (name, user_id)
- delete_user (user_id)
- update_user (user_id, name)
- add_access_group (name, group_id)
- delete_access_group (group_id)
- update_access_group (group_id, name, access_level)
- get_access_group (group_id)

Examples:

Input: Add access group VIP with id 5
Output:
{
  "tasks": [
    {
      "intent": "add_access_group",
      "parameters": {
        "name": "VIP",
        "group_id": "5"
      }
    }
  ]
}

Input: Delete access group 3
Output:
{
  "tasks": [
    {
      "intent": "delete_access_group",
      "parameters": {
        "group_id": "3"
      }
    }
  ]
}
"""
```

**Step 6: Update Parameter Resolver** (Update `app/core/param_resolver.py`)

```python
def resolve_parameters_for_group(group: str, action: str, params: Dict) -> Tuple[bool, Dict]:
    """Generic parameter resolver for any group"""
    
    logger.debug(f"Resolving parameters for {group}.{action}")
    
    if group == "users":
        return resolve_user_params(action, params)
    
    elif group == "accessgroup":
        return resolve_access_group_params(action, params)  # NEW
    
    else:
        raise ValidationError(f"No resolver for group: {group}")


def resolve_access_group_params(action: str, params: Dict) -> Tuple[bool, Dict]:
    """Resolve access group parameters"""
    from schemas.access_group_schema import access_group_schema
    
    # Use schema for validation
    required = access_group_schema.get_required_fields(action)
    optional = access_group_schema.get_optional_fields(action)
    
    all_valid_fields = required + optional
    invalid_fields = [f for f in params.keys() if f not in all_valid_fields]
    
    if invalid_fields:
        raise ValidationError(f"Invalid fields: {invalid_fields}")
    
    # Check for missing required
    missing = [f for f in required if f not in params]
    
    if missing:
        return False, {
            "missing": missing,
            "partial": params
        }
    
    # Validate values
    is_valid, result = access_group_schema.validate_parameters(action, params)
    
    if not is_valid:
        raise ValidationError(f"Invalid parameters for accessgroup.{action}")
    
    return True, {
        "missing": [],
        "partial": params,
        "resolved": params
    }
```

---

## 🔄 Testing Your New Group

```bash
# Test adding an access group
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Add access group VIP with id 5"
  }'

# Expected response:
{
    "status": "success",
    "message": "✅ Mock executed: {...}",
    "details": {...}
}
```

---

## 📝 Following the Pattern

For each new group you add:

1. **Schema** - Defines API structure & validation
2. **Handler** - Converts intents to API calls
3. **Registry entries** - Register in schema & handler registries
4. **LLM prompt** - Add supported intents
5. **Parameter resolver** - Add resolution logic
6. **Test** - Validate with curl

---

## 🎓 Key Files Reference

| Task | File |
|------|------|
| Add logging | Use `app/logger.py` functions |
| Handle errors | Catch `app.exceptions` error types |
| Add new group | Follow schema pattern in `app/schemas/` |
| Add handler | Follow pattern in `handlers/` |
| Configuration | Update `.env` and `app/config.py` |
| LLM behavior | Update `app/llm/openai_client.py` |

---

## ✅ Best Practices

1. **Always validate** - Use schema validation before API calls
2. **Log everything** - Use logging for debugging
3. **Handle errors gracefully** - Catch specific exceptions
4. **Test each group** - Before moving to next
5. **Keep memory context** - Reuse previous inputs
6. **Document config** - Update `.env.example`

---

## 🚀 Future Enhancements

- [ ] Add database persistence (PostgreSQL/MongoDB)
- [ ] Implement authentication & authorization
- [ ] Add request/response caching
- [ ] Create admin dashboard
- [ ] Add batch operations
- [ ] Implement undo/rollback
- [ ] Add webhooks & notifications
- [ ] Create mobile app
- [ ] Add multi-language support
- [ ] Implement audit logging

---

Happy extending! 🎉
