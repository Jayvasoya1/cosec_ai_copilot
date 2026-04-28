"""
OpenAI LLM client with error handling
"""

from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from app.config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, DEBUG_MODE
from app.exceptions import IntentParsingError, ConfigError
from app.logger import logger

# Validate API key
if not OPENAI_API_KEY:
    raise ConfigError("OPENAI_API_KEY not configured", "OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

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
- add_user (name, user_id)
- delete_user (user_id)
- update_user (user_id, name)

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

Input: Add Ravi and delete user 102
Output:
{
  "tasks": [
    {
      "intent": "add_user",
      "parameters": {
        "name": "Ravi"
      }
    },
    {
      "intent": "delete_user",
      "parameters": {
        "user_id": "102"
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