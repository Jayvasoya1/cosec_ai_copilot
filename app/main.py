"""
CoSec AI Copilot — FastAPI entry point (LangGraph edition)

Every POST /chat invocation:
  1. Wraps the user's text as a HumanMessage
  2. Invokes the compiled LangGraph with the session's thread_id
     (MemorySaver handles per-session state automatically)
  3. Reads response_status / response_message / response_details
     from the final state and returns a ChatResponse

The graph itself (app/graph/graph.py) owns all pipeline logic.
This file is intentionally thin — only HTTP plumbing lives here.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from langchain_core.messages import HumanMessage

from app.config import validate_config, DEBUG_MODE
from app.graph.graph import graph
from app.logger import logger

try:
    validate_config()
    logger.info("Configuration validated successfully")
except Exception as e:
    logger.critical(f"Configuration error at startup: {e}")
    raise

app = FastAPI(
    title="CoSec AI Copilot",
    description="AI-powered COSEC device control — LangGraph edition",
    version="2.0.0",
    debug=DEBUG_MODE,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    text:       str = Field(..., min_length=1, max_length=5000, description="User's natural language command")
    session_id: str = Field(default="default", description="Unique ID per user/tab — isolates conversation state")

    @validator("text")
    def not_blank(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be whitespace only")
        return v.strip()


class ChatResponse(BaseModel):
    status:  str  = Field(..., description="success | error | need_input | partial_success")
    message: str  = Field(..., description="Human-readable response for the chat UI")
    details: dict = Field(default_factory=dict, description="Structured data (URLs, missing fields, etc.)")


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Liveness check — also used by the frontend status badge."""
    return {
        "status":  "healthy",
        "service": "CoSec AI Copilot",
        "version": "2.0.0",
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Main chat endpoint.

    session_id becomes the LangGraph thread_id.  MemorySaver keeps a separate
    state snapshot per thread_id, so each user/tab gets isolated multi-turn
    context without any global state.
    """
    logger.info(f"=== Chat [{req.session_id}] ===")
    logger.info(f"Input: {req.text}")

    config = {"configurable": {"thread_id": req.session_id}}

    try:
        final_state = graph.invoke(
            {"messages": [HumanMessage(content=req.text)]},
            config=config,
        )

        status  = final_state.get("response_status",  "error")
        message = final_state.get("response_message", "Completed")
        details = final_state.get("response_details") or {}

        logger.info(f"Response [{req.session_id}]: {status} — {message[:80]}")
        logger.info("=== Done ===\n")

        return ChatResponse(status=status, message=message, details=details)

    except Exception as e:
        logger.critical(f"Unhandled error [{req.session_id}]: {e}", exc_info=True)
        return ChatResponse(
            status="error",
            message="An unexpected error occurred. Please try again.",
            details={"error": str(e) if DEBUG_MODE else None},
        )


# ── Static frontend ──────────────────────────────────────────────────────────
# Mounted LAST so all API routes above take priority over static file matching.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug" if DEBUG_MODE else "info",
    )
