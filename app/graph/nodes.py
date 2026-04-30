"""
Graph nodes — each function transforms CopilotState and returns a partial update.

Pipeline:
  classify_node → validate_node → execute_node → respond_node

classify  : LLM tool-calling extracts intent + params.
            If LLM returns no tool call and there is a pending intent,
            treats the user's message as a continuation answer.
validate  : Merges partial context with current params, checks schema
            required fields, validates values.
execute   : Builds device URL and calls the API (mock or real).
respond   : Formats the final ChatResponse fields.
"""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from app.graph.state import CopilotState
from app.llm.tools import ALL_TOOLS, TOOL_TO_GROUP_ACTION, normalise_params, mock_classify
from app.schemas.registry import schema_registry
from app.core.question_engine import generate_question
from app.services.api_builder import build_url
from app.services.device_api import call_device_api
from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, USE_MOCK, DEBUG_MODE
from app.exceptions import CoSecException
from app.logger import logger


SYSTEM_PROMPT = """\
You are the intent classification engine for CoSec — a biometric access control system.
Your ONLY job: read the user's message and call the correct tool(s) with every parameter you can extract.

RULES
1. Always call a tool when you detect any access-control intent — even with zero parameters extracted.
   Missing required fields are collected from the user automatically afterwards.
2. Call multiple tools when the message contains multiple operations (e.g. "add user AND set finger count").
3. Never respond in text. Only tool calls, or silence for completely off-topic input.
4. Stay silent ONLY when the message has zero relevance to access control (pure greetings, random text, etc.).

━━━ TOOL SELECTION — map natural language to the correct tool ━━━

USERS
  add_user      → "add / create / register / new user / enroll new employee"
  update_user   → "update / edit / change / rename / modify user"
  delete_user   → "delete / remove / deactivate / erase user"
  get_user      → "get / show / find / fetch / look up / retrieve user info"

ENROLL OPTIONS (biometric enrollment — fingerprint, palm, card)
  get_enroll_options         → "get/show enroll options", "what is the finger count"
  set_enroll_options         → "set/change/update enroll options", "set finger count to N"
  get_default_enroll_options → "get/show default enroll settings", "factory enroll config"
  set_default_enroll_options → "set/restore default enroll options"

ACCESS SETTINGS (work hours / time schedule)
  get_access_setting         → "get access settings", "show work hours", "what time does work start/end"
  set_access_setting         → "set access", "change work hours", "update start/end time to HH:MM"
  get_default_access_setting → "get/show default access settings"
  set_default_access_setting → "set/restore default access settings"

PANEL DETAILS (device summary counts)
  get_panel_details → "panel details", "device summary/info", "how many users/doors/alarms on the panel"

DOOR CONFIGURATION
  ⚠️  KEY DISAMBIGUATION: "set/configure/update/change door" = set_panel_door_config (WRITE operation)
                          "get/show/fetch/read door" = get_panel_door_config (READ operation)
  "set door configuration"      → set_panel_door_config  (NOT get!)
  "configure door N"            → set_panel_door_config
  "update door settings"        → set_panel_door_config
  "change door name/IP/type"    → set_panel_door_config
  "show/get/fetch door config"  → get_panel_door_config
  "what are door settings"      → get_panel_door_config
  get_default_panel_door_config → "get/show default door config"
  set_default_panel_door_config → "set/restore/change default door config"

━━━ PARAMETER EXTRACTION RULES ━━━

Names & IDs
  "add user Jay with id 5"   → name="Jay",  user_id="5"
  "delete user 7"            → user_id="7"
  "update user 3 to Alice"   → user_id="3", name="Alice"

Time — ALWAYS split into separate HH and MM fields. Convert 12-hour to 24-hour.
  "9:00" / "9 00" / "9am" / "9 o'clock" → hh="9",  mm="0"
  "9:30" / "09:30 AM"                   → hh="9",  mm="30"
  "5:30 PM" / "17:30"                   → hh="17", mm="30"
  "start at 9"       → work_start_hh="9",  work_start_mm="0"
  "end at 5 PM"      → work_end_hh="17",   work_end_mm="0"
  "9 to 17"          → work_start_hh="9",  work_start_mm="0", work_end_hh="17",  work_end_mm="0"
  "9 AM to 5 PM"     → work_start_hh="9",  work_start_mm="0", work_end_hh="17",  work_end_mm="0"
  12→24h rule: PM adds 12 (except 12 PM stays 12). 12 AM = 0.

Weekday numbers:  Sunday=0  Monday=1  Tuesday=2  Wednesday=3  Thursday=4  Friday=5  Saturday=6

Enroll
  "3 fingers" / "finger count 3"    → enroll_finger_count="3"
  "dual mode" / "dual template"     → enroll_mode="1"
  "single mode" / "single template" → enroll_mode="0"

Door
  "door 2" / "door id 2"  → door_id="2"
  "name MainGate"          → door_name="MainGate"
"""


