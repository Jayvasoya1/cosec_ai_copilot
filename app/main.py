"""
Main FastAPI application for CoSec AI Copilot
Orchestrates the complete request-response flow
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from app.config import validate_config, DEBUG_MODE
from app.core.intent_parser import parse_intent
from app.core.planner import plan_tasks
from app.core.router import route_intent
from app.core.executor import execute_tasks
from app.core.response_builder import build_response
from app.exceptions import CoSecException
from app.logger import logger, setup_logger

# Validate configuration at startup
try:
    validate_config()
    logger.info("Configuration validated")
except Exception as e:
    logger.critical(f"Configuration error: {str(e)}")
    raise

# FastAPI app
app = FastAPI(
    title="CoSec AI Copilot",
    description="AI-powered COSEC device control system",
    version="0.1.0",
    debug=DEBUG_MODE
)


class ChatQuery(BaseModel):
    """User query model"""
    text: str = Field(..., min_length=1, max_length=5000, description="User input text")
    
    @validator('text')
    def text_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Text cannot be only whitespace')
        return v.strip()


class ChatResponse(BaseModel):
    """API response model"""
    status: str = Field(..., description="Response status: success, error, need_input, partial_success")
    message: str = Field(..., description="Main message for user")
    details: dict = Field(default_factory=dict, description="Additional details")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "CoSec AI Copilot"
    }


@app.post("/chat", response_model=ChatResponse)
def chat(query: ChatQuery):
    """
    Main chat endpoint for user queries
    
    Workflow:
    1. Parse natural language intent
    2. Plan tasks
    3. Route to appropriate handler
    4. Execute tasks
    5. Build response
    
    Args:
        query: User query with text field
        
    Returns:
        ChatResponse with status and message
    """
    
    user_input = query.text
    logger.info(f"=== New Request ===")
    logger.info(f"User input: {user_input}")
    
    try:
        # Step 1: Parse intent using LLM
        logger.debug("Step 1: Parsing intent...")
        intent_data = parse_intent(user_input)
        
        # Step 2: Plan tasks
        logger.debug("Step 2: Planning tasks...")
        tasks = plan_tasks(intent_data)
        
        if not tasks:
            logger.warning("No tasks generated from intent")
            return ChatResponse(
                status="error",
                message="Could not understand your request. Please try again.",
                details={"reason": "no_tasks_generated"}
            )
        
        logger.info(f"Planned {len(tasks)} task(s)")
        
        # Step 3-5: Route, Execute, and Build Response
        logger.debug("Step 3-5: Routing and executing tasks...")
        results = execute_tasks(tasks, route_intent)
        
        # Build final response
        logger.debug("Building response...")
        response = build_response(results)
        
        logger.info(f"Response status: {response.get('status')}")
        logger.info(f"=== Request Complete ===\n")
        
        return ChatResponse(
            status=response.get("status", "error"),
            message=response.get("message", "Completed"),
            details=response
        )
        
    except CoSecException as e:
        logger.error(f"Application error: {e.message} (code: {e.code})")
        return ChatResponse(
            status="error",
            message=e.message,
            details={
                "error_code": e.code,
                "error_details": e.details
            }
        )
        
    except Exception as e:
        logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
        
        return ChatResponse(
            status="error",
            message="An unexpected error occurred. Please try again.",
            details={
                "error_type": type(e).__name__,
                "error_message": str(e) if DEBUG_MODE else None
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug" if DEBUG_MODE else "info"
    )