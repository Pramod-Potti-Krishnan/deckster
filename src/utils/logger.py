"""
Logging configuration using LogFire for the presentation generator.
Provides structured logging with observability features.
"""

import os
import sys
import json
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from contextvars import ContextVar
from functools import wraps
import asyncio
import time

# Optional import - logfire for observability
try:
    import logfire
    from logfire import Logger
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    print("Warning: logfire not available, using standard logging")
    import logging
    logging.basicConfig(level=logging.INFO)

from pydantic import BaseModel


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar('session_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
agent_id_var: ContextVar[Optional[str]] = ContextVar('agent_id', default=None)


# Configuration
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")
LOGFIRE_PROJECT = os.getenv("LOGFIRE_PROJECT", "presentation-generator")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
APP_ENV = os.getenv("APP_ENV", "development")


# Initialize LogFire or fallback logger
if LOGFIRE_AVAILABLE:
    if LOGFIRE_TOKEN:
        logfire.configure(
            token=LOGFIRE_TOKEN,
            project_name=LOGFIRE_PROJECT,
            environment=APP_ENV,
            console=APP_ENV == "development",  # Console output in development
            service_name="presentation-generator-api"
        )
    else:
        # Fallback to console logging if no LogFire token
        logfire.configure(
            console=True,
            service_name="presentation-generator-api"
        )
else:
    # Create a mock logfire object for compatibility
    class MockLogfire:
        def __getattr__(self, name):
            return logging.getLogger("presentation-generator")
    
    logfire = MockLogfire()


# Create logger instances
# Note: logfire doesn't have get_logger method, using logfire directly
logger = logfire
agent_logger = logfire
api_logger = logfire
storage_logger = logfire
security_logger = logfire


# Structured log models
class LogContext(BaseModel):
    """Standard context for all log entries."""
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: datetime = None
    environment: str = APP_ENV
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Auto-populate from context vars if not provided
        if self.request_id is None:
            self.request_id = request_id_var.get()
        if self.session_id is None:
            self.session_id = session_id_var.get()
        if self.user_id is None:
            self.user_id = user_id_var.get()
        if self.agent_id is None:
            self.agent_id = agent_id_var.get()


class APIRequestLog(BaseModel):
    """API request log entry."""
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    body_size: Optional[int] = None
    client_ip: Optional[str] = None


class APIResponseLog(BaseModel):
    """API response log entry."""
    status_code: int
    response_time_ms: float
    body_size: Optional[int] = None
    error: Optional[str] = None


class AgentRequestLog(BaseModel):
    """Agent request log entry."""
    agent_name: str
    action: str
    input_data: Dict[str, Any]
    correlation_id: str


class AgentResponseLog(BaseModel):
    """Agent response log entry."""
    agent_name: str
    status: str
    processing_time_ms: float
    output_summary: Dict[str, Any]
    tokens_used: Optional[Dict[str, int]] = None
    cost_estimate: Optional[float] = None
    error: Optional[str] = None


class LLMCallLog(BaseModel):
    """LLM API call log entry."""
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost: float
    temperature: Optional[float] = None
    error: Optional[str] = None


# Logging functions
def get_context() -> LogContext:
    """Get current logging context."""
    return LogContext()


def log_api_request(
    method: str,
    path: str,
    headers: Dict[str, str],
    query_params: Optional[Dict[str, str]] = None,
    body_size: Optional[int] = None,
    client_ip: Optional[str] = None
):
    """Log an API request."""
    context = get_context()
    request_log = APIRequestLog(
        method=method,
        path=path,
        headers={k: v for k, v in headers.items() if k.lower() != 'authorization'},
        query_params=query_params or {},
        body_size=body_size,
        client_ip=client_ip
    )
    
    api_logger.info(
        f"API Request: {method} {path}",
        context=context.model_dump(),
        request=request_log.model_dump()
    )


def log_api_response(
    status_code: int,
    response_time_ms: float,
    body_size: Optional[int] = None,
    error: Optional[str] = None
):
    """Log an API response."""
    context = get_context()
    response_log = APIResponseLog(
        status_code=status_code,
        response_time_ms=response_time_ms,
        body_size=body_size,
        error=error
    )
    
    level = "error" if status_code >= 500 else "warn" if status_code >= 400 else "info"
    getattr(api_logger, level)(
        f"API Response: {status_code}",
        context=context.model_dump(),
        response=response_log.model_dump()
    )


def log_agent_request(
    agent_name: str,
    action: str,
    input_data: Dict[str, Any],
    correlation_id: str
):
    """Log an agent request."""
    context = get_context()
    agent_log = AgentRequestLog(
        agent_name=agent_name,
        action=action,
        input_data=input_data,
        correlation_id=correlation_id
    )
    
    agent_logger.info(
        f"Agent Request: {agent_name}.{action}",
        context=context.model_dump(),
        agent_request=agent_log.model_dump()
    )


def log_agent_response(
    agent_name: str,
    status: str,
    processing_time_ms: float,
    output_summary: Dict[str, Any],
    tokens_used: Optional[Dict[str, int]] = None,
    error: Optional[str] = None
):
    """Log an agent response."""
    context = get_context()
    
    # Calculate cost estimate if tokens provided
    cost_estimate = None
    if tokens_used:
        # Rough cost estimates (update with actual pricing)
        cost_per_1k_prompt = 0.01
        cost_per_1k_completion = 0.03
        cost_estimate = (
            (tokens_used.get('prompt_tokens', 0) / 1000 * cost_per_1k_prompt) +
            (tokens_used.get('completion_tokens', 0) / 1000 * cost_per_1k_completion)
        )
    
    agent_log = AgentResponseLog(
        agent_name=agent_name,
        status=status,
        processing_time_ms=processing_time_ms,
        output_summary=output_summary,
        tokens_used=tokens_used,
        cost_estimate=cost_estimate,
        error=error
    )
    
    level = "error" if status == "failed" else "info"
    getattr(agent_logger, level)(
        f"Agent Response: {agent_name} - {status}",
        context=context.model_dump(),
        agent_response=agent_log.model_dump()
    )


def log_llm_call(
    model: str,
    provider: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    temperature: Optional[float] = None,
    error: Optional[str] = None
):
    """Log an LLM API call."""
    context = get_context()
    
    # Calculate cost based on model
    cost_mapping = {
        "gpt-4": (0.03, 0.06),  # (prompt, completion) per 1k tokens
        "gpt-3.5-turbo": (0.001, 0.002),
        "claude-3-opus": (0.015, 0.075),
        "claude-3-sonnet": (0.003, 0.015),
    }
    
    costs = cost_mapping.get(model, (0.01, 0.01))
    total_cost = (prompt_tokens / 1000 * costs[0]) + (completion_tokens / 1000 * costs[1])
    
    llm_log = LLMCallLog(
        model=model,
        provider=provider,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        latency_ms=latency_ms,
        cost=total_cost,
        temperature=temperature,
        error=error
    )
    
    agent_logger.info(
        f"LLM Call: {provider}/{model}",
        context=context.model_dump(),
        llm_call=llm_log.model_dump()
    )


def log_error(
    error: Exception,
    error_type: str = "general",
    additional_context: Optional[Dict[str, Any]] = None
):
    """Log an error with full context."""
    context = get_context()
    
    error_info = {
        "error_type": error_type,
        "error_class": error.__class__.__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "additional_context": additional_context or {}
    }
    
    logger.error(
        f"Error: {error_type} - {error.__class__.__name__}",
        context=context.model_dump(),
        error=error_info,
        exc_info=True
    )


def log_security_event(
    event_type: str,
    severity: str,  # low, medium, high, critical
    details: Dict[str, Any],
    user_ip: Optional[str] = None
):
    """Log a security event."""
    context = get_context()
    
    security_event = {
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "user_ip": user_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    security_logger.warning(
        f"Security Event: {event_type} ({severity})",
        context=context.model_dump(),
        security=security_event
    )


# Decorators
def log_execution_time(func_name: Optional[str] = None):
    """Decorator to log function execution time."""
    def decorator(func):
        name = func_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            context = get_context()
            
            try:
                result = await func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                logger.debug(
                    f"Function executed: {name}",
                    context=context.model_dump(),
                    execution_time_ms=execution_time
                )
                
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Function failed: {name}",
                    context=context.model_dump(),
                    execution_time_ms=execution_time,
                    error=str(e),
                    exc_info=True
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            context = get_context()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                logger.debug(
                    f"Function executed: {name}",
                    context=context.model_dump(),
                    execution_time_ms=execution_time
                )
                
                return result
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                
                logger.error(
                    f"Function failed: {name}",
                    context=context.model_dump(),
                    execution_time_ms=execution_time,
                    error=str(e),
                    exc_info=True
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def with_logging_context(**context_kwargs):
    """Decorator to set logging context for a function."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Set context variables
            tokens = []
            for key, value in context_kwargs.items():
                if key == 'request_id' and value:
                    tokens.append(request_id_var.set(value))
                elif key == 'session_id' and value:
                    tokens.append(session_id_var.set(value))
                elif key == 'user_id' and value:
                    tokens.append(user_id_var.set(value))
                elif key == 'agent_id' and value:
                    tokens.append(agent_id_var.set(value))
            
            try:
                return await func(*args, **kwargs)
            finally:
                # Reset context variables
                for token in tokens:
                    token.var.reset(token)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Set context variables
            tokens = []
            for key, value in context_kwargs.items():
                if key == 'request_id' and value:
                    tokens.append(request_id_var.set(value))
                elif key == 'session_id' and value:
                    tokens.append(session_id_var.set(value))
                elif key == 'user_id' and value:
                    tokens.append(user_id_var.set(value))
                elif key == 'agent_id' and value:
                    tokens.append(agent_id_var.set(value))
            
            try:
                return func(*args, **kwargs)
            finally:
                # Reset context variables
                for token in tokens:
                    token.var.reset(token)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


# Utility functions
def set_request_id(request_id: str):
    """Set the current request ID."""
    request_id_var.set(request_id)


def set_session_id(session_id: str):
    """Set the current session ID."""
    session_id_var.set(session_id)


def set_user_id(user_id: str):
    """Set the current user ID."""
    user_id_var.set(user_id)


def set_agent_id(agent_id: str):
    """Set the current agent ID."""
    agent_id_var.set(agent_id)


def get_request_id() -> Optional[str]:
    """Get the current request ID."""
    return request_id_var.get()


def clear_context():
    """Clear all context variables."""
    request_id_var.set(None)
    session_id_var.set(None)
    user_id_var.set(None)
    agent_id_var.set(None)


# Export main components
__all__ = [
    'logger',
    'agent_logger',
    'api_logger',
    'storage_logger',
    'security_logger',
    'log_api_request',
    'log_api_response',
    'log_agent_request',
    'log_agent_response',
    'log_llm_call',
    'log_error',
    'log_security_event',
    'log_execution_time',
    'with_logging_context',
    'set_request_id',
    'set_session_id',
    'set_user_id',
    'set_agent_id',
    'get_request_id',
    'clear_context'
]