# ── LLM singleton (lazy, avoids import-time errors when no key) ──────────────

_llm_with_tools = None

def _get_llm():
    global _llm_with_tools
    if _llm_with_tools is None:
        base = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0,
            timeout=OPENAI_TIMEOUT,
        )
        _llm_with_tools = base.bind_tools(ALL_TOOLS)
    return _llm_with_tools


# ── Keyword fallback (used when LLM returns no / unknown tool calls) ─────────

def _keyword_fallback(user_text: str) -> list:
    """
    Run mock_classify on the user message as a safety net.
    Supports multiple intents separated by 'and'.
    Also handles vague queries like 'get configuration' → panel details.
    Returns a list of task dicts ready for the task queue, or [].
    """
    new_tasks = []
    parts = [p.strip() for p in user_text.lower().split(" and ")]
    for part in parts:
        tool_name, raw_params = mock_classify(part)
        if tool_name and tool_name in TOOL_TO_GROUP_ACTION:
            group, action = TOOL_TO_GROUP_ACTION[tool_name]
            new_tasks.append({
                "intent": tool_name,
                "group":  group,
                "action": action,
                "params": raw_params,
            })

    # ── Vague-query fallbacks when mock_classify has no match ─────────────────
    if not new_tasks:
        t = user_text.lower()
        # "get/show/fetch configuration" (no domain) → panel details overview
        if any(k in t for k in ("get", "show", "fetch", "read", "display")) and \
           any(k in t for k in ("config", "configuration", "setting", "settings", "info", "status", "details")):
            new_tasks.append({
                "intent": "get_panel_details",
                "group":  "panel-details",
                "action": "get",
                "params": {},
            })
            logger.info("Vague 'get' query resolved to get_panel_details")

    return new_tasks


# ── Node 1: classify ─────────────────────────────────────────────────────────

def classify_node(state: CopilotState) -> dict:
    """
    Classify the user's latest message.

    Priority order:
      1. LLM tool call detected        → new command(s), resets task queue
      2. No LLM tool call + tasks      → continuation: fill missing[0] with user's answer
      3. No LLM tool call, no tasks    → mock_classify fallback (keyword safety net)
      4. Neither LLM nor keyword match → unrecognised input
    """
    tasks           = state.get("tasks") or []
    missing_fields  = state.get("missing_fields") or []
    user_text       = state["messages"][-1].content if state.get("messages") else ""

    update: dict = {"execution_result": None}   # reset execution result each turn

    try:
        # ── Mock mode: use keyword classifier ──────────────────────────────
        if USE_MOCK and not OPENAI_API_KEY:
            # We'll support multiple parts separated by "and" in mock mode
            parts = [p.strip() for p in user_text.lower().split(" and ")]
            new_tasks = []
            for part in parts:
                tool_name, raw_params = mock_classify(part)
                if tool_name:
                    group, action = TOOL_TO_GROUP_ACTION[tool_name]
                    new_tasks.append({
                        "intent": tool_name,
                        "group": group,
                        "action": action,
                        "params": raw_params
                    })
            
            if new_tasks:
                update.update({
                    "tasks": new_tasks,
                    "partial_params": {}, # start fresh
                    "missing_fields": [],
                    "completed_results": [], # new batch
                })
                logger.info(f"[MOCK] classified tasks: {new_tasks}")
            elif tasks and missing_fields:
                field = missing_fields[0]
                new_partial = {**(state.get("partial_params") or {}), field: user_text}
                update.update({
                    "partial_params": new_partial,
                    "missing_fields": [],
                })
                logger.info(f"[MOCK] continuation: filling '{field}' = '{user_text}'")
            else:
                update.update(_unrecognised())
            return update

        # ── Real LLM tool calling ───────────────────────────────────────────
        # Keep only the most recent turns to prevent stale context from
        # causing inconsistent classification on repeated inputs.
        MAX_HISTORY = 10
        trimmed_history = list(state["messages"])[-MAX_HISTORY:]
        messages  = [SystemMessage(content=SYSTEM_PROMPT)] + trimmed_history
        response: AIMessage = _get_llm().invoke(messages)

        # Always add the LLM response to conversation history
        update["messages"] = [response]

        if response.tool_calls:
            # ── New commands ────────────────────────────────────────────────
            new_tasks = []
            tool_msgs = []
            for tc in response.tool_calls:
                tool_name = tc["name"]
                raw_args  = {k: v for k, v in tc["args"].items() if v is not None}
                normalised = normalise_params(raw_args)

                if tool_name not in TOOL_TO_GROUP_ACTION:
                    logger.warning(f"LLM called unknown tool: {tool_name}")
                    continue

                group, action = TOOL_TO_GROUP_ACTION[tool_name]
                new_tasks.append({
                    "intent": tool_name,
                    "group": group,
                    "action": action,
                    "params": normalised
                })
                tool_msgs.append(ToolMessage(
                    content="parameters extracted",
                    tool_call_id=tc.get("id", "0"),
                ))

            if not new_tasks:
                # LLM called only unknown tools — fall back to mock_classify
                new_tasks = _keyword_fallback(user_text)
                if not new_tasks:
                    update.update(_unrecognised())
                    return update
                logger.info(f"LLM unknown-tool fallback → mock_classify: {[t['intent'] for t in new_tasks]}")
            else:
                # Close the tool-call loop in message history
                update["messages"].extend(tool_msgs)

            logger.info(f"Tool calls extracted {len(new_tasks)} tasks")

            # Check if this is a continuation where the LLM just re-issued the pending tool call
            if tasks and missing_fields and len(new_tasks) == 1 and new_tasks[0]["intent"] == tasks[0]["intent"]:
                logger.info(f"LLM re-issued pending task {tasks[0]['intent']}. Merging params and continuing queue.")
                merged_params = {
                    **(state.get("partial_params") or {}),
                    **new_tasks[0]["params"]
                }
                update.update({
                    "partial_params": merged_params,
                    "missing_fields": [],
                    # We do NOT touch tasks or completed_results, so the queue continues!
                })
            else:
                # Completely new command (or user changed their mind)
                update.update({
                    "tasks": new_tasks,
                    "partial_params": {}, # Start fresh for new commands
                    "missing_fields": [],
                    "completed_results": [], # New batch
                })

        elif tasks and missing_fields:
            # ── Continuation: user answered the pending question ────────────
            field       = missing_fields[0]
            new_partial = {**(state.get("partial_params") or {}), field: user_text}

            logger.info(f"Continuation: filling '{field}' = '{user_text}'")

            update.update({
                "partial_params": new_partial,
                "missing_fields": [],
            })

        else:
            # ── LLM returned no tool call — try mock_classify as safety net ─
            new_tasks = _keyword_fallback(user_text)
            if new_tasks:
                logger.info(f"LLM no-tool fallback → mock_classify: {[t['intent'] for t in new_tasks]}")
                update.update({
                    "tasks": new_tasks,
                    "partial_params": {},
                    "missing_fields": [],
                    "completed_results": [],
                })
            else:
                logger.info("No tool call and no pending state — input not recognised")
                update.update(_unrecognised())

    except Exception as e:
        logger.error(f"classify_node error: {e}", exc_info=DEBUG_MODE)
        update.update(_unrecognised())

    return update


