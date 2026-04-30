"""
Main FastAPI application for CoSec AI Copilot
Orchestrates the complete request-response flow
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from app.config import validate_config, DEBUG_MODE
from app.core.intent_parser import parse_intent
from app.core.planner import plan_tasks
from app.core.router import route_intent
from app.core.executor import execute_tasks
from app.core.response_builder import build_response
from app.core.memory import memory
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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
        pending = memory.get("pending_intent")
        tasks = None

        # Always try LLM first — a full command overrides any pending state
        try:
            intent_data = parse_intent(user_input)
            tasks = plan_tasks(intent_data)
            if tasks and pending:
                # User typed a new command while a follow-up was pending → discard pending
                logger.info(f"New command received — discarding pending intent '{pending['intent']}'")
                memory.data.pop("pending_intent", None)
                pending = None
        except CoSecException:
            tasks = None  # LLM couldn't extract anything → treat as continuation below

        # If LLM returned nothing AND there is a pending intent → continuation answer
        if not tasks and pending:
            intent  = pending["intent"]
            missing = pending["missing"]
            memory.data.pop("pending_intent", None)
            logger.info(f"Continuing pending intent '{intent}', filling '{missing[0] if missing else '?'}' = '{user_input}'")
            params = {missing[0]: user_input} if missing else {}
            tasks = [{"intent": intent, "parameters": params}]

        if not tasks:
            return ChatResponse(
                status="error",
                message="Could not understand your request. Please try again.",
                details={"reason": "no_tasks_generated"}
            )

        logger.info(f"Planned {len(tasks)} task(s)")

        # Execute tasks (shared path for both normal and continuation)
        logger.debug("Executing tasks...")
        results = execute_tasks(tasks, route_intent)

        # If still need input, save pending state for the next turn
        for result in results:
            if "need_input" in result or result.get("status") == "need_input":
                if result.get("pending_intent"):
                    memory.set("pending_intent", {
                        "intent": result["pending_intent"],
                        "missing": result.get("missing", [])
                    })
                break

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


# Mount frontend LAST — API routes registered above take priority over static files.
# html=True means StaticFiles serves index.html for / and unknown paths.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug" if DEBUG_MODE else "info"
    )