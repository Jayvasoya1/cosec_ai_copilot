from handlers.user_handler import handle_user_intent

def route_intent(task):
    intent = task["intent"]
    params = task.get("parameters", {})

    if intent in ["add_user", "delete_user", "update_user"]:
        return handle_user_intent(intent, params)

    return {"error": "Unknown intent"}