# ── Node 2: validate ─────────────────────────────────────────────────────────

def validate_node(state: CopilotState) -> dict:
    """
    Validate tasks[0] against schema.
    """
    tasks = state.get("tasks") or []
    if not tasks:
        return {} # Should not happen if routing is correct
    
    current_task = tasks[0]
    group  = current_task["group"]
    action = current_task["action"]

    try:
        schema   = schema_registry.get(group)
        required = schema.get_required_fields(action)
        optional = schema.get_optional_fields(action)
        all_valid = set(required + optional)

        # Merge: partial from previous turns + fresh params from this turn
        merged = {
            **(state.get("partial_params") or {}),
            **(current_task.get("params") or {}),
        }

        # Strip fields the schema doesn't know (LLM or user may send extras)
        merged = {k: v for k, v in merged.items() if k in all_valid}

        missing = [f for f in required if f not in merged]

        if missing:
            logger.info(f"Missing required fields for {group}.{action}: {missing}")
            return {
                "partial_params":  merged,
                "missing_fields":  missing,
                "execution_result": None,
            }

        # All required fields present — validate values
        is_valid, result = schema.validate_parameters(action, merged)
        if not is_valid:
            logger.warning(f"Value validation failed for {group}.{action}: {result}")
            return {
                "execution_result": {
                    "status": "error",
                    "error":  f"Invalid parameter values: {result.get('missing', result)}",
                    "code":   "VALIDATION_ERROR",
                },
                "missing_fields": [],
            }

        # Use the schema-cleaned params (unknown fields stripped, values cast)
        clean = result.get("params", merged)
        logger.info(f"Validation passed for {group}.{action}: {clean}")

        return {
            "partial_params": clean,
            "missing_fields": [],
        }

    except Exception as e:
        logger.error(f"validate_node error: {e}", exc_info=DEBUG_MODE)
        return {
            "execution_result": {
                "status": "error",
                "error":  str(e),
                "code":   "VALIDATE_NODE_ERROR",
            },
            "missing_fields": [],
        }


# ── Node 3: execute ──────────────────────────────────────────────────────────

