"""
OpenAI LLM client with error handling
"""

from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, DEBUG_MODE, USE_MOCK
from app.exceptions import IntentParsingError, ConfigError
from app.logger import logger

# Initialize client only if API key is available
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
elif not USE_MOCK:
    raise ConfigError("OPENAI_API_KEY not configured", "OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are an intent detection engine for a security system.

Return ONLY valid JSON. No explanation, no markdown, just pure JSON.

Format:
{
  "tasks": [
    {
      "intent": "",
      "parameters": {}
    }
  ]
}

Supported intents:

USER MANAGEMENT:
- add_user (name, user_id) - Add a new user
- delete_user (user_id) - Delete a user
- update_user (user_id, name) - Update user details

ENROLLMENT OPTIONS:
- get_enroll_options (format) - Get current enrollment configuration
- set_enroll_options (enroll_on_device, enroll_using, enroll_finger_count, enroll_palm_count, enroll_card_count, enroll_mode, format) - Set enrollment options
- get_default_enroll_options (format) - Get default enrollment settings
- set_default_enroll_options (enroll_on_device, enroll_using, enroll_finger_count, enroll_palm_count, enroll_card_count, enroll_mode) - Set default enrollment options

ACCESS SETTING:
- get_access_setting (week_day, work_start_hh, work_start_mm, work_end_hh, work_end_mm, format) - Get current access settings
- set_access_setting (week_day, work_start_hh, work_start_mm, work_end_hh, work_end_mm, format) - Set access settings
- get_default_access_setting (format) - Get default access settings
- set_default_access_setting (week_day, work_start_hh, work_start_mm, work_end_hh, work_end_mm) - Set default access settings

PANEL DETAILS:
- get_panel_details (user, door, alarm, io_link, format) - Get panel summary counts (users, doors, alarms, IO-links). Pass filter flags to get only specific sections; omit all to get everything.

PANEL DOOR LIST:
- get_panel_door_list (pdid, format) - Get list of configured panel doors or specific door details. Pass pdid to fetch a particular panel door; omit it to retrieve all doors. Use format to specify response type (text or xml).

COMMAND:
- get_user_count () - Get total number of users configured in the device. Returns count of all users irrespective of active/inactive status.

Examples:

Input: Add user Ravi with id 101
Output:
{
  "tasks": [
    {
      "intent": "add_user",
      "parameters": {
        "name": "Ravi",
        "user_id": "101"
      }
    }
  ]
}

Input: Set enrollment to max 5 fingers
Output:
{
  "tasks": [
    {
      "intent": "set_enroll_options",
      "parameters": {
        "enroll_finger_count": "5"
      }
    }
  ]
}

Input: Get current enrollment settings
Output:
{
  "tasks": [
    {
      "intent": "get_enroll_options",
      "parameters": {}
    }
  ]
}

Input: Set dual template mode for enrollment
Output:
{
  "tasks": [
    {
      "intent": "set_enroll_options",
      "parameters": {
        "enroll_mode": "1"
      }
    }
  ]
}
"""

def call_llm(user_input: str) -> str:
    """
    Call OpenAI LLM to parse user intent
    
    Args:
        user_input: User's natural language input
        
    Returns:
        JSON string with parsed intent
        
    Raises:
        IntentParsingError: If LLM call fails or returns invalid JSON
    """
    try:
        logger.debug(f"Calling LLM with input: {user_input}")
        
        # If in mock mode and no API key, use simple intent parser
        if USE_MOCK and not client:
            return _mock_parse_intent(user_input)
        
        if not client:
            raise IntentParsingError(
                "LLM client not initialized",
                {"user_input": user_input}
            )
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0,
            timeout=OPENAI_TIMEOUT,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ]
        )

        if not response.choices or not response.choices[0].message.content:
            raise IntentParsingError(
                "Empty response from LLM",
                {"user_input": user_input}
            )

        result = response.choices[0].message.content.strip()
        
        if DEBUG_MODE:
            logger.debug(f"LLM response: {result}")
        
        return result

    except (RateLimitError, APIConnectionError) as e:
        logger.error(f"LLM API connection error: {str(e)}")
        raise IntentParsingError(
            f"LLM service temporarily unavailable: {str(e)}",
            {"user_input": user_input, "error_type": type(e).__name__}
        )
        
    except APIError as e:
        logger.error(f"LLM API error: {str(e)}")
        raise IntentParsingError(
            f"LLM API error: {str(e)}",
            {"user_input": user_input, "error_type": type(e).__name__}
        )
        
    except Exception as e:
        logger.error(f"Unexpected error calling LLM: {str(e)}")
        raise IntentParsingError(
            f"Failed to call LLM: {str(e)}",
            {"user_input": user_input, "error_type": type(e).__name__}
        )


def _mock_parse_intent(user_input: str) -> str:
    """
    Simple mock intent parser for testing without OpenAI API
    Used when USE_MOCK=True and no API key is configured
    """
    import json
    
    user_input_lower = user_input.lower()
    
    # Mock mapping of user inputs to intents
    if "enroll" in user_input_lower or "enrollment" in user_input_lower:
        if "get" in user_input_lower or "show" in user_input_lower or "current" in user_input_lower:
            if "default" in user_input_lower:
                return json.dumps({
                    "tasks": [{
                        "intent": "get_default_enroll_options",
                        "parameters": {}
                    }]
                })
            return json.dumps({
                "tasks": [{
                    "intent": "get_enroll_options",
                    "parameters": {}
                }]
            })
        elif "set" in user_input_lower:
            params = {}
            if "finger" in user_input_lower or "5" in user_input_lower:
                params["finger_count"] = "5"
            if "mode" in user_input_lower or "dual" in user_input_lower:
                params["mode"] = "1"
            if "default" in user_input_lower:
                return json.dumps({
                    "tasks": [{
                        "intent": "set_default_enroll_options",
                        "parameters": params
                    }]
                })
            return json.dumps({
                "tasks": [{
                    "intent": "set_enroll_options",
                    "parameters": params
                }]
            })
    
    # User management intents
    if "add" in user_input_lower or "create" in user_input_lower:
        if "user" in user_input_lower:
            parts = user_input_lower.split()
            name = "user"
            user_id = None
            for i, part in enumerate(parts):
                if part == "user" and i + 1 < len(parts):
                    name = parts[i + 1]
                if part == "id" and i + 1 < len(parts):
                    user_id = parts[i + 1]
            return json.dumps({
                "tasks": [{
                    "intent": "add_user",
                    "parameters": {
                        "name": name,
                        **({"user_id": user_id} if user_id else {})
                    }
                }]
            })
    
    # Nothing matched — return empty so caller treats as unrecognised input
    return json.dumps({"tasks": []})