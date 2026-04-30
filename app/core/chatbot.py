"""
Chatbot help engine for CoSec AI Copilot.

Handles conversational help queries — "what can I do?", "what params does
enroll user need?", "tell me about set door config?" — without touching any
existing classification or execution logic.

Features:
  • Full function registry with required/optional params and descriptions
  • Natural-language help intent detection (list / describe / params)
  • Fuzzy matching for spelling tolerance (difflib)
  • AI-sense: understands aliases, partial names, synonym phrases
"""

import re
import difflib
from typing import Optional, Tuple


# ── Function registry ─────────────────────────────────────────────────────────
# Each entry: display name, description, required/optional params (name, type, desc), example, notes

FUNCTION_REGISTRY = {
    "add_user": {
        "display":      "Add User",
        "description":  "Register a new user in the access control system.",
        "example":      "add user Jay with id 5",
        "required": [
            ("user-id", "int",    "Unique numeric ID for the user (e.g. 5)"),
            ("name",    "string", "Full name of the user (e.g. Jay)"),
        ],
        "optional": [
            ("user-active",        "0|1",      "1 = active (default), 0 = inactive"),
            ("vip",                "0|1",      "1 = VIP access"),
            ("user-pin",           "string",   "PIN code for the user"),
            ("card1",              "string",   "Primary card number"),
            ("card2",              "string",   "Secondary card number"),
            ("user-group",         "0–999",    "Group the user belongs to"),
            ("restrict-access",    "0|1",      "1 = restrict access"),
            ("route-id",           "int",      "Access route ID"),
            ("by-pass-finger",     "0|1",      "1 = skip fingerprint verification"),
            ("by-pass-palm",       "0|1",      "1 = skip palm verification"),
            ("by-pass-face",       "0|1",      "1 = skip face verification"),
            ("validity-enable",    "0|1",      "1 = enable validity period"),
            ("validity-date-dd",   "1–31",     "Validity expiry day"),
            ("validity-date-mm",   "1–12",     "Validity expiry month"),
            ("validity-date-yyyy", "2000–2099","Validity expiry year"),
            ("validity-time-hh",   "0–23",     "Validity expiry hour (24-hour)"),
            ("validity-time-mm",   "0–59",     "Validity expiry minute"),
        ],
        "group": "users",
    },

    "update_user": {
        "display":      "Update User",
        "description":  "Update an existing user's name or settings.",
        "example":      "update user 3 name to Alice",
        "required": [
            ("user-id", "int",    "ID of the user to update"),
            ("name",    "string", "New name for the user"),
        ],
        "optional": [
            ("user-active",     "0|1",   "1 = active, 0 = inactive"),
            ("vip",             "0|1",   "1 = VIP access"),
            ("user-pin",        "string","New PIN code"),
            ("card1",           "string","Primary card number"),
            ("card2",           "string","Secondary card number"),
            ("user-group",      "0–999", "Group the user belongs to"),
            ("restrict-access", "0|1",   "1 = restrict access"),
            ("by-pass-finger",  "0|1",   "1 = skip fingerprint"),
            ("by-pass-palm",    "0|1",   "1 = skip palm"),
            ("by-pass-face",    "0|1",   "1 = skip face"),
        ],
        "group": "users",
    },

    "delete_user": {
        "display":      "Delete User",
        "description":  "Permanently remove a user and all their credentials.",
        "example":      "delete user 3",
        "required": [
            ("user-id", "int", "ID of the user to delete"),
        ],
        "optional": [],
        "group": "users",
    },

    "get_user": {
        "display":      "Get User",
        "description":  "Retrieve user details. Returns all users if no filter is given.",
        "example":      "get user 5",
        "required":     [],
        "optional": [
            ("user-id",     "int",   "Filter by user ID"),
            ("ref-user-id", "int",   "Filter by reference user ID"),
            ("name",        "string","Filter by name"),
            ("user-active", "0|1",   "Filter by active status"),
            ("vip",         "0|1",   "Filter by VIP status"),
            ("user-group",  "int",   "Filter by group"),
        ],
        "notes": "Omit all filters to retrieve every user in the system.",
        "group": "users",
    },

    "enroll_user": {
        "display":      "Enroll User",
        "description":  (
            "Enroll a user's biometric (face) data on a specific door device.\n"
            "Automatically enables face recognition for the user and activates\n"
            "face-recognition settings on the door."
        ),
        "example":      "enroll user 5 on door 2",
        "required": [
            ("user-id", "int", "ID of the user to enroll"),
            ("pdid",    "int", "Panel Door ID — which door to enroll on"),
        ],
        "optional": [],
        "notes": (
            "Triggers 3 API calls automatically:\n"
            "  1. Enroll biometric on door\n"
            "  2. Enable face-recognition flag on the user record\n"
            "  3. Activate FR settings on the door"
        ),
        "group": "enrolluser",
    },

    "get_panel_door_config": {
        "display":      "Get Door Configuration",
        "description":  "Read the current configuration of a door device.",
        "example":      "get door config for door 2",
        "required": [
            ("pdid", "int", "Panel Door ID of the door to read"),
        ],
        "optional": [
            ("format", "text|xml", "Response format (default: text)"),
        ],
        "group": "panel-door-config",
    },

    "set_panel_door_config": {
        "display":      "Set Door Configuration",
        "description":  "Add or configure a door device on the panel.",
        "example":      "set door name MainGate type argo face ip 192.168.1.100 mac AA:BB:CC:DD:EE:FF",
        "required": [
            ("door-name",   "string", "Name for the door (e.g. MainGate)"),
            ("door-type",   "string", "Device model: 'argo face' or 'vega'"),
            ("ip-address",  "string", "IP address of the door device (e.g. 192.168.1.100)"),
            ("mac-address", "string", "MAC address of the door device (e.g. AA:BB:CC:DD:EE:FF)"),
        ],
        "optional": [
            ("format", "text|xml", "Response format"),
        ],
        "notes": "door-type accepts: 'argo face' (face recognition unit) or 'vega'.",
        "group": "panel-door-config",
    },

    "get_default_panel_door_config": {
        "display":      "Get Default Door Configuration",
        "description":  "Retrieve the factory/default door configuration settings.",
        "example":      "get default door config",
        "required":     [],
        "optional": [
            ("format", "text|xml", "Response format"),
        ],
        "group": "panel-door-config",
    },

    "set_default_panel_door_config": {
        "display":      "Set Default Door Configuration",
        "description":  "Restore or update the default door configuration.",
        "example":      "set default door config",
        "required":     [],
        "optional": [
            ("door-name",          "string",   "Default door name"),
            ("door-type",          "string",   "Default door type"),
            ("communication-type", "int",      "Communication protocol type"),
            ("ip-address",         "string",   "Default IP address"),
            ("mac-address",        "string",   "Default MAC address"),
            ("format",             "text|xml", "Response format"),
        ],
        "group": "panel-door-config",
    },

    "get_access_setting": {
        "display":      "Get Access Settings",
        "description":  "Retrieve current work-hours / access-time schedule.",
        "example":      "get access settings",
        "required":     [],
        "optional": [
            ("week-day",      "0–6",  "Day of week: Sunday=0, Monday=1 … Saturday=6"),
            ("work-start-hh", "0–23", "Work start hour (24-hour)"),
            ("work-start-mm", "0–59", "Work start minute"),
            ("work-end-hh",   "0–23", "Work end hour (24-hour)"),
            ("work-end-mm",   "0–59", "Work end minute"),
            ("format",        "text|xml", "Response format"),
        ],
        "group": "access-setting",
    },

    "set_access_setting": {
        "display":      "Set Access Settings",
        "description":  "Configure work-hours / access-time schedule.",
        "example":      "set work hours 9 AM to 5 PM on Monday",
        "required":     [],
        "optional": [
            ("week-day",      "0–6",  "Day of week: Sunday=0, Monday=1 … Saturday=6"),
            ("work-start-hh", "0–23", "Work start hour (24-hour)"),
            ("work-start-mm", "0–59", "Work start minute"),
            ("work-end-hh",   "0–23", "Work end hour (24-hour)"),
            ("work-end-mm",   "0–59", "Work end minute"),
            ("format",        "text|xml", "Response format"),
        ],
        "notes": "Times auto-converted: '9 AM' → hh=9 mm=0, '5 PM' → hh=17 mm=0.",
        "group": "access-setting",
    },

    "get_default_access_setting": {
        "display":      "Get Default Access Settings",
        "description":  "Retrieve the factory-default access time schedule.",
        "example":      "get default access settings",
        "required":     [],
        "optional":     [],
        "group": "access-setting",
    },

    "set_default_access_setting": {
        "display":      "Set Default Access Settings",
        "description":  "Restore factory-default access time schedule.",
        "example":      "restore default access settings",
        "required":     [],
        "optional":     [],
        "group": "access-setting",
    },

    "get_panel_details": {
        "display":      "Get Panel Details",
        "description":  "Get a summary of the panel: total users, doors, alarms, and IO-links.",
        "example":      "get panel details",
        "required":     [],
        "optional": [
            ("user",    "int", "1 = include user count"),
            ("door",    "int", "1 = include door count"),
            ("alarm",   "int", "1 = include alarm count"),
            ("io-link", "int", "1 = include IO-link count"),
            ("format",  "text|xml", "Response format"),
        ],
        "group": "panel-details",
    },
}


