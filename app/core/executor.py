"""
Executor - Executes tasks by calling APIs
Handles parameter resolution, API building, and device communication
"""

from app.services.api_builder import build_url
from app.services.device_api import call_device_api
from app.config import USE_MOCK
from app.exceptions import MissingParametersError, DeviceAPIError
from app.logger import logger, log_task_execution


def execute_task(route_data: dict) -> dict:
    """
    Execute a single task
    
    Args:
        route_data: Handler response with group, params, and optional fields
        
    Returns:
        Execution result dict
    """
    
    logger.debug(f"Executing task: {route_data}")
    
    # Check for parameter errors
    if "need_input" in route_data:
        logger.info(f"Need user input: {route_data.get('missing')}")
        return route_data
    
    if "error" in route_data:
        logger.error(f"Task error: {route_data['error']}")
        return {
            "status": "error",
            "error": route_data["error"],
            "details": route_data.get("details", {})
        }
    
    try:
        group = route_data.get("group")
        params = route_data.get("params", {})
        
        if not group:
            raise ValueError("Group name is required in route_data")
        
        # params can be empty for "get" operations
        if params is None:
            raise ValueError("Parameters dict is required in route_data")
        logger.info(params)
        # Build API URL
        url = build_url(group, params)
        logger.info(f"Built URL: {url}")
        
        # Mock execution for testing
        if USE_MOCK:
            logger.info("Using MOCK mode - not calling real device")
            return {
                "status": "success",
                "url": url,
                "message": f"✅ Mock executed: {params}",
                "mock": True,
                "group": group,
                "action": params.get("action")
            }
        
        # Real device execution
        logger.info("Calling real device API...")
        response = call_device_api(url)
        
        log_task_execution(route_data, "device_api", response)
        
        return {
            "status": "success",
            "url": url,
            "message": "✅ Command executed successfully",
            "response": response.get("data"),
            "device_status": response.get("status_code"),
            "group": group,
            "action": params.get("action")
        }
        
    except DeviceAPIError as e:
        logger.error(f"Device API error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "code": e.code,
            "details": e.details
        }
        
    except Exception as e:
        logger.error(f"Task execution error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "code": "EXECUTION_ERROR"
        }


def execute_tasks(tasks: list, router) -> list:
    """
    Execute multiple tasks in sequence
    Stops if input is needed
    
    Args:
        tasks: List of task dicts
        router: Routing function to convert tasks to handler calls
        
    Returns:
        List of execution results
    """
    
    if not tasks:
        logger.warning("No tasks to execute")
        return []
    
    logger.info(f"Executing {len(tasks)} task(s)")
    results = []
    
    for i, task in enumerate(tasks):
        logger.info(f"Task {i+1}/{len(tasks)}: {task.get('intent')}")
        
        try:
            # Route task to appropriate handler
            route_data = router(task)
            
            # Execute the task
            result = execute_task(route_data)
            
            # Check if user input is needed
            if result.get("status") == "need_input" or "need_input" in result:
                result["pending_intent"] = task.get("intent")
                logger.info(f"User input needed, stopping execution")
                return [result]
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error executing task {i}: {str(e)}")
            results.append({
                "status": "error",
                "error": str(e),
                "code": "EXECUTION_FAILED",
                "task_index": i
            })
            # Continue with next task or stop?
            # For now, continue to collect all results
    
    logger.info(f"Execution complete: {len(results)} result(s)")
    return results