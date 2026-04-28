from schemas.user_schema import USER_SCHEMA
from app.core.memory import memory

def resolve_user_params(action, params):
    schema = USER_SCHEMA["actions"][action]
    required = schema["required"]

    # 🔥 Merge memory (context reuse)
    last_user = memory.get("last_user") or {}

    merged = {**last_user, **params}

    missing = [p for p in required if p not in merged]

    if missing:
        return False, {"missing": missing, "partial": merged}

    # Save for future
    memory.set("last_user", merged)

    return True, merged