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


SYSTEM_PROMPT = (
    "You are an intent detection engine for a COSEC security access control system.\n"
    "When the user gives a command, call the SINGLE most appropriate tool with every "
    "parameter you can extract from their message.\n"
    "If some parameters are missing, still call the tool with what you have — "
    "the system will ask the user for the rest.\n"
    "If the input is ambiguous or not related to access control, do NOT call any tool.\n"
    "Never explain your reasoning — only make tool calls or stay silent."
)


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


# ── Node 1: classify ─────────────────────────────────────────────────────────

def classify_node(state: CopilotState) -> dict:
    """
    Classify the user's latest message.

    Priority order:
      1. LLM tool call detected  → new (or same-intent) command
      2. No tool call + pending  → continuation: fill missing[0] with user answer
      3. Neither                 → unrecognised input

    Always-LLM-first ensures a new command (e.g. "add user Ravi") overrides
    a pending follow-up from a previous turn.
    """
    pending_intent = state.get("pending_intent")
    missing_fields  = state.get("missing_fields") or []
    user_text       = state["messages"][-1].content if state.get("messages") else ""

    update: dict = {"execution_result": None}   # reset execution result each turn

    try:
        # ── Mock mode: use keyword classifier ──────────────────────────────
        if USE_MOCK and not OPENAI_API_KEY:
            tool_name, raw_params = mock_classify(user_text)
            if tool_name:
                group, action = TOOL_TO_GROUP_ACTION[tool_name]
                same_intent   = (pending_intent == tool_name)
                update.update({
                    "current_intent": tool_name,
                    "current_group":  group,
                    "current_action": action,
                    "current_params": raw_params,
                    # Keep partial only when the LLM is continuing the SAME intent
                    "partial_params": state.get("partial_params") or {} if same_intent else {},
                    "pending_intent": None,
                    "pending_group":  None,
                    "pending_action": None,
                    "missing_fields": [],
                })
                logger.info(f"[MOCK] classified: {tool_name} params={raw_params}")
            elif pending_intent and missing_fields:
                field = missing_fields[0]
                new_partial = {**(state.get("partial_params") or {}), field: user_text}
                update.update({
                    "current_intent": pending_intent,
                    "current_group":  state.get("pending_group"),
                    "current_action": state.get("pending_action"),
                    "current_params": {field: user_text},
                    "partial_params": new_partial,
                    "missing_fields": [],
                })
                logger.info(f"[MOCK] continuation: filling '{field}' = '{user_text}'")
            else:
                update.update(_unrecognised())
            return update

        # ── Real LLM tool calling ───────────────────────────────────────────
        messages  = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
        response: AIMessage = _get_llm().invoke(messages)

        # Always add the LLM response to conversation history
        update["messages"] = [response]

        if response.tool_calls:
            # ── New or same-intent command ──────────────────────────────────
            tc        = response.tool_calls[0]
            tool_name = tc["name"]
            raw_args  = {k: v for k, v in tc["args"].items() if v is not None}
            normalised = normalise_params(raw_args)

            if tool_name not in TOOL_TO_GROUP_ACTION:
                logger.warning(f"LLM called unknown tool: {tool_name}")
                update.update(_unrecognised())
                return update

            group, action = TOOL_TO_GROUP_ACTION[tool_name]
            same_intent   = (pending_intent == tool_name)

            logger.info(f"Tool call: {tool_name} group={group} action={action} params={normalised}")

            # Add a ToolMessage to close the tool-call loop in the conversation
            # so models that require it stay coherent across turns.
            tool_msg = ToolMessage(
                content="parameters extracted",
                tool_call_id=tc.get("id", "0"),
            )
            update["messages"] = [response, tool_msg]

            update.update({
                "current_intent": tool_name,
                "current_group":  group,
                "current_action": action,
                "current_params": normalised,
                # Keep old partial only when the LLM is continuing the same intent
                # (e.g. it used conversation context to fill one more field).
                # For a different intent, start fresh.
                "partial_params": state.get("partial_params") or {} if same_intent else {},
                "pending_intent": None,
                "pending_group":  None,
                "pending_action": None,
                "missing_fields": [],
            })

        elif pending_intent and missing_fields:
            # ── Continuation: user answered the pending question ────────────
            field       = missing_fields[0]
            new_partial = {**(state.get("partial_params") or {}), field: user_text}

            logger.info(f"Continuation: filling '{field}' = '{user_text}'")

            update.update({
                "current_intent": pending_intent,
                "current_group":  state.get("pending_group"),
                "current_action": state.get("pending_action"),
                "current_params": {field: user_text},
                "partial_params": new_partial,
                "missing_fields": [],
            })

        else:
            # ── Unrecognised ────────────────────────────────────────────────
            logger.info("No tool call and no pending state — input not recognised")
            update.update(_unrecognised())

    except Exception as e:
        logger.error(f"classify_node error: {e}", exc_info=DEBUG_MODE)
        update.update(_unrecognised())

    return update


