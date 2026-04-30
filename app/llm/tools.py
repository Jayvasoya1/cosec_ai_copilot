"""
Tool definitions for LLM tool-calling.

Each tool = one intent the user can express.
Tools do NOT execute anything — they are purely schema declarations.
The LLM fills in what it can from the user's message; missing required fields
are detected later in validate_node and asked from the user there.

All params are Optional so the LLM can make a partial call when the user
only provides some values (e.g. "set finger count to 5" → only enroll_finger_count).
The schema-level required-field check happens in validate_node, not here.
"""

from typing import Optional
from langchain_core.tools import tool


# ── Param name normalisation ─────────────────────────────────────────────────
# Maps Python underscore names (tool args) → API hyphen names (device params).
# Any name not in this map passes through as-is.

PARAM_MAP: dict = {
    # user
    "user_id":            "user-id",
    "ref_user_id":        "ref-user-id",
    "user_active":        "user-active",
    "user_pin":           "user-pin",
    "user_group":         "user-group",
    "bypass_finger":      "by-pass-finger",
    "bypass_palm":        "by-pass-palm",
    "bypass_face":        "by-pass-face",
    "restrict_access":    "restrict-access",
    "route_id":           "route-id",
    "validity_enable":    "validity-enable",
    "validity_date_dd":   "validity-date-dd",
    "validity_date_mm":   "validity-date-mm",
    "validity_date_yyyy": "validity-date-yyyy",
    "validity_time_hh":   "validity-time-hh",
    "validity_time_mm":   "validity-time-mm",
    # enroll-options
    "enroll_finger_count": "enroll-finger-count",
    "enroll_palm_count":   "enroll-palm-count",
    "enroll_card_count":   "enroll-card-count",
    "enroll_on_device":    "enroll-on-device",
    "enroll_using":        "enroll-using",
    "enroll_mode":         "enroll-mode",
    # access-setting
    "week_day":      "week-day",
    "work_start_hh": "work-start-hh",
    "work_start_mm": "work-start-mm",
    "work_end_hh":   "work-end-hh",
    "work_end_mm":   "work-end-mm",
    # panel-details
    "io_link": "io-link",
    # common
    "id_format": "format",
}


def normalise_params(raw: dict) -> dict:
    """Convert tool arg names (underscore) to API param names (hyphen), drop None values."""
    return {PARAM_MAP.get(k, k): v for k, v in raw.items() if v is not None}


# ── Intent → (group, action) routing table ───────────────────────────────────
# Tells the graph which schema group and which action to use for each tool.

TOOL_TO_GROUP_ACTION: dict = {
    # users
    "add_user":    ("users", "set"),
    "update_user": ("users", "set"),
    "delete_user": ("users", "delete"),
    "get_user":    ("users", "get"),
    # enroll-options
    "get_enroll_options":         ("enroll-options", "get"),
    "set_enroll_options":         ("enroll-options", "set"),
    "get_default_enroll_options": ("enroll-options", "getdefault"),
    "set_default_enroll_options": ("enroll-options", "setdefault"),
    # access-setting
    "get_access_setting":         ("access-setting", "get"),
    "set_access_setting":         ("access-setting", "set"),
    "get_default_access_setting": ("access-setting", "getdefault"),
    "set_default_access_setting": ("access-setting", "setdefault"),
    # panel-details
    "get_panel_details": ("panel-details", "get"),
}


# ── Tool definitions ─────────────────────────────────────────────────────────
# Return value doesn't matter — the tool body never runs in this pipeline.
# The LLM only sees the function signature + docstring to decide which tool
# to call and what arguments to fill.

@tool
def add_user(
    user_id: Optional[str] = None,
    name:    Optional[str] = None,
) -> str:
    """Add a new user to the COSEC access control system."""
    return "dispatched"


@tool
def update_user(
    user_id: Optional[str] = None,
    name:    Optional[str] = None,
) -> str:
    """Update an existing user's name or details in the COSEC system."""
    return "dispatched"


@tool
def delete_user(
    user_id: Optional[str] = None,
) -> str:
    """Delete (remove) a user from the COSEC system by their user ID."""
    return "dispatched"


@tool
def get_user(
    user_id: Optional[str] = None,
) -> str:
    """Retrieve user information from the COSEC system."""
    return "dispatched"


@tool
def get_enroll_options(
    format: Optional[str] = None,
) -> str:
    """Get the current enrollment configuration options from the device."""
    return "dispatched"


@tool
def set_enroll_options(
    enroll_finger_count: Optional[str] = None,
    enroll_palm_count:   Optional[str] = None,
    enroll_card_count:   Optional[str] = None,
    enroll_on_device:    Optional[str] = None,
    enroll_using:        Optional[str] = None,
    enroll_mode:         Optional[str] = None,
    format:              Optional[str] = None,
) -> str:
    """Set enrollment options on the COSEC device (finger count, palm count, card count, mode, etc.)."""
    return "dispatched"


@tool
def get_default_enroll_options(
    format: Optional[str] = None,
) -> str:
    """Get the factory-default enrollment configuration from the device."""
    return "dispatched"


@tool
def set_default_enroll_options(
    enroll_finger_count: Optional[str] = None,
    enroll_palm_count:   Optional[str] = None,
    enroll_card_count:   Optional[str] = None,
    enroll_on_device:    Optional[str] = None,
    enroll_using:        Optional[str] = None,
    enroll_mode:         Optional[str] = None,
) -> str:
    """Set the default enrollment options on the COSEC device."""
    return "dispatched"


@tool
def get_access_setting(
    week_day:      Optional[str] = None,
    work_start_hh: Optional[str] = None,
    work_start_mm: Optional[str] = None,
    work_end_hh:   Optional[str] = None,
    work_end_mm:   Optional[str] = None,
    format:        Optional[str] = None,
) -> str:
    """Get the current access time settings (work hours, week day) from the device."""
    return "dispatched"


@tool
def set_access_setting(
    week_day:      Optional[str] = None,
    work_start_hh: Optional[str] = None,
    work_start_mm: Optional[str] = None,
    work_end_hh:   Optional[str] = None,
    work_end_mm:   Optional[str] = None,
    format:        Optional[str] = None,
) -> str:
    """Set the access time settings (work start/end hours and minutes, week day) on the device."""
    return "dispatched"


@tool
def get_default_access_setting(
    format: Optional[str] = None,
) -> str:
    """Get the factory-default access time settings from the device."""
    return "dispatched"


@tool
def set_default_access_setting(
    week_day:      Optional[str] = None,
    work_start_hh: Optional[str] = None,
    work_start_mm: Optional[str] = None,
    work_end_hh:   Optional[str] = None,
    work_end_mm:   Optional[str] = None,
) -> str:
    """Set the default access time settings on the COSEC device."""
    return "dispatched"


@tool
def get_panel_details(
    user:    Optional[str] = None,
    door:    Optional[str] = None,
    alarm:   Optional[str] = None,
    io_link: Optional[str] = None,
    format:  Optional[str] = None,
) -> str:
    """Get panel summary counts: total users, doors, alarms, and IO-links on the device."""
    return "dispatched"


# ── Tool list exported to nodes.py ───────────────────────────────────────────

ALL_TOOLS = [
    add_user,
    update_user,
    delete_user,
    get_user,
    get_enroll_options,
    set_enroll_options,
    get_default_enroll_options,
    set_default_enroll_options,
    get_access_setting,
    set_access_setting,
    get_default_access_setting,
    set_default_access_setting,
    get_panel_details,
]


# ── Mock classifier (used when USE_MOCK=True and no API key) ─────────────────

def mock_classify(text: str):
    """
    Keyword-based intent classifier used in mock mode (no OpenAI key needed).
    Returns (tool_name, normalised_params) or (None, {}) if unrecognised.
    """
    t = text.lower()
    parts = text.split()

    # ── panel details ──
    if "panel" in t and ("detail" in t or "summary" in t or "count" in t):
        params = {}
        if "user" in t:  params["user"]  = "1"
        if "door" in t:  params["door"]  = "1"
        if "alarm" in t: params["alarm"] = "1"
        if "io" in t:    params["io-link"] = "1"
        return "get_panel_details", params

    # ── enroll ──
    if "enroll" in t or "enrollment" in t:
        if "default" in t:
            if "set" in t:
                return "set_default_enroll_options", _extract_enroll_params(t, parts)
            return "get_default_enroll_options", {}
        if "set" in t:
            return "set_enroll_options", _extract_enroll_params(t, parts)
        return "get_enroll_options", {}

    # ── access setting ──
    if "access" in t and ("setting" in t or "time" in t or "hour" in t):
        if "default" in t:
            if "set" in t:
                return "set_default_access_setting", _extract_access_params(t, parts)
            return "get_default_access_setting", {}
        if "set" in t:
            return "set_access_setting", _extract_access_params(t, parts)
        return "get_access_setting", {}

    # ── users ──
    if "delete" in t or "remove" in t:
        if "user" in t:
            uid = next((p for p in parts if p.isdigit()), None)
            return "delete_user", {"user-id": uid} if uid else {}

    if "update" in t or "change" in t or "rename" in t:
        if "user" in t:
            params = _extract_user_params(parts)
            return "update_user", params

    if "add" in t or "create" in t or "new" in t:
        if "user" in t:
            params = _extract_user_params(parts)
            return "add_user", params

    if "get" in t or "show" in t or "find" in t or "list" in t:
        if "user" in t:
            uid = next((p for p in parts if p.isdigit()), None)
            return "get_user", {"user-id": uid} if uid else {}

    return None, {}


def _extract_user_params(parts: list) -> dict:
    params = {}
    for i, p in enumerate(parts):
        pl = p.lower()
        if pl in ("user", "add", "create", "new") and i + 1 < len(parts):
            candidate = parts[i + 1]
            if not candidate.isdigit() and candidate.lower() not in ("with", "id", "user"):
                params["name"] = candidate
        if pl in ("id", "user-id") and i + 1 < len(parts) and parts[i + 1].isdigit():
            params["user-id"] = parts[i + 1]
        if p.isdigit() and "user-id" not in params:
            params["user-id"] = p
    return params


def _extract_enroll_params(t: str, parts: list) -> dict:
    params = {}
    for i, p in enumerate(parts):
        if p.isdigit():
            if "finger" in t:
                params["enroll-finger-count"] = p
            elif "palm" in t:
                params["enroll-palm-count"] = p
            elif "card" in t:
                params["enroll-card-count"] = p
            elif "mode" in t:
                params["enroll-mode"] = p
    if "dual" in t:
        params["enroll-mode"] = "1"
    if "single" in t:
        params["enroll-mode"] = "0"
    return params


def _extract_access_params(t: str, parts: list) -> dict:
    params = {}
    nums = [p for p in parts if p.isdigit()]
    if "start" in t and len(nums) >= 2:
        params["work-start-hh"] = nums[0]
        params["work-start-mm"] = nums[1]
    elif "end" in t and len(nums) >= 2:
        params["work-end-hh"] = nums[0]
        params["work-end-mm"] = nums[1]
    elif len(nums) >= 1:
        params["work-start-hh"] = nums[0]
        if len(nums) >= 2:
            params["work-start-mm"] = nums[1]
    return params