def execute_node(state: CopilotState) -> dict:
    """
    Execute tasks[0].
    """
    tasks = state.get("tasks") or []
    if not tasks:
        return {}
    
    current_task = tasks[0]
    group  = current_task["group"]
    action = current_task["action"]
    params = state.get("partial_params") or {}

    completed_results = list(state.get("completed_results") or [])

    try:
        url = build_url(group, {"action": action, **params})
        logger.info(f"Executing: {url}")

        if USE_MOCK:
            result = {
                "status":  "success",
                "url":     url,
                "mock":    True,
                "group":   group,
                "action":  action,
                "message": f"✅ Mock executed: {params}",
                "response": {"status": "success", "mock_data": params},
            }
        else:
            resp = call_device_api(url)
            result = {
                "status":        "success",
                "url":           resp.get("url", url),
                "mock":          False,
                "group":         group,
                "action":        action,
                "message":       "✅ Command executed successfully",
                "response":      resp.get("data"),
                "device_status": resp.get("status_code"),
            }

        completed_results.append(result)
        
        return {
            "execution_result": result, 
            "completed_results": completed_results,
            "tasks": tasks[1:], # Pop the completed task
            "partial_params": {}, # Clear for next task
            "missing_fields": [],
        }

    except CoSecException as e:
        logger.error(f"execute_node CoSec error: {e.message}")
        return {
            "execution_result": {
                "status":  "error",
                "error":   e.message,
                "code":    e.code,
                "details": e.details,
            },
            "tasks": [], # Abort remaining
            "partial_params": {},
            "missing_fields": [],
        }
    except Exception as e:
        logger.error(f"execute_node unexpected error: {e}", exc_info=DEBUG_MODE)
        return {
            "execution_result": {
                "status": "error",
                "error":  str(e),
                "code":   "EXECUTION_ERROR",
            },
            "tasks": [], # Abort remaining
            "partial_params": {},
            "missing_fields": [],
        }


# ── Node 4: respond ──────────────────────────────────────────────────────────

def respond_node(state: CopilotState) -> dict:
    """
    Format response using completed_results and any errors/missing fields.
    """
    tasks = state.get("tasks") or []
    missing = state.get("missing_fields") or []
    result  = state.get("execution_result")
    completed = state.get("completed_results") or []

    # ── 1. Unrecognised ──────────────────────────────────────────────────────
    if not tasks and not missing and not result and not completed:
        return {
            "response_status":  "error",
            "response_message": (
                "I couldn't understand that request. Please be more specific. Try:\n"
                "• Users → \"add user Jay with id 5\", \"delete user 3\", \"get user 10\"\n"
                "• Door config → \"set door 1 configuration\", \"get door 2 config\"\n"
                "• Enroll → \"set finger count to 3\", \"get enroll options\"\n"
                "• Access → \"set work start at 9:00\", \"get access settings\"\n"
                "• Panel → \"get panel details\""
            ),
            "response_details": {"reason": "no_intent_detected"},
        }

    # ── 2. Need more input ───────────────────────────────────────────────────
    if missing:
        question = generate_question(missing)
        return {
            "response_status":  "need_input",
            "response_message": question,
            "response_details": {
                "missing_fields": missing,
                "partial":        state.get("partial_params") or {},
            },
        }

    # ── 3. Execution error ───────────────────────────────────────────────────
    if result and result.get("status") == "error":
        msg = f"Error: {result.get('error', 'Execution failed')}"
        if completed:
            msg = f"Partially completed before error. {msg}"
            
        return {
            "response_status":  "error",
            "response_message": msg,
            "response_details": {
                "error_code": result.get("code"),
                "details":    result.get("details") or {},
                "errors":     [result],
                "successes":  completed,
            },
        }

    # ── 4. Success ───────────────────────────────────────────────────────────
    if completed:
        messages = [r.get("message", "✅ Command executed successfully") for r in completed]
        
        # Combine messages
        if len(completed) > 1:
            combined_message = f"✅ Successfully executed {len(completed)} tasks:\n" + "\n".join(f"- {m.replace('✅ ', '')}" for m in messages)
        else:
            combined_message = messages[0]

        return {
            "response_status":  "success",
            "response_message": combined_message,
            "response_details": {
                "successes":      completed,
                "missing_fields": [],
                "summary":        {"total_tasks": len(completed), "successful": len(completed), "failed": 0},
            },
        }

    # ── Fallback ─────────────────────────────────────────────────────────────
    return {
        "response_status":  "error",
        "response_message": "Unexpected internal state. Please try again.",
        "response_details": {},
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _unrecognised() -> dict:
    """Return the state fragment for an unrecognised / no-intent turn."""
    return {
        "tasks": [],
        "missing_fields": [],
        "partial_params": {},
        "completed_results": [],
        "execution_result": None,
    }
