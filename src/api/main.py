"""
Main FastAPI application for the presentation generator.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles

from .websocket import websocket_endpoint
from .middleware import setup_middleware, get_current_user
from ..config.settings import get_settings, Settings
from ..storage import get_redis, get_supabase
from ..utils.logger import logger, api_logger
from ..utils.auth import TokenData, create_test_token
from ..models.messages import SystemMessage


# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown tasks.
    """
    # Startup
    logger.info("Starting Presentation Generator API", version=settings.app_version)
    
    try:
        # Initialize Redis connection
        redis = await get_redis()
        await redis.health_check()
        logger.info("Redis connection established")
        
        # Initialize Supabase connection
        supabase = get_supabase()
        await supabase.health_check()
        logger.info("Supabase connection established")
        
        # Start background tasks
        asyncio.create_task(cleanup_expired_sessions())
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Presentation Generator API")
    
    try:
        # Close Redis connection
        redis = await get_redis()
        await redis.disconnect()
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered presentation generation API with WebSocket support",
    lifespan=lifespan,
    docs_url=None,  # Disable default docs
    redoc_url=None,  # Disable redoc
    openapi_url="/api/openapi.json" if settings.debug else None
)

# Setup middleware
setup_middleware(app)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    Checks all critical services.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check Redis
    try:
        redis = await get_redis()
        redis_healthy = await redis.health_check()
        health_status["services"]["redis"] = "healthy" if redis_healthy else "unhealthy"
    except Exception as e:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Supabase
    try:
        supabase = get_supabase()
        supabase_healthy = await supabase.health_check()
        health_status["services"]["supabase"] = "healthy" if supabase_healthy else "unhealthy"
    except Exception as e:
        health_status["services"]["supabase"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


# API Info endpoint
@app.get("/api/info", dependencies=[Depends(get_current_user)])
async def api_info(current_user: TokenData = Depends(get_current_user)):
    """Get API information."""
    return {
        "version": settings.app_version,
        "environment": settings.app_env,
        "user_id": current_user.user_id,
        "features": {
            "websocket": True,
            "max_file_size_mb": settings.max_file_size_mb,
            "rate_limit": {
                "requests": settings.rate_limit_requests,
                "period_seconds": settings.rate_limit_period
            }
        }
    }


# Session endpoints
@app.get("/api/sessions/current", dependencies=[Depends(get_current_user)])
async def get_current_session(current_user: TokenData = Depends(get_current_user)):
    """Get current session information."""
    if not current_user.session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active session"
        )
    
    supabase = get_supabase()
    session = await supabase.get_session(current_user.session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    return session


@app.post("/api/sessions", dependencies=[Depends(get_current_user)])
async def create_session(current_user: TokenData = Depends(get_current_user)):
    """Create a new session."""
    from uuid import uuid4
    
    session_id = f"session_{uuid4().hex[:12]}"
    
    supabase = get_supabase()
    session = await supabase.create_session(
        session_id=session_id,
        user_id=current_user.user_id,
        expires_hours=24
    )
    
    return {
        "session_id": session_id,
        "created_at": session["created_at"],
        "expires_at": session["expires_at"]
    }


# Presentation endpoints
@app.get("/api/presentations", dependencies=[Depends(get_current_user)])
async def list_presentations(
    current_user: TokenData = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """List user's presentations."""
    # This would be implemented with proper pagination
    return {
        "presentations": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/presentations/{presentation_id}", dependencies=[Depends(get_current_user)])
async def get_presentation(
    presentation_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get a specific presentation."""
    supabase = get_supabase()
    presentation = await supabase.get_presentation(presentation_id)
    
    if not presentation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Presentation not found"
        )
    
    # Verify ownership through session
    # This would need proper implementation
    
    return presentation


# WebSocket endpoint
app.add_api_websocket_route("/ws", websocket_endpoint)


# Documentation endpoint (only in debug mode)
if settings.debug:
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Serve Swagger UI."""
        return get_swagger_ui_html(
            openapi_url="/api/openapi.json",
            title=f"{settings.app_name} - API Docs"
        )


# Development endpoints (only in development mode)
if settings.is_development:
    @app.post("/api/dev/token")
    async def create_dev_token(user_id: str = "test_user"):
        """Create a development token for testing."""
        token = create_test_token(user_id=user_id)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "note": "This endpoint is only available in development mode"
        }
    
    @app.post("/api/dev/clear-cache")
    async def clear_cache():
        """Clear all cache entries."""
        redis = await get_redis()
        # Implementation would clear specific namespaces
        return {"message": "Cache cleared"}


# Background tasks
async def cleanup_expired_sessions():
    """Background task to cleanup expired sessions."""
    while True:
        try:
            await asyncio.sleep(settings.session_cleanup_interval)
            
            supabase = get_supabase()
            cleaned = await supabase.cleanup_expired_sessions()
            
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired sessions")
                
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    api_logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Export app for running
__all__ = ['app']