# ── Node 2: validate ─────────────────────────────────────────────────────────

def validate_node(state: CopilotState) -> dict:
    """
    Merge params collected across turns and validate against the schema.

    partial_params  = everything collected from previous turns
    current_params  = what was just extracted in this turn
    merged          = partial ∪ current  (current wins on conflicts)

    Sets missing_fields + pending_* if required fields are still absent.
    Clears them and stores clean merged params if all requirements met.
    """
    group  = state.get("current_group")
    action = state.get("current_action")

    try:
        schema   = schema_registry.get(group)
        required = schema.get_required_fields(action)
        optional = schema.get_optional_fields(action)
        all_valid = set(required + optional)

        # Merge: partial from previous turns + fresh params from this turn
        merged = {
            **(state.get("partial_params") or {}),
            **(state.get("current_params") or {}),
        }

        # Strip fields the schema doesn't know (LLM or user may send extras)
        merged = {k: v for k, v in merged.items() if k in all_valid}

        missing = [f for f in required if f not in merged]

        if missing:
            logger.info(f"Missing required fields for {group}.{action}: {missing}")
            return {
                "partial_params":  merged,
                "missing_fields":  missing,
                "pending_intent":  state.get("current_intent"),
                "pending_group":   group,
                "pending_action":  action,
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
    Build the device API URL and call it (real device or mock).
    Clears all pending / partial state on success so the next command starts clean.
    """
    group  = state.get("current_group")
    action = state.get("current_action")
    params = state.get("partial_params") or {}

    _clear_pending = {
        "pending_intent": None,
        "pending_group":  None,
        "pending_action": None,
        "partial_params": {},
        "missing_fields": [],
    }

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

        return {"execution_result": result, **_clear_pending}

    except CoSecException as e:
        logger.error(f"execute_node CoSec error: {e.message}")
        return {
            "execution_result": {
                "status":  "error",
                "error":   e.message,
                "code":    e.code,
                "details": e.details,
            },
            **_clear_pending,
        }
    except Exception as e:
        logger.error(f"execute_node unexpected error: {e}", exc_info=DEBUG_MODE)
        return {
            "execution_result": {
                "status": "error",
                "error":  str(e),
                "code":   "EXECUTION_ERROR",
            },
            **_clear_pending,
        }


# ── Node 4: respond ──────────────────────────────────────────────────────────

def respond_node(state: CopilotState) -> dict:
    """
    Build the final response fields that main.py reads from the state.

    Four cases, in priority order:
      1. No intent detected      → error / unrecognised
      2. Missing required fields → need_input + question
      3. Execution error         → error + details
      4. Execution success       → success + URL + mock flag
    """
    intent  = state.get("current_intent")
    missing = state.get("missing_fields") or []
    result  = state.get("execution_result")

    # ── 1. Unrecognised ──────────────────────────────────────────────────────
    if not intent:
        return {
            "response_status":  "error",
            "response_message": "Could not understand your request. Please try again with a clearer command.",
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
        return {
            "response_status":  "error",
            "response_message": result.get("error", "Execution failed"),
            "response_details": {
                "error_code": result.get("code"),
                "details":    result.get("details") or {},
                "errors":     [result],
            },
        }

    # ── 4. Success ───────────────────────────────────────────────────────────
    if result and result.get("status") == "success":
        success_details = {
            "url": result.get("url"),
            "mock": result.get("mock", False),
        }
        # Include device response if available (non-mock execution)
        device_response = result.get("response")
        http_status = result.get("device_status")
        
        if device_response:
            success_details["device_response"] = device_response
        if http_status:
            success_details["http_status"] = http_status
        
        # Format message with device response if available
        message = result.get("message", "✅ Command executed successfully")
        if device_response:
            # Limit response to 500 chars for display, add ellipsis if longer
            response_preview = device_response[:500] if len(device_response) > 500 else device_response
            if len(device_response) > 500:
                response_preview += "..."
            message += f"\n\n**Device Response:**\n{response_preview}"
        if http_status:
            message += f"\n\n**HTTP Status:** {http_status}"
        
        return {
            "response_status":  "success",
            "response_message": message,
            "response_details": {
                "successes":      [success_details],
                "missing_fields": [],
                "summary":        {"total_tasks": 1, "successful": 1, "failed": 0},
            },
        }

    # ── Fallback (should not reach here in normal operation) ─────────────────
    return {
        "response_status":  "error",
        "response_message": "Unexpected internal state. Please try again.",
        "response_details": {},
    }


# ── Helpers ──────────────────────────────────────────────────────────────────

def _unrecognised() -> dict:
    """Return the state fragment for an unrecognised / no-intent turn."""
    return {
        "current_intent": None,
        "current_group":  None,
        "current_action": None,
        "current_params": {},
    }
