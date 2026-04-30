"""
CopilotState — the single source of truth flowing through every graph node.

Fields split into three concerns:
  1. messages        — full conversation history (accumulated by add_messages)
  2. current_*       — data extracted from THIS turn (reset each turn in classify)
  3. pending_* /
     partial_params /
     missing_fields  — multi-turn context (persist across turns via MemorySaver)
  4. execution_result — output from execute_node
  5. response_*      — final answer written by respond_node, read by main.py
"""

from typing import Annotated, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class CopilotState(TypedDict):
    # ── Conversation history ─────────────────────────────────────────────────
    # add_messages annotation: new messages are APPENDED, never replaced.
    # This gives the LLM full conversation context on every turn.
    messages: Annotated[list, add_messages]

    # ── Current-turn data (set fresh by classify_node each turn) ─────────────
    current_intent: Optional[str]   # e.g. "add_user"
    current_group:  Optional[str]   # e.g. "users"
    current_action: Optional[str]   # e.g. "set"
    current_params: Dict            # normalised API-hyphen params from LLM

    # ── Multi-turn context (persisted by MemorySaver between turns) ──────────
    pending_intent: Optional[str]   # intent still awaiting missing params
    pending_group:  Optional[str]
    pending_action: Optional[str]
    partial_params: Dict            # params collected so far (hyphen-named)
    missing_fields: List[str]       # fields still required for pending_intent

    # ── Execution result (set by execute_node) ───────────────────────────────
    execution_result: Optional[Dict]

    # ── Final response (set by respond_node, consumed by main.py) ───────────
    response_status:  str   # "success" | "error" | "need_input" | "partial_success"
    response_message: str
    response_details: Dict