# ── Alias table for natural-language → canonical key mapping ─────────────────

_ALIASES: dict[str, str] = {
    # add_user
    "add user":         "add_user",
    "create user":      "add_user",
    "register user":    "add_user",
    "new user":         "add_user",
    "add new user":     "add_user",
    "add_user":         "add_user",

    # update_user
    "update user":      "update_user",
    "edit user":        "update_user",
    "modify user":      "update_user",
    "change user":      "update_user",
    "rename user":      "update_user",
    "update_user":      "update_user",

    # delete_user
    "delete user":      "delete_user",
    "remove user":      "delete_user",
    "deactivate user":  "delete_user",
    "erase user":       "delete_user",
    "delete_user":      "delete_user",

    # get_user
    "get user":         "get_user",
    "show user":        "get_user",
    "find user":        "get_user",
    "fetch user":       "get_user",
    "retrieve user":    "get_user",
    "list users":       "get_user",
    "get_user":         "get_user",

    # enroll_user
    "enroll user":              "enroll_user",
    "enroll":                   "enroll_user",
    "enrollment":               "enroll_user",
    "enroll_user":              "enroll_user",
    "biometric enroll":         "enroll_user",
    "face enroll":              "enroll_user",
    "register biometric":       "enroll_user",

    # get_panel_door_config
    "get door config":          "get_panel_door_config",
    "get door configuration":   "get_panel_door_config",
    "show door config":         "get_panel_door_config",
    "read door config":         "get_panel_door_config",
    "fetch door config":        "get_panel_door_config",
    "get_panel_door_config":    "get_panel_door_config",
    "panel door config get":    "get_panel_door_config",

    # set_panel_door_config
    "set door config":          "set_panel_door_config",
    "set door configuration":   "set_panel_door_config",
    "configure door":           "set_panel_door_config",
    "add door":                 "set_panel_door_config",
    "update door config":       "set_panel_door_config",
    "set_panel_door_config":    "set_panel_door_config",
    "panel door config set":    "set_panel_door_config",
    "door configuration":       "set_panel_door_config",

    # get_default_panel_door_config
    "get default door":         "get_default_panel_door_config",
    "get default door config":  "get_default_panel_door_config",
    "default door config get":  "get_default_panel_door_config",

    # set_default_panel_door_config
    "set default door":         "set_default_panel_door_config",
    "set default door config":  "set_default_panel_door_config",
    "restore default door":     "set_default_panel_door_config",

    # get_access_setting
    "get access":               "get_access_setting",
    "get access setting":       "get_access_setting",
    "get access settings":      "get_access_setting",
    "show work hours":          "get_access_setting",
    "show access settings":     "get_access_setting",
    "get_access_setting":       "get_access_setting",

    # set_access_setting
    "set access":               "set_access_setting",
    "set access setting":       "set_access_setting",
    "set access settings":      "set_access_setting",
    "set work hours":           "set_access_setting",
    "change work hours":        "set_access_setting",
    "update work hours":        "set_access_setting",
    "set_access_setting":       "set_access_setting",

    # get_default_access_setting
    "get default access":               "get_default_access_setting",
    "get default access settings":      "get_default_access_setting",
    "default access settings get":      "get_default_access_setting",

    # set_default_access_setting
    "set default access":               "set_default_access_setting",
    "set default access settings":      "set_default_access_setting",
    "restore default access":           "set_default_access_setting",
    "restore access settings":          "set_default_access_setting",

    # get_panel_details
    "panel details":            "get_panel_details",
    "get panel details":        "get_panel_details",
    "device info":              "get_panel_details",
    "device summary":           "get_panel_details",
    "panel info":               "get_panel_details",
    "panel summary":            "get_panel_details",
    "get_panel_details":        "get_panel_details",
}

