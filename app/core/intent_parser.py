"""
Intent Parser - Converts natural language to structured tasks
Uses LLM to understand user intent and extract parameters
"""

import json
from app.llm.openai_client import call_llm
from app.exceptions import IntentParsingError
from app.logger import logger, log_intent


def parse_intent(user_input: str) -> dict:
    """
    Parse user input into structured intent
    
    Args:
        user_input: User's natural language input
        
    Returns:
        Dict with "tasks" key containing list of task dicts
        
    Raises:
        IntentParsingError: If parsing or validation fails
    """
    
    if not user_input or not isinstance(user_input, str):
        raise IntentParsingError(
            "User input must be non-empty string",
            {"user_input": user_input}
        )
    
    user_input = user_input.strip()
    
    logger.debug(f"Parsing intent for: {user_input}")
    
    try:
        # Call LLM to get raw response
        raw_response = call_llm(user_input)
        
        # Parse JSON response
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LLM: {raw_response}")
            raise IntentParsingError(
                f"LLM returned invalid JSON: {str(e)}",
                {
                    "user_input": user_input,
                    "raw_response": raw_response[:200],  # First 200 chars
                    "error": str(e)
                }
            )
        
        # Validate structure
        if "tasks" not in parsed:
            raise IntentParsingError(
                "LLM response missing 'tasks' key",
                {
                    "user_input": user_input,
                    "response": parsed
                }
            )
        
        if not isinstance(parsed["tasks"], list):
            raise IntentParsingError(
                "'tasks' must be a list",
                {
                    "user_input": user_input,
                    "tasks_type": type(parsed["tasks"]).__name__
                }
            )
        
        if len(parsed["tasks"]) == 0:
            logger.warning(f"LLM returned no tasks for: {user_input}")
            raise IntentParsingError(
                "No tasks could be extracted from input",
                {"user_input": user_input}
            )
        
        # Validate each task
        for i, task in enumerate(parsed["tasks"]):
            if not isinstance(task, dict):
                raise IntentParsingError(
                    f"Task {i} is not a dictionary",
                    {"user_input": user_input, "task_index": i}
                )
            
            if "intent" not in task:
                raise IntentParsingError(
                    f"Task {i} missing 'intent' key",
                    {"user_input": user_input, "task_index": i}
                )
            
            if "parameters" not in task:
                task["parameters"] = {}
            
            if not isinstance(task["parameters"], dict):
                raise IntentParsingError(
                    f"Task {i} parameters must be dictionary",
                    {"user_input": user_input, "task_index": i}
                )
        
        log_intent(user_input, parsed)
        logger.info(f"Successfully parsed {len(parsed['tasks'])} task(s)")
        
        return parsed
        
    except IntentParsingError:
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error parsing intent: {str(e)}")
        raise IntentParsingError(
            f"Unexpected error: {str(e)}",
            {
                "user_input": user_input,
                "error_type": type(e).__name__
            }
        )