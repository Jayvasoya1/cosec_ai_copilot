from fastapi import FastAPI
from pydantic import BaseModel

from app.core.intent_parser import parse_intent
from app.core.planner import plan_tasks
from app.core.router import route_intent
from app.core.executor import execute_tasks
from app.core.response_builder import build_response

app = FastAPI()

class Query(BaseModel):
    text: str


@app.post("/chat")
def chat(query: Query):
    user_input = query.text

    # 1. Parse
    intent_data = parse_intent(user_input)

    # 2. Plan
    tasks = plan_tasks(intent_data)

    if not tasks:
        return {"status": "error", "message": "No tasks found"}

    # 3. Execute
    results = execute_tasks(tasks, route_intent)

    # 4. Build response
    response = build_response(results)

    return response