"""
CopilotState — the single source of truth flowing through every graph node.

Fields split into three concerns:
  1. messages        — full conversation history (accumulated by add_messages)
  2. tasks           — queue of tasks to process (reset in classify)
  3. pending_* /
     partial_params /
     missing_fields  — multi-turn context (persist across turns via MemorySaver)
  4. execution_result — output from execute_node
  5. completed_results - results accumulated from all tasks
  6. response_*      — final answer written by respond_node, read by main.py
"""

from typing import Annotated, Dict, List, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class CopilotState(TypedDict):
    # ── Conversation history ─────────────────────────────────────────────────
    # add_messages annotation: new messages are APPENDED, never replaced.
    # This gives the LLM full conversation context on every turn.
    messages: Annotated[list, add_messages]

    # ── Task Queue ───────────────────────────────────────────────────────────
    tasks: List[Dict]               # list of tasks. Each task: {"intent": ..., "group": ..., "action": ..., "params": ...}

    # ── Active task multi-turn context (for tasks[0]) ────────────────────────
    partial_params: Dict            # params collected so far for the active task
    missing_fields: List[str]       # fields still required for the active task

    # ── Execution results ────────────────────────────────────────────────────
    completed_results: List[Dict]   # Results for successfully completed tasks in the current batch
    execution_result: Optional[Dict] # Kept for single-step errors during execute

    # ── Final response (set by respond_node, consumed by main.py) ───────────
    response_status:  str   # "success" | "error" | "need_input" | "partial_success"
    response_message: str
    response_details: Dict
