from app.core.param_resolver import resolve_user_params

def handle_user_intent(intent, params):

    if intent == "add_user":
        action = "set"

    elif intent == "delete_user":
        action = "delete"

    elif intent == "update_user":
        action = "set"

    else:
        return {"error": "Invalid intent"}

    # Map LLM keys → API keys
    mapped = {}

    if "user_id" in params:
        mapped["user-id"] = params["user_id"]

    if "name" in params:
        mapped["name"] = params["name"]

    ok, result = resolve_user_params(action, mapped)

    if not ok:
        return {
            "need_input": True,
            "missing": result["missing"],
            "partial": result["partial"]
        }

    return {
        "group": "users",
        "params": {
            "action": action,
            **result
        }
    }