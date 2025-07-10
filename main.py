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
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Handle WebSocket connections."""
    handler = WebSocketHandler()
    try:
        await websocket.accept()
        logger.info(f"WebSocket connection established for session: {session_id}")
        await handler.handle_connection(websocket, session_id)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        await websocket.close()

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

# API info endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Deckster API",
        "description": "AI-powered presentation generation assistant",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws?session_id={session_id}",
            "health": "/health"
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