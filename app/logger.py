"""
Centralized logging system for CoSec Copilot
"""

import logging
import json
from datetime import datetime
from app.config import DEBUG_MODE


def setup_logger(name: str, level=logging.INFO):
    """Setup and return a logger with structured format"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if DEBUG_MODE:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(level)
    
    return logger


# Create module-level logger
logger = setup_logger(__name__)


def log_event(event_type: str, data: dict, level: str = "INFO"):
    """Log structured events for debugging and monitoring"""
    timestamp = datetime.now().isoformat()
    log_data = {
        "timestamp": timestamp,
        "event_type": event_type,
        "data": data
    }
    
    log_level = getattr(logging, level, logging.INFO)
    logger.log(log_level, json.dumps(log_data))


def log_intent(user_input: str, parsed_intent: dict):
    """Log intent parsing for debugging"""
    log_event("INTENT_PARSED", {
        "user_input": user_input,
        "intent": parsed_intent
    }, "DEBUG")


def log_task_execution(task: dict, handler: str, result: dict):
    """Log task execution for monitoring"""
    log_event("TASK_EXECUTED", {
        "task": task,
        "handler": handler,
        "result": result
    }, "INFO")


def log_parameter_resolution(params: dict, missing: list, partial: dict):
    """Log parameter resolution issues"""
    log_event("PARAMETER_RESOLUTION", {
        "params": params,
        "missing": missing,
        "partial": partial
    }, "DEBUG")


def log_api_call(url: str, request_params: dict, response: str, status: str = "success"):
    """Log API calls for debugging"""
    log_event("API_CALL", {
        "url": url,
        "request_params": request_params,
        "response_preview": response[:100] if response else None,
        "status": status
    }, "DEBUG")


def log_error(error: Exception, context: dict = None):
    """Log errors with context"""
    log_event("ERROR", {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }, "ERROR")
