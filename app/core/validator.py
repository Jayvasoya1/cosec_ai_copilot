INTENT_REQUIREMENTS = {
    "add_user": ["name", "user_id"],
    "delete_user": ["user_id"],
    "update_user": ["user_id"]
}

def validate_intent(data: dict):
    intent = data.get("intent")
    params = data.get("parameters", {})

    if intent not in INTENT_REQUIREMENTS:
        return False, "Unsupported intent"

    missing = [p for p in INTENT_REQUIREMENTS[intent] if p not in params]

    if missing:
        return False, f"Missing parameters: {missing}"

    return True, "Valid"