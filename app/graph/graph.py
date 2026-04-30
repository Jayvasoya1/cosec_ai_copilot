"""
Graph assembly — wires nodes + conditional edges into a compiled LangGraph.

Flow:
  START
    │
    ▼
  classify ──► (no intent) ──────────────────────────────────► respond ──► END
    │
    │ (intent detected)
    ▼
  validate ──► (missing fields or value error) ──────────────► respond ──► END
    │
    │ (all params valid)
    ▼
  execute ────────────────────────────────────────────────────► respond ──► END

State is checkpointed after every node by MemorySaver, keyed by thread_id
(= session_id from the API request).  This gives each user session its own
isolated conversation + parameter-collection context across turns.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import CopilotState
from app.graph.nodes import classify_node, validate_node, execute_node, respond_node


# ── Routing functions ────────────────────────────────────────────────────────

def _route_classify(state: CopilotState) -> str:
    """After classify: go to validate if we have an intent, else respond."""
    return "validate" if state.get("current_intent") else "respond"


def _route_validate(state: CopilotState) -> str:
    """
    After validate:
      - Missing fields OR execution_result already set to error → respond
      - All params clean and no error             → execute
    """
    if state.get("missing_fields"):
        return "respond"
    result = state.get("execution_result") or {}
    if result.get("status") == "error":
        return "respond"
    return "execute"


# ── Graph construction ───────────────────────────────────────────────────────

def build_graph():
    builder = StateGraph(CopilotState)

    builder.add_node("classify", classify_node)
    builder.add_node("validate", validate_node)
    builder.add_node("execute",  execute_node)
    builder.add_node("respond",  respond_node)

    builder.add_edge(START, "classify")

    builder.add_conditional_edges(
        "classify",
        _route_classify,
        {"validate": "validate", "respond": "respond"},
    )

    builder.add_conditional_edges(
        "validate",
        _route_validate,
        {"execute": "execute", "respond": "respond"},
    )

    builder.add_edge("execute", "respond")
    builder.add_edge("respond", END)

    # MemorySaver persists state per thread_id between API calls.
    # Swap to SqliteSaver / PostgresSaver for production persistence.
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)


# Singleton — import this in main.py and anywhere else that needs it.
graph = build_graph()
