"""
Deckster - AI Presentation Assistant
Main entry point for the application.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logfire early in startup
from src.utils.logfire_config import configure_logfire
configure_logfire()

from src.handlers.websocket import WebSocketHandler
from src.utils.logger import setup_logger
from config.settings import get_settings

# Initialize
logger = setup_logger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    logger.info("Starting Deckster API...")
    
    # Validate required configurations
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        logger.error("FATAL: Supabase configuration missing!")
        logger.error("Please set the following environment variables in your .env file:")
        logger.error("  SUPABASE_URL=https://your-project.supabase.co")
        logger.error("  SUPABASE_ANON_KEY=your-anon-key-here")
        logger.error("Get these values from your Supabase project settings.")
        raise RuntimeError("Cannot start without Supabase configuration. See logs for details.")
    
    # Validate AI API keys
    try:
        settings.validate_settings()
        logger.info("✓ AI API key configuration validated")
    except ValueError as e:
        logger.error(f"FATAL: {str(e)}")
        logger.error("Please set at least one of these in your .env file:")
        logger.error("  GOOGLE_API_KEY=your-key-here")
        logger.error("  OPENAI_API_KEY=sk-...")
        logger.error("  ANTHROPIC_API_KEY=sk-ant-...")
        raise RuntimeError("Cannot start without AI API configuration. See logs for details.")
    
    # Validate Supabase connection
    from src.storage.supabase import get_supabase_client
    try:
        client = get_supabase_client()
        logger.info("✓ Supabase connection validated")
    except Exception as e:
        logger.error(f"FATAL: Failed to connect to Supabase: {str(e)}")
        raise RuntimeError("Cannot start without valid Supabase connection.")
    
    yield
    logger.info("Shutting down Deckster API...")

app = FastAPI(
    title="Deckster API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://www.deckster.xyz",
        "https://deckster.xyz",
        "http://localhost:3000",  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str, user_id: str):
    """Handle WebSocket connections with user authentication."""
    # Validate parameters
    if not session_id or not user_id:
        logger.error("WebSocket connection attempted without session_id or user_id")
        await websocket.close(code=1008, reason="Missing required parameters")
        return
        
    print(f"[DEBUG] Attempting to initialize WebSocketHandler for session: {session_id}")
    try:
        handler = WebSocketHandler()
        print("[DEBUG] WebSocketHandler initialized successfully")
    except Exception as init_error:
        print(f"[DEBUG] Failed to initialize WebSocketHandler: {str(init_error)}")
        logger.error(f"Failed to initialize WebSocketHandler: {str(init_error)}", exc_info=True)
        await websocket.close(code=1011, reason="Server error during initialization")
        return
        
    try:
        print("[DEBUG] Accepting WebSocket connection")
        await websocket.accept()
        print(f"[DEBUG] WebSocket accepted for user: {user_id}, session: {session_id}")
        logger.info(f"WebSocket connection established for user: {user_id}, session: {session_id}")
        
        # Add explicit error handling for the handler
        try:
            print("[DEBUG] Calling handler.handle_connection")
            await handler.handle_connection(websocket, session_id, user_id)
        except Exception as handler_error:
            print(f"[DEBUG] Handler error: {str(handler_error)}")
            logger.error(f"Handler error for user {user_id}, session {session_id}: {str(handler_error)}", exc_info=True)
            raise
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user: {user_id}, session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}, session {session_id}: {str(e)}", exc_info=True)
        # Connection might already be closed, so wrap in try-except
        try:
            if websocket.client_state.value <= 1:  # CONNECTING=0, CONNECTED=1
                await websocket.close()
        except Exception:
            pass  # Ignore close errors

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "deckster-api",
        "version": "1.0.0",
        "environment": settings.APP_ENV
    }

# Test endpoint for WebSocketHandler initialization
@app.get("/test-handler")
async def test_handler():
    """Test WebSocketHandler initialization."""
    try:
        print("[TEST] Creating WebSocketHandler instance")
        handler = WebSocketHandler()
        print("[TEST] WebSocketHandler created successfully")
        return {
            "status": "success",
            "message": "WebSocketHandler initialized successfully",
            "components": {
                "intent_router": handler.intent_router is not None,
                "director": handler.director is not None,
                "sessions": handler.sessions is not None,
                "packager": handler.packager is not None,
                "streamlined_packager": handler.streamlined_packager is not None,
                "workflow": handler.workflow is not None
            }
        }
    except Exception as e:
        print(f"[TEST] Failed to create WebSocketHandler: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Failed to initialize WebSocketHandler: {str(e)}",
            "error_type": type(e).__name__
        }

# API info endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Deckster API",
        "description": "AI-powered presentation generation assistant",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws?session_id={session_id}&user_id={user_id}",
            "health": "/health",
            "test-handler": "/test-handler"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    log_level = "debug" if settings.DEBUG else "info"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level=log_level,
        reload=settings.DEBUG
    )