# All strings available for fuzzy matching
_ALL_MATCH_KEYS = sorted(set(list(_ALIASES.keys()) + list(FUNCTION_REGISTRY.keys())))


# ── Help intent patterns ───────────────────────────────────────────────────────

_LIST_PATTERNS = [
    r"\bhelp\b",
    r"\bwhat\b.{0,20}\bcan\b.{0,20}\bdo\b",
    r"\bwhat\b.{0,15}\bfeatures?\b",
    r"\bwhat\b.{0,15}\bcommands?\b",
    r"\bwhat\b.{0,15}\bfunctions?\b",
    r"\bwhat\b.{0,15}\boperations?\b",
    r"\bwhat\b.{0,15}\bavailable\b",
    r"\blist\b.{0,15}\boperations?\b",
    r"\blist\b.{0,15}\bcommands?\b",
    r"\blist\b.{0,15}\bfunctions?\b",
    r"\bshow\b.{0,10}\bcommands?\b",
    r"\bshow\b.{0,10}\bfeatures?\b",
    r"\ball\b.{0,15}\boperations?\b",
    r"\ball\b.{0,15}\bcommands?\b",
    r"\bsupported\b.{0,15}\boperations?\b",
    r"\bwhat\b.{0,20}\bpossible\b",
    r"\bwhat\b.{0,20}\btypes?\b.{0,10}\bcommand\b",
    r"\bwhat\b.{0,20}\bdo\b.{0,15}\bsupport\b",
    r"\bwhat\b.{0,20}\bdo\b.{0,15}\boffer\b",
    r"\bwhat\b.{0,20}\bcan\b.{0,15}\buse\b",
]

