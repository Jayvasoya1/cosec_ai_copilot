"""
Response Builder - Formats execution results into user-friendly responses
"""

from app.core.question_engine import generate_question
from app.core.memory import memory
from app.core.param_resolver import MEMORY_KEY_MAP
from app.logger import logger


def build_response(results: list) -> dict:
    """
    Build final response for user
    
    Args:
        results: List of execution results
        
    Returns:
        Final response dict with status and messages
    """
    
    if not results:
        return {
            "status": "error",
            "message": "No tasks were executed",
            "details": []
        }
    
    # Check if any result needs user input
    for result in results:
        if result.get("status") == "need_input" or "need_input" in result:
            missing = result.get("missing", [])
            question = generate_question(missing)
            logger.info(f"Asking for user input: {missing}")
            
            return {
                "status": "need_input",
                "message": question,
                "partial": result.get("partial", {}),
                "missing_fields": missing
            }
    
    # Process results
    messages = []
    errors = []
    successes = []
    details = []
    failed_actions = []  # Track which groups/actions failed
    successful_groups = set()  # Track successful groups for context clearing
    
    for i, result in enumerate(results):
        logger.debug(f"Processing result {i}: {result.get('status')}")
        
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error")
            error_code = result.get("code", "ERROR")
            messages.append(f"❌ Task {i+1}: {error_msg}")
            errors.append({
                "task": i,
                "error": error_msg,
                "code": error_code,
                "details": result.get("details", {})
            })
            failed_actions.append(result.get("group"))
            
        elif result.get("status") == "success":
            success_msg = result.get("message", "Command executed")
            messages.append(success_msg)
            successes.append({
                "task": i,
                "url": result.get("url"),
                "mock": result.get("mock", False)
            })
            successful_groups.add(result.get("group"))
            
        else:
            messages.append(f"⚠️ Task {i+1}: Unknown status '{result.get('status')}'")
        
        details.append(result)
    
    if successful_groups:
        logger.info(f"Clearing memory context for successful groups: {successful_groups}")
        for group in successful_groups:
            key = MEMORY_KEY_MAP.get(group, f"last_{group}")
            memory.data.pop(key, None)
        logger.debug(f"Memory after clearing: {memory.data}")
    
    # Determine overall status
    if errors:
        overall_status = "partial_success" if successes else "error"
    else:
        overall_status = "success"
    
    logger.info(f"Final status: {overall_status}")
    
    return {
        "status": overall_status,
        "message": "\n".join(messages),
        "summary": {
            "total_tasks": len(results),
            "successful": len(successes),
            "failed": len(errors)
        },
        "errors": errors,
        "successes": successes,
        "details": details
    }