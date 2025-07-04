"""
Middleware for authentication, rate limiting, and request processing.
"""

import time
import json
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from ..utils.auth import decode_token, TokenData
from ..utils.validators import check_rate_limit as validate_rate_limit
from ..utils.logger import (
    api_logger, security_logger, set_request_id, set_session_id,
    set_user_id, clear_context, log_api_request, log_api_response,
    log_security_event
)


# Security scheme
security = HTTPBearer()


# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    headers_enabled=True
)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication."""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/api/health/cors",
            "/api/health/test-logging",
            "/docs",
            "/openapi.json",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication."""
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Skip for WebSocket (handled separately)
        if request.url.path == "/ws":
            return await call_next(request)
        
        # Extract token
        authorization = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization header"}
            )
        
        token = authorization.split(" ")[1]
        
        try:
            # Decode token
            token_data = decode_token(token)
            
            # Store in request state
            request.state.token_data = token_data
            request.state.user_id = token_data.user_id
            
            # Set logging context
            if token_data.session_id:
                set_session_id(token_data.session_id)
            set_user_id(token_data.user_id)
            
            # Process request
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            api_logger.error(f"Authentication error: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication failed"}
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Custom rate limiting middleware with Redis backend."""
    
    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self._redis = None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get identifier (user_id if authenticated, IP otherwise)
        identifier = getattr(request.state, "user_id", None) or get_remote_address(request)
        
        # Check rate limit using Redis
        try:
            # Lazy load Redis
            if self._redis is None:
                from ..storage import get_redis
                self._redis = await get_redis()
            
            is_allowed, requests_made = await self._redis.check_rate_limit(
                identifier=identifier,
                limit=self.requests_per_minute,
                window_seconds=60
            )
            
            if not is_allowed:
                # Log rate limit violation
                log_security_event(
                    event_type="rate_limit_exceeded",
                    severity="medium",
                    details={
                        "identifier": identifier,
                        "requests_made": requests_made,
                        "limit": self.requests_per_minute
                    },
                    user_ip=get_remote_address(request)
                )
                
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded. Please try again later."},
                    headers={
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 60)
                    }
                )
            
            # Add rate limit headers
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(
                self.requests_per_minute - requests_made
            )
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
            
            return response
            
        except Exception as e:
            api_logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
            return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with logging."""
        # Generate request ID
        request_id = f"req_{uuid4().hex[:12]}"
        request.state.request_id = request_id
        set_request_id(request_id)
        
        # Start timer
        start_time = time.time()
        
        # Get request body size (if available)
        body_size = None
        if request.headers.get("content-length"):
            body_size = int(request.headers["content-length"])
        
        # Log request
        log_api_request(
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            body_size=body_size,
            client_ip=get_remote_address(request)
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_api_response(
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Log error response
            response_time_ms = (time.time() - start_time) * 1000
            log_api_response(
                status_code=500,
                response_time_ms=response_time_ms,
                error=str(e)
            )
            raise
        finally:
            # Clear context
            clear_context()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add CSP header (adjust based on your needs)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' wss: https:;"
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors consistently."""
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Let FastAPI handle HTTP exceptions
            raise
        except Exception as e:
            # Log unexpected errors
            api_logger.error(
                f"Unhandled error: {e}",
                exc_info=True,
                request_id=getattr(request.state, "request_id", None),
                path=str(request.url.path)
            )
            
            # Return generic error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "An internal error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )


def setup_middleware(app):
    """Setup all middleware for the application."""
    # Import settings to get CORS origins
    from ..config.settings import get_settings
    settings = get_settings()
    
    # Log CORS configuration
    from ..utils.logger import logger
    logger.info(f"Setting up CORS middleware with origins: {settings.cors_origins}")
    logger.info("[DEBUG] Middleware setup order (outer to inner):")
    
    # CORS middleware (configure based on your frontend)
    logger.info("[DEBUG] 1. Adding CORSMiddleware (handles OPTIONS preflight)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # Read from settings/environment
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
        max_age=3600  # Cache preflight requests for 1 hour
    )
    
    # Add custom middleware in order (outer to inner)
    logger.info("[DEBUG] 2. Adding ErrorHandlingMiddleware")
    app.add_middleware(ErrorHandlingMiddleware)
    logger.info("[DEBUG] 3. Adding SecurityHeadersMiddleware")
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("[DEBUG] 4. Adding LoggingMiddleware")
    app.add_middleware(LoggingMiddleware)
    logger.info("[DEBUG] 5. Adding RateLimitMiddleware")
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10)
    logger.info("[DEBUG] 6. Adding AuthenticationMiddleware (now skips OPTIONS)")
    app.add_middleware(AuthenticationMiddleware)
    
    # Add exception handler for rate limits
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Dependency for getting current user
async def get_current_user(request: Request) -> TokenData:
    """Get current authenticated user from request."""
    if not hasattr(request.state, "token_data"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.token_data


# Export
__all__ = [
    'setup_middleware',
    'get_current_user',
    'limiter',
    'AuthenticationMiddleware',
    'RateLimitMiddleware',
    'LoggingMiddleware',
    'SecurityHeadersMiddleware',
    'ErrorHandlingMiddleware'
]