def generate_question(missing_fields):
    questions = {
        "user-id": "Please provide user ID",
        "name": "Please provide user name"
    }

    msgs = [questions.get(f, f"Provide {f}") for f in missing_fields]

    return " | ".join(msgs)