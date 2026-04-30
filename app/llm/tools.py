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

import re
import difflib
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
    # enrolluser
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
    "door_id":             "pdid",
    "door_name":           "door-name",
    "door_type":           "door-type",
    "communication_type":  "communication-type",
    "ip_address":          "ip-address",
    "mac_address":         "mac-address",
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
    # enrolluser
    "enroll_user": ("enrolluser", "enroll"),
    # access-setting
    "get_access_setting":         ("access-setting", "get"),
    "set_access_setting":         ("access-setting", "set"),
    "get_default_access_setting": ("access-setting", "getdefault"),
    "set_default_access_setting": ("access-setting", "setdefault"),
    # panel-details
    "get_panel_details": ("panel-details", "get"),
    # panel-door-config
    "get_panel_door_config":         ("panel-door-config", "get"),
    "set_panel_door_config":         ("panel-door-config", "set"),
    "get_default_panel_door_config": ("panel-door-config", "getdefault"),
    "set_default_panel_door_config": ("panel-door-config", "setdefault"),
}


# ── Tool definitions ─────────────────────────────────────────────────────────
# Return value doesn't matter — the tool body never runs in this pipeline.
# The LLM only sees the function signature + docstring to decide which tool
# to call and what arguments to fill.

@tool
def add_user(
    user_id:     Optional[str] = None,
    name:        Optional[str] = None,
    user_pin:    Optional[str] = None,
    user_active: Optional[str] = None,
    user_group:  Optional[str] = None,
) -> str:
    """
    Add / create / register a new user in the COSEC access control system.
    Use for: "add user", "create user", "register user", "new user".
    Extract: user_id (numeric id), name (person's name), user_pin if given,
    user_active (1=active 0=inactive), user_group (group number 0-999).
    """
    return "dispatched"


@tool
def update_user(
    user_id:     Optional[str] = None,
    name:        Optional[str] = None,
    user_pin:    Optional[str] = None,
    user_active: Optional[str] = None,
    user_group:  Optional[str] = None,
) -> str:
    """
    Update / edit / modify an existing user's details in the COSEC system.
    Use for: "update user", "edit user", "change user name", "rename user", "modify user".
    Extract: user_id (which user), name (new name), and any other fields being changed.
    """
    return "dispatched"


@tool
def delete_user(
    user_id: Optional[str] = None,
) -> str:
    """
    Delete / remove / deactivate a user from the COSEC system.
    Use for: "delete user", "remove user", "deactivate user", "erase user".
    Extract: user_id from any number mentioned or "user <id>" pattern.
    """
    return "dispatched"


@tool
def get_user(
    user_id: Optional[str] = None,
    name:    Optional[str] = None,
) -> str:
    """
    Retrieve / fetch / look up user information from the COSEC system.
    Use for: "get user", "show user", "find user", "fetch user", "who is user", "look up user".
    Extract: user_id if a number is mentioned, name if searching by name.
    """
    return "dispatched"


@tool
def enroll_user(
    pdid: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Enroll a user on a specific panel door device.
    Use for: "enroll user", "enroll user on door N".
    Extract: pdid (door id or panel door id), user_id (user id).
    """
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
    """
    Get the current access time / work hour settings from the COSEC device.
    Use for: "get access settings", "show work hours", "what time does work start",
    "check timing", "what are the access times", "show schedule".
    """
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
    """
    Set / update / configure work hours and access time settings on the COSEC device.
    Use for: "set access", "change work hours", "update start time", "set work time to HH:MM",
    "set work start at 9", "change end time to 6 PM".
    Always split time into HH and MM fields. Convert 12-hour to 24-hour.
    "start at 9" → work_start_hh="9", work_start_mm="0".
    "end at 5 PM" → work_end_hh="17", work_end_mm="0".
    Weekday: Sunday=0 Monday=1 Tuesday=2 Wednesday=3 Thursday=4 Friday=5 Saturday=6.
    """
    return "dispatched"


@tool
def get_default_access_setting(
    format: Optional[str] = None,
) -> str:
    """
    Get the factory-default access time / work hour settings from the COSEC device.
    Use for: "get default access settings", "show default work hours", "factory access config".
    """
    return "dispatched"


@tool
def set_default_access_setting(
    week_day:      Optional[str] = None,
    work_start_hh: Optional[str] = None,
    work_start_mm: Optional[str] = None,
    work_end_hh:   Optional[str] = None,
    work_end_mm:   Optional[str] = None,
) -> str:
    """
    Set / restore the default access time settings on the COSEC device.
    Use for: "set default access settings", "restore default work hours".
    """
    return "dispatched"


@tool
def get_panel_details(
    user:    Optional[str] = None,
    door:    Optional[str] = None,
    alarm:   Optional[str] = None,
    io_link: Optional[str] = None,
    format:  Optional[str] = None,
) -> str:
    """
    Get panel / device summary: total users, doors, alarms, and IO-links on the COSEC device.
    Use for: "panel details", "panel info", "device summary", "how many users/doors/alarms",
    "panel status", "show device counts", "what is on the panel".
    """
    return "dispatched"


@tool
def get_panel_door_config(
    door_id: Optional[str] = None,
    format:  Optional[str] = None,
) -> str:
    """
    READ the current configuration of a specific door (READ-ONLY operation).
    Use for: "get door config", "show door N settings", "fetch door info",
    "what is door N config", "display door settings", "read door configuration".
    Do NOT use when the user says set, configure, update, or change a door.
    REQUIRED: door_id — extract from "door 2", "door id 2", or number after "door".
    """
    return "dispatched"


@tool
def set_panel_door_config(
    door_name:          Optional[str] = None,
    door_type:          Optional[str] = None,
    communication_type: Optional[str] = None,
    ip_address:         Optional[str] = None,
    mac_address:        Optional[str] = None,
    format:             Optional[str] = None,
) -> str:
    """
    WRITE / set / configure / update door settings on the COSEC device (WRITE operation).
    Use for: "set door config", "configure door", "set door configuration",
    "update door settings", "change door name/IP/type".
    ALWAYS use this (not get_panel_door_config) when the user says set/configure/update/change for a door.
    The door ID is auto-assigned — do NOT look for or extract a door ID for this tool.
    Extract: door_name ("name MainGate"), door_type ("type vega" or "argo face"),
    ip_address ("ip 192.168.1.50"), mac_address ("mac AA:BB:CC:DD:EE:FF").
    All 4 fields will be collected from the user if not provided in the message.
    """
    return "dispatched"


@tool
def get_default_panel_door_config(
    format: Optional[str] = None,
) -> str:
    """
    Get the default / factory door configuration settings from the COSEC device.
    Use for: "get default door config", "show default door settings", "factory door config".
    """
    return "dispatched"


@tool
def set_default_panel_door_config(
    door_name:          Optional[str] = None,
    door_type:          Optional[str] = None,
    communication_type: Optional[str] = None,
    ip_address:         Optional[str] = None,
    mac_address:        Optional[str] = None,
) -> str:
    """
    Set / restore the default door configuration values on the COSEC device.
    Use for: "set default door config", "restore default door settings".
    """
    return "dispatched"
# ── Tool list exported to nodes.py ───────────────────────────────────────────

ALL_TOOLS = [
    add_user,
    update_user,
    delete_user,
    get_user,
    enroll_user,
    get_access_setting,
    set_access_setting,
    get_default_access_setting,
    set_default_access_setting,
    get_panel_details,
    get_panel_door_config,
    set_panel_door_config,
    get_default_panel_door_config,
    set_default_panel_door_config,
]


# ── Time / weekday helpers ────────────────────────────────────────────────────

def _apply_ampm(hh: int, period: str) -> int:
    """Convert 12-hour hour + AM/PM to 24-hour integer."""
    if period == "pm" and hh != 12:
        return hh + 12
    if period == "am" and hh == 12:
        return 0
    return hh


def _parse_time(text: str):
    """
    Extract (hh_str, mm_str) from a time expression, or return None.
    Handles: "9:00", "09:30 AM", "5:30pm", "9am", "9 o'clock".
    """
    # HH:MM with optional AM/PM
    m = re.search(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b", text, re.IGNORECASE)
    if m:
        hh = _apply_ampm(int(m.group(1)), (m.group(3) or "").lower())
        return str(hh), str(int(m.group(2)))
    # H am/pm (no colon)
    m = re.search(r"\b(\d{1,2})\s*(am|pm)\b", text, re.IGNORECASE)
    if m:
        hh = _apply_ampm(int(m.group(1)), m.group(2).lower())
        return str(hh), "0"
    # "at N" / "from N" bare number in context
    m = re.search(r"\b(?:at|from|start|begin)\s+(\d{1,2})\b", text, re.IGNORECASE)
    if m:
        hh = int(m.group(1))
        if 0 <= hh <= 23:
            return str(hh), "0"
    return None


def _parse_weekday(text: str):
    """Map day name to COSEC week-day number string (Sunday=0 … Saturday=6)."""
    DAYS = {
        "sunday": "0", "sun": "0",
        "monday": "1", "mon": "1",
        "tuesday": "2", "tue": "2",
        "wednesday": "3", "wed": "3",
        "thursday": "4", "thu": "4",
        "friday": "5", "fri": "5",
        "saturday": "6", "sat": "6",
    }
    t = text.lower()
    for name, num in DAYS.items():
        if re.search(r"\b" + name + r"\b", t):
            return num
    return None


# ── Fuzzy spelling correction for mock classifier ────────────────────────────

# All domain keywords the classifier cares about — used to fuzzy-correct typos.
_DOMAIN_WORDS: frozenset = frozenset({
    # action verbs
    "add", "create", "register",
    "update", "edit", "modify", "change", "rename",
    "delete", "remove", "deactivate", "erase",
    "get", "show", "fetch", "retrieve", "list", "find", "display", "view", "check",
    "set", "configure", "restore", "reset",
    "enroll",
    # entities
    "user", "users", "employee", "staff", "member", "person", "worker",
    "door", "doors",
    "panel", "device",
    "access", "setting", "settings", "schedule",
    "config", "configuration",
    "detail", "details", "info", "information", "summary", "status",
    "default",
    # access-setting descriptors
    "work", "working", "start", "end", "hour", "hours", "time", "timing",
    "office", "shift", "morning", "evening",
    # weekdays
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    # door / enroll specifics
    "biometric", "face", "finger", "palm", "fingerprint",
    "address", "type", "name",
})

# Words after these are user-supplied values (names, IDs, IPs) — never correct them.
_VALUE_MARKERS: frozenset = frozenset({
    "name", "id", "ip", "mac", "with", "to", "as", "called", "named", "number",
})


def _normalise_input(text: str) -> str:
    """
    Fuzzy-correct spelling mistakes in domain keywords only.
    Numbers, IPs, MACs, names (after value markers), and short words are
    passed through unchanged — only intent/entity words are corrected.
    """
    words = text.lower().split()
    result: list[str] = []
    protect_next = False

    for word in words:
        # Previous word was a value marker → keep this word exactly as-is
        if protect_next:
            result.append(word)
            protect_next = False
            continue

        # Value marker → next word is user-provided, protect it
        if word in _VALUE_MARKERS:
            result.append(word)
            protect_next = True
            continue

        # Numeric tokens and IP/MAC-like strings → preserve
        if word.isdigit() or re.match(r'^[\d.:/]+$', word):
            result.append(word)
            continue

        # Very short words (1–2 chars) → too risky to correct
        if len(word) <= 2:
            result.append(word)
            continue

        # Already a known domain word → no correction needed
        if word in _DOMAIN_WORDS:
            result.append(word)
            continue

        # Fuzzy match against domain vocabulary (threshold 0.78)
        matches = difflib.get_close_matches(word, _DOMAIN_WORDS, n=1, cutoff=0.78)
        result.append(matches[0] if matches else word)

    return " ".join(result)


# ── Mock classifier (used when USE_MOCK=True and no API key) ─────────────────

def _word_in(text: str, *words) -> bool:
    """True if any word appears as a whole word (not substring) in text."""
    return any(bool(re.search(r"\b" + w + r"\b", text)) for w in words)


def mock_classify(text: str):
    """
    Keyword-based intent classifier for mock mode (no LLM key needed).
    Returns (tool_name, normalised_params) or (None, {}) if unrecognised.
    """
    t = _normalise_input(text)   # ← fuzzy-correct spelling mistakes first
    parts = text.split()         # ← keep original text for param value extraction

    # ── panel details (check before door to avoid conflict on "door") ─────────
    if "panel" in t and any(k in t for k in ("detail", "summary", "count", "info",
                                              "information", "status", "how many")):
        params = {}
        if "user" in t:    params["user"]    = "1"
        if "door" in t:    params["door"]    = "1"
        if "alarm" in t:   params["alarm"]   = "1"
        if "io" in t:      params["io-link"] = "1"
        return "get_panel_details", params

    # ── device / panel loose match (e.g. "show device info") ─────────────────
    if any(k in t for k in ("device", "panel")) and \
       any(k in t for k in ("info", "information", "summary", "status", "detail", "details", "count")):
        return "get_panel_details", {}

    # ── door config ───────────────────────────────────────────────────────────
    if "door" in t:
        _door_write = _word_in(t, "set", "update", "change", "configure", "edit",
                                "modify", "restore", "reset", "add", "create")
        _door_read  = (_word_in(t, "get", "show", "fetch", "read", "display",
                                 "find", "list", "view", "check", "what")
                       or any(k in t for k in ("config", "configuration", "setting",
                                               "settings", "info", "detail", "details")))

        if _door_write or _door_read:
            if "default" in t:
                if _door_write:
                    return "set_default_panel_door_config", _extract_door_params(parts)
                return "get_default_panel_door_config", {}
            if _door_write:
                return "set_panel_door_config", _extract_door_params(parts)
            return "get_panel_door_config", _extract_door_params(parts)

    # ── vague config ──────────────────────────────────────────────────────────
    if not "door" in t and any(k in t for k in ("config", "configuration", "setting", "settings")):
        if _word_in(t, "get", "show", "fetch", "read", "display", "what"):
            return "get_panel_door_config", {}
        if _word_in(t, "set", "update", "change", "edit", "modify", "add", "create"):
            return "set_panel_door_config", _extract_door_params(parts)

    # ── users ─────────────────────────────────────────────────────────────────
    _user_entity = any(k in t for k in ("user", "users", "employee", "staff",
                                         "member", "person", "worker"))

    if _word_in(t, "delete", "remove", "deactivate", "erase") and _user_entity:
        uid = next((p for p in parts if p.isdigit()), None)
        return "delete_user", ({"user-id": uid} if uid else {})

    if _word_in(t, "update", "edit", "rename", "modify", "change") and _user_entity:
        return "update_user", _extract_user_params(parts)

    if _word_in(t, "add", "create", "register") and _user_entity:
        return "add_user", _extract_user_params(parts)

    if "new" in t and _user_entity and not _word_in(t, "get", "show", "find"):
        return "add_user", _extract_user_params(parts)

    if _word_in(t, "get", "show", "find", "fetch", "retrieve",
                "list", "look", "view", "check", "display") and _user_entity:
        uid = next((p for p in parts if p.isdigit()), None)
        return "get_user", ({"user-id": uid} if uid else {})

    # ── enroll ────────────────────────────────────────────────────────────────
    if "enroll" in t or "biometric" in t or "face" in t and _user_entity:
        params = {**_extract_door_params(parts), **_extract_user_params(parts)}
        return "enroll_user", params

    # ── access setting ────────────────────────────────────────────────────────
    _access_phrase = any(k in t for k in (
        "access setting", "access time", "work hour", "work time",
        "start time", "end time", "work start", "work end", "schedule",
        "working hour", "office hour", "shift time", "timing",
    ))
    _access_loose = "access" in t and any(k in t for k in (
        "setting", "settings", "time", "hour", "hours", "schedule", "timing",
    ))
    _time_direct = any(k in t for k in ("work start", "work end", "start time", "end time"))

    if _access_phrase or _access_loose or _time_direct:
        if "default" in t:
            if _word_in(t, "set", "update", "change", "restore", "reset"):
                return "set_default_access_setting", _extract_access_params(t, parts)
            return "get_default_access_setting", {}
        if _word_in(t, "set", "update", "change", "configure", "reset"):
            return "set_access_setting", _extract_access_params(t, parts)
        return "get_access_setting", {}

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





def _extract_access_params(t: str, parts: list) -> dict:
    params = {}

    # Weekday
    day = _parse_weekday(t)
    if day is not None:
        params["week-day"] = day

    # Collect all time mentions in order (HH:MM or H am/pm or bare H)
    all_times = []
    for m in re.finditer(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", t, re.IGNORECASE):
        hh = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
        period = (m.group(3) or "").lower()
        hh = _apply_ampm(hh, period)
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            all_times.append((str(hh), str(mm)))

    has_start = any(k in t for k in ("start", "from", "begin", "open"))
    has_end   = any(k in t for k in ("end", "to", "until", "close", "finish"))

    if len(all_times) >= 2:
        # Two distinct times → first is start, second is end
        params["work-start-hh"] = all_times[0][0]
        params["work-start-mm"] = all_times[0][1]
        params["work-end-hh"]   = all_times[1][0]
        params["work-end-mm"]   = all_times[1][1]
    elif len(all_times) == 1:
        hh, mm = all_times[0]
        if has_end and not has_start:
            params["work-end-hh"] = hh
            params["work-end-mm"] = mm
        else:
            params["work-start-hh"] = hh
            params["work-start-mm"] = mm

    return params



def _extract_door_params(parts: list) -> dict:
    params = {}

    for i, p in enumerate(parts):
        pl = p.lower()

        if pl in ("door", "id", "door-id") and i + 1 < len(parts):
            if parts[i + 1].isdigit():
                params["pdid"] = parts[i + 1]

        if pl == "name" and i + 1 < len(parts):
            params["door-name"] = parts[i + 1]

        if pl == "ip" and i + 1 < len(parts):
            params["ip-address"] = parts[i + 1]

        if pl == "mac" and i + 1 < len(parts):
            params["mac-address"] = parts[i + 1]

        if p.isdigit() and "pdid" not in params:
            params["pdid"] = p

    return params