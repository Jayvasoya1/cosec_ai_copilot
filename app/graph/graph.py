from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import CopilotState
from app.graph.nodes import (
    classify_node,
    validate_node,
    execute_node,
    respond_node,
)


def _route_classify(state: CopilotState) -> str:
    """
    After classify_node:
      - If tasks exist, proceed to validate.
      - Otherwise, we didn't understand the input (or it was pure chat) → respond directly.
    """
    if state.get("tasks"):
        return "validate_node"
    return "respond_node"


def _route_validate(state: CopilotState) -> str:
    """
    After validate_node:
      - If missing_fields is populated, we need to ask the user → skip to respond.
      - If execution_result has an error (e.g. invalid value), skip to respond.
      - Otherwise, params are valid → proceed to execute.
    """
    if state.get("missing_fields"):
        return "respond_node"
    
    res = state.get("execution_result")
    if res and res.get("status") == "error":
        return "respond_node"
        
    return "execute_node"


def _route_execute(state: CopilotState) -> str:
    """
    After execute_node:
      - If execution failed (execution_result is error), stop and report.
      - If tasks still remain in the queue, loop back to validate the next task.
      - Otherwise, all tasks completed successfully → proceed to respond.
    """
    res = state.get("execution_result")
    if res and res.get("status") == "error":
        return "respond_node"
        
    if state.get("tasks"):
        return "validate_node"
        
    return "respond_node"


builder = StateGraph(CopilotState)

builder.add_node("classify_node", classify_node)
builder.add_node("validate_node", validate_node)
builder.add_node("execute_node",  execute_node)
builder.add_node("respond_node",  respond_node)

builder.add_edge(START, "classify_node")

builder.add_conditional_edges(
    "classify_node",
    _route_classify,
    {
        "validate_node": "validate_node",
        "respond_node":  "respond_node",
    }
)

builder.add_conditional_edges(
    "validate_node",
    _route_validate,
    {
        "execute_node": "execute_node",
        "respond_node": "respond_node",
    }
)

builder.add_conditional_edges(
    "execute_node",
    _route_execute,
    {
        "validate_node": "validate_node",
        "respond_node":  "respond_node",
    }
)

builder.add_edge("respond_node", END)

# In-memory checkpointer for multi-turn conversational state (like "What's the ID?")
memory = MemorySaver()

# Export the compiled LangGraph object
graph = builder.compile(checkpointer=memory)
