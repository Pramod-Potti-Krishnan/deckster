"""
Utilities module for the presentation generator.
Provides authentication, validation, and logging functionality.
"""

from .auth import (
    create_access_token, decode_token, validate_token,
    generate_user_token, authenticate_websocket,
    get_current_user, require_roles
)
from .validators import (
    validate_text_input, validate_prompt_injection,
    validate_file_upload, sanitize_filename,
    validate_url, validate_email, check_rate_limit
)
from .logger import (
    logger, agent_logger, api_logger, storage_logger, security_logger,
    log_api_request, log_api_response, log_agent_request,
    log_agent_response, log_llm_call, log_error,
    log_security_event, log_execution_time,
    set_request_id, set_session_id, set_user_id, set_agent_id
)

__all__ = [
    # Auth
    'create_access_token', 'decode_token', 'validate_token',
    'generate_user_token', 'authenticate_websocket',
    'get_current_user', 'require_roles',
    
    # Validators
    'validate_text_input', 'validate_prompt_injection',
    'validate_file_upload', 'sanitize_filename',
    'validate_url', 'validate_email', 'check_rate_limit',
    
    # Logger
    'logger', 'agent_logger', 'api_logger', 'storage_logger', 'security_logger',
    'log_api_request', 'log_api_response', 'log_agent_request',
    'log_agent_response', 'log_llm_call', 'log_error',
    'log_security_event', 'log_execution_time',
    'set_request_id', 'set_session_id', 'set_user_id', 'set_agent_id'
]