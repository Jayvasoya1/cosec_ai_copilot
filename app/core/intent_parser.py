import json
from app.llm.openai_client import call_llm

def parse_intent(user_input: str):
    raw = call_llm(user_input)

    try:
        return json.loads(raw)
    except Exception:
        return {
            "tasks": [],
            "error": "Invalid JSON from LLM"
        }