_PARAMS_PATTERNS = [
    r"\bwhat\b.{0,20}\bparam(eter)?s?\b",
    r"\bwhat\b.{0,20}\bfields?\b",
    r"\bwhat\b.{0,20}\brequired\b",
    r"\bwhat\b.{0,20}\boptional\b",
    r"\bparam(eter)?s?\b.{0,15}\bfor\b",
    r"\bparam(eter)?s?\b.{0,15}\bneed(ed)?\b",
    r"\bfields?\b.{0,15}\bneed(ed)?\b",
    r"\binputs?\b.{0,15}\bfor\b",
    r"\bparam(eter)?\b.{0,10}\blist\b",
    r"\breq(uired)?\b.{0,10}\bparam(eter)?s?\b",
    r"\bmandatory\b.{0,15}\bparam(eter)?s?\b",
    r"\bopt(ional)?\b.{0,10}\bparam(eter)?s?\b",
    r"\bwhat\b.{0,20}\bneed\b.{0,15}\bprovide\b",
    r"\bwhat\b.{0,20}\bneed\b.{0,15}\bpass\b",
    r"\bwhat\b.{0,20}\bneed\b.{0,15}\benter\b",
    r"\bwhat\b.{0,20}\bneed\b.{0,15}\bgive\b",
    r"\bwhat\b.{0,20}\binput\b",
    r"\bwhat\b.{0,30}\barg(ument)?s?\b",
]

_DESCRIBE_PATTERNS = [
    r"\bwhat\s+is\b",
    r"\bwhat'?s\b",
    r"\btell\b.{0,10}\babout\b",
    r"\bexplain\b",
    r"\bdescribe\b",
    r"\bhow\s+does\b",
    r"\bhow\s+do\s+i\b",
    r"\bhow\s+to\b",
    r"\bwhat\b.{0,15}\bmean\b",
    r"\bwhat\b.{0,15}\bdoes\b",
    r"\binfo\b.{0,10}\babout\b",
    r"\bdetails?\b.{0,10}\babout\b",
    r"\btell\b.{0,15}\bmore\b",
]


# ── Core helpers ───────────────────────────────────────────────────────────────

def _normalise(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_match(text: str, patterns: list) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def _fuzzy_resolve(text: str) -> Optional[str]:
    """
    Return the canonical FUNCTION_REGISTRY key that best matches `text`.
    Strategy:
      1. Exact alias / key lookup
      2. Partial containment in aliases
      3. Difflib fuzzy match on all known names
      4. Sliding n-gram word windows
    """
    t = _normalise(text)

    # 1. Exact
    if t in _ALIASES:
        return _ALIASES[t]
    if t in FUNCTION_REGISTRY:
        return t

    # 2. Containment (alias is substring of query, or query is substring of alias)
    for alias, key in _ALIASES.items():
        if alias in t or t in alias:
            return key

    # 3. Difflib on full normalised text
    matches = difflib.get_close_matches(t, _ALL_MATCH_KEYS, n=1, cutoff=0.55)
    if matches:
        hit = matches[0]
        return _ALIASES.get(hit, hit if hit in FUNCTION_REGISTRY else None)

    # 4. Sliding window: try longest sub-phrases first
    words = t.split()
    for length in range(min(5, len(words)), 0, -1):
        for start in range(len(words) - length + 1):
            phrase = " ".join(words[start : start + length])

            if phrase in _ALIASES:
                return _ALIASES[phrase]
            if phrase in FUNCTION_REGISTRY:
                return phrase

            close = difflib.get_close_matches(phrase, _ALL_MATCH_KEYS, n=1, cutoff=0.62)
            if close:
                hit = close[0]
                resolved = _ALIASES.get(hit, hit if hit in FUNCTION_REGISTRY else None)
                if resolved:
                    return resolved

    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def detect_help_intent(text: str) -> Optional[Tuple[str, Optional[str]]]:
    """
    Return (query_type, target_key) if the text is a help query, else None.

    query_type: "list"     → user wants all available operations
                "describe" → user wants to know what a specific function does
                "params"   → user wants required/optional params for a function
    target_key: canonical FUNCTION_REGISTRY key, or None (for list / system query)
    """
    if not text or not text.strip():
        return None

    t = _normalise(text)

    # ── params query first (more specific than describe) ──────────────────
    # Also catches trailing "X params" / "X parameters" phrasing
    has_param_word = bool(re.search(r"\bparams?\b|\bparameters?\b", t))
    if _is_match(t, _PARAMS_PATTERNS) or has_param_word:
        func = _fuzzy_resolve(t)
        return ("params", func)

    # ── describe query ────────────────────────────────────────────────────
    if _is_match(t, _DESCRIBE_PATTERNS):
        func = _fuzzy_resolve(t)
        if func:
            return ("describe", func)
        # Generic "what is this system" type questions
        if any(k in t for k in ("cosec", "copilot", "system", "chatbot", "bot", "this", "you")):
            return ("describe", None)

    # ── list query ────────────────────────────────────────────────────────
    if _is_match(t, _LIST_PATTERNS):
        func = _fuzzy_resolve(t)
        # "what can enroll user do?" → describe, not list
        if func and _is_match(t, _DESCRIBE_PATTERNS):
            return ("describe", func)
        return ("list", None)

    return None


def generate_help_response(query_type: str, target: Optional[str]) -> str:
    """Build the human-readable help string for the chatbot response."""
    if query_type == "list":
        return _response_list_all()
    if query_type == "describe":
        if target and target in FUNCTION_REGISTRY:
            return _response_describe(target)
        return _response_system_overview()
    if query_type == "params":
        if target and target in FUNCTION_REGISTRY:
            return _response_params(target)
        return _response_params_generic()
    return _response_system_overview()


# ── HTML response builders ─────────────────────────────────────────────────────
# All responses return HTML strings that the frontend renders via innerHTML.
# Content from FUNCTION_REGISTRY is author-controlled so no escaping needed.

def _response_list_all() -> str:
    groups = [
        ("User Management", [
            "add_user", "update_user", "delete_user", "get_user",
        ]),
        ("Enrollment", [
            "enroll_user",
        ]),
        ("Door Configuration", [
            "get_panel_door_config", "set_panel_door_config",
            "get_default_panel_door_config", "set_default_panel_door_config",
        ]),
        ("Access Settings", [
            "get_access_setting", "set_access_setting",
            "get_default_access_setting", "set_default_access_setting",
        ]),
        ("Panel", [
            "get_panel_details",
        ]),
    ]

    rows = []
    for group_label, keys in groups:
        rows.append(f'<div class="ch-group-label">{group_label}</div>')
        for key in keys:
            info = FUNCTION_REGISTRY[key]
            desc = info["description"].splitlines()[0]
            rows.append(
                f'<div class="ch-op-row">'
                f'<span class="ch-op-name">{info["display"]}</span>'
                f'<span class="ch-op-desc">{desc}</span>'
                f'</div>'
            )

    return (
        '<div class="ch-card">'
        '<div class="ch-title">Available Operations</div>'
        + "".join(rows) +
        '<div class="ch-footer">'
        'Ask: <code>"what is [operation]?"</code> &nbsp;or&nbsp; <code>"params for [operation]?"</code>'
        '</div>'
        '</div>'
    )


def _response_describe(key: str) -> str:
    info = FUNCTION_REGISTRY[key]

    html = (
        '<div class="ch-card">'
        f'<div class="ch-title">{info["display"]}</div>'
        f'<div class="ch-desc">{info["description"].replace(chr(10), "<br>")}</div>'
    )

    # Required params
    html += '<div class="ch-section-label">Required Parameters</div>'
    if info["required"]:
        for name, typ, desc in info["required"]:
            html += (
                f'<div class="ch-param-row">'
                f'<span class="ch-param-name">{name}</span>'
                f'<span class="ch-param-type">{typ}</span>'
                f'<span class="ch-param-desc">{desc}</span>'
                f'</div>'
            )
    else:
        html += '<div class="ch-none">None — call it without any required parameters</div>'

    # Optional params
    html += '<div class="ch-section-label">Optional Parameters</div>'
    if info["optional"]:
        for name, typ, desc in info["optional"]:
            html += (
                f'<div class="ch-param-row">'
                f'<span class="ch-param-name">{name}</span>'
                f'<span class="ch-param-type">{typ}</span>'
                f'<span class="ch-param-desc">{desc}</span>'
                f'</div>'
            )
    else:
        html += '<div class="ch-none">None</div>'

    # Example
    html += (
        f'<div class="ch-example">'
        f'<span class="ch-example-label">Example</span>'
        f'<code>{info["example"]}</code>'
        f'</div>'
    )

    # Notes
    notes = info.get("notes", "")
    if notes:
        note_html = notes.replace("\n", "<br>")
        html += f'<div class="ch-note">{note_html}</div>'

    html += '</div>'
    return html


def _response_params(key: str) -> str:
    info = FUNCTION_REGISTRY[key]

    html = (
        '<div class="ch-card">'
        f'<div class="ch-title">{info["display"]} &mdash; Parameters</div>'
    )

    # Required
    html += '<div class="ch-section-label ch-req-label">Required</div>'
    if info["required"]:
        for name, typ, desc in info["required"]:
            html += (
                f'<div class="ch-param-row">'
                f'<span class="ch-param-name">{name}</span>'
                f'<span class="ch-param-type">{typ}</span>'
                f'<span class="ch-param-desc">{desc}</span>'
                f'</div>'
            )
    else:
        html += '<div class="ch-none">None — all parameters are optional</div>'

    # Optional
    html += '<div class="ch-section-label">Optional</div>'
    if info["optional"]:
        for name, typ, desc in info["optional"]:
            html += (
                f'<div class="ch-param-row">'
                f'<span class="ch-param-name">{name}</span>'
                f'<span class="ch-param-type">{typ}</span>'
                f'<span class="ch-param-desc">{desc}</span>'
                f'</div>'
            )
    else:
        html += '<div class="ch-none">None</div>'

    # Notes
    notes = info.get("notes", "")
    if notes:
        note_html = notes.replace("\n", "<br>")
        html += f'<div class="ch-note">{note_html}</div>'

    html += '</div>'
    return html


def _response_params_generic() -> str:
    examples = [
        ("params for add user",           "add_user"),
        ("params for enroll user",        "enroll_user"),
        ("params for set door config",    "set_panel_door_config"),
        ("params for set access settings","set_access_setting"),
    ]
    rows = "".join(
        f'<div class="ch-op-row">'
        f'<span class="ch-op-name">{FUNCTION_REGISTRY[key]["display"]}</span>'
        f'<span class="ch-op-desc">try: <code>{phrase}</code></span>'
        f'</div>'
        for phrase, key in examples
    )
    return (
        '<div class="ch-card">'
        '<div class="ch-title">Parameter Help</div>'
        '<div class="ch-desc">Which operation do you want parameter info for?</div>'
        + rows +
        '<div class="ch-footer">Or type <code>help</code> to list all operations.</div>'
        '</div>'
    )


def _response_system_overview() -> str:
    capabilities = [
        ("Add / Update / Delete / Get User",  "Manage users in the system"),
        ("Enroll User",                        "Register face biometrics on a door device"),
        ("Get / Set Door Configuration",       "Read or configure door devices"),
        ("Get / Set Access Settings",          "Manage work-hours schedule"),
        ("Get Panel Details",                  "View device summary counts"),
    ]
    rows = "".join(
        f'<div class="ch-op-row">'
        f'<span class="ch-op-name">{name}</span>'
        f'<span class="ch-op-desc">{desc}</span>'
        f'</div>'
        for name, desc in capabilities
    )
    return (
        '<div class="ch-card">'
        '<div class="ch-title">CoSec AI Copilot</div>'
        '<div class="ch-desc">Your assistant for managing the biometric access control system.</div>'
        + rows +
        '<div class="ch-footer">'
        'Type <code>help</code> for all operations &nbsp;|&nbsp; '
        '<code>"what is [operation]?"</code> for details'
        '</div>'
        '</div>'
    )
