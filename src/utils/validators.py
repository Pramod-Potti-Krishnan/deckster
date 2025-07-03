"""
Input validation utilities for the presentation generator.
Provides security-focused validation for user inputs and file uploads.
"""

import re
import os
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import magic
import hashlib
from datetime import datetime
import json


# Configuration
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {
    ".pdf": ["application/pdf"],
    ".pptx": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
    ".docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    ".xlsx": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
    ".png": ["image/png"],
    ".jpg": ["image/jpeg"],
    ".jpeg": ["image/jpeg"],
    ".gif": ["image/gif"],
    ".svg": ["image/svg+xml"],
    ".csv": ["text/csv", "application/csv"],
    ".txt": ["text/plain"]
}

# Dangerous patterns for prompt injection
DANGEROUS_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s+prompt",
    r"disregard\s+instructions",
    r"forget\s+everything",
    r"new\s+instructions",
    r"<script[^>]*>",
    r"javascript:",
    r"onclick\s*=",
    r"onerror\s*=",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"subprocess",
    r"os\.system"
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    r";\s*DROP\s+TABLE",
    r";\s*DELETE\s+FROM",
    r";\s*UPDATE\s+SET",
    r"UNION\s+SELECT",
    r"OR\s+1\s*=\s*1",
    r"AND\s+1\s*=\s*1",
    r"--\s*$",
    r"/\*.*\*/",
    r"xp_cmdshell",
    r"sp_executesql"
]


# Validation Models
class TextInput(BaseModel):
    """Validated text input."""
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)
    
    @field_validator('text')
    def validate_text(cls, v):
        """Validate text input for security issues."""
        # Check for null bytes
        if '\0' in v:
            raise ValueError("Text contains null bytes")
        
        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Text contains potentially dangerous content")
        
        # Basic XSS prevention
        if any(tag in v.lower() for tag in ['<script', '<iframe', '<object', '<embed']):
            raise ValueError("Text contains potentially dangerous HTML")
        
        return v.strip()


class FileUploadValidation(BaseModel):
    """File upload validation result."""
    is_valid: bool
    filename: str
    file_extension: str
    file_size: int
    mime_type: str
    error_message: Optional[str] = None
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionIdInput(BaseModel):
    """Validated session ID."""
    session_id: str = Field(..., pattern=r'^[a-zA-Z0-9_-]+$', max_length=64)


class PresentationTitleInput(BaseModel):
    """Validated presentation title."""
    title: str = Field(..., min_length=1, max_length=200)
    
    @field_validator('title')
    def validate_title(cls, v):
        """Validate presentation title."""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        
        # Check for special characters that might cause issues
        if re.search(r'[<>:"/\\|?*]', v):
            raise ValueError("Title contains invalid characters")
        
        return v


# Validation Functions
def validate_text_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Validate and sanitize text input.
    
    Args:
        text: Input text to validate
        max_length: Optional custom max length
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If validation fails
    """
    if max_length is None:
        max_length = MAX_TEXT_LENGTH
    
    # Check length
    if len(text) > max_length:
        raise ValueError(f"Text exceeds maximum length of {max_length} characters")
    
    # Use TextInput model for validation
    validated = TextInput(text=text)
    return validated.text


def validate_prompt_injection(text: str) -> bool:
    """
    Check for potential prompt injection attempts.
    
    Args:
        text: Text to check
        
    Returns:
        True if safe, False if potential injection detected
    """
    text_lower = text.lower()
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text_lower):
            return False
    
    # Check for repeated instructions to override
    if text_lower.count("ignore") > 2 or text_lower.count("instructions") > 3:
        return False
    
    # Check for system prompt references
    system_keywords = ["system prompt", "system message", "system:", "assistant:"]
    if any(keyword in text_lower for keyword in system_keywords):
        return False
    
    return True


def validate_sql_injection(text: str) -> bool:
    """
    Check for potential SQL injection attempts.
    
    Args:
        text: Text to check
        
    Returns:
        True if safe, False if potential injection detected
    """
    text_upper = text.upper()
    
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text_upper):
            return False
    
    return True


def validate_file_upload(
    filename: str,
    file_content: bytes,
    allowed_extensions: Optional[Set[str]] = None
) -> FileUploadValidation:
    """
    Validate a file upload for security.
    
    Args:
        filename: Original filename
        file_content: File content as bytes
        allowed_extensions: Optional custom allowed extensions
        
    Returns:
        FileUploadValidation object with results
    """
    # Clean filename
    filename = Path(filename).name
    file_extension = Path(filename).suffix.lower()
    
    # Check extension
    if allowed_extensions is None:
        allowed_extensions = set(ALLOWED_EXTENSIONS.keys())
    
    if file_extension not in allowed_extensions:
        return FileUploadValidation(
            is_valid=False,
            filename=filename,
            file_extension=file_extension,
            file_size=len(file_content),
            mime_type="",
            error_message=f"File type {file_extension} not allowed"
        )
    
    # Check file size
    if len(file_content) > MAX_FILE_SIZE_BYTES:
        return FileUploadValidation(
            is_valid=False,
            filename=filename,
            file_extension=file_extension,
            file_size=len(file_content),
            mime_type="",
            error_message=f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"
        )
    
    # Check MIME type
    mime = magic.Magic(mime=True)
    detected_mime = mime.from_buffer(file_content)
    
    expected_mimes = ALLOWED_EXTENSIONS.get(file_extension, [])
    if detected_mime not in expected_mimes:
        return FileUploadValidation(
            is_valid=False,
            filename=filename,
            file_extension=file_extension,
            file_size=len(file_content),
            mime_type=detected_mime,
            error_message=f"File content does not match extension. Expected {expected_mimes}, got {detected_mime}"
        )
    
    # Calculate file hash
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # Additional checks based on file type
    metadata = {}
    
    if file_extension in ['.png', '.jpg', '.jpeg', '.gif']:
        # Check image dimensions
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(file_content))
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['format'] = img.format
            
            # Check for reasonable dimensions
            if img.width > 10000 or img.height > 10000:
                return FileUploadValidation(
                    is_valid=False,
                    filename=filename,
                    file_extension=file_extension,
                    file_size=len(file_content),
                    mime_type=detected_mime,
                    error_message="Image dimensions too large"
                )
        except Exception:
            return FileUploadValidation(
                is_valid=False,
                filename=filename,
                file_extension=file_extension,
                file_size=len(file_content),
                mime_type=detected_mime,
                error_message="Invalid image file"
            )
    
    return FileUploadValidation(
        is_valid=True,
        filename=filename,
        file_extension=file_extension,
        file_size=len(file_content),
        mime_type=detected_mime,
        file_hash=file_hash,
        metadata=metadata
    )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Get base name
    filename = Path(filename).name
    
    # Remove special characters
    filename = re.sub(r'[^\w\s.-]', '_', filename)
    
    # Replace spaces
    filename = filename.replace(' ', '_')
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return f"{name}{ext}"


def validate_json_structure(
    data: Dict[str, Any],
    required_fields: List[str],
    max_depth: int = 10
) -> bool:
    """
    Validate JSON structure and depth.
    
    Args:
        data: JSON data to validate
        required_fields: Required top-level fields
        max_depth: Maximum nesting depth
        
    Returns:
        True if valid, False otherwise
    """
    # Check required fields
    for field in required_fields:
        if field not in data:
            return False
    
    # Check depth
    def check_depth(obj, current_depth=0):
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            for value in obj.values():
                if not check_depth(value, current_depth + 1):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not check_depth(item, current_depth + 1):
                    return False
        
        return True
    
    return check_depth(data)


def validate_url(url: str) -> bool:
    """
    Validate URL for safety.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid and safe, False otherwise
    """
    # Basic URL pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        return False
    
    # Check for dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:']
    if any(url.lower().startswith(proto) for proto in dangerous_protocols):
        return False
    
    # Check for IP addresses in production
    if os.getenv("APP_ENV") == "production":
        ip_pattern = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
        if ip_pattern.search(url):
            return False
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(email_pattern.match(email))


def validate_color_hex(color: str) -> bool:
    """
    Validate hex color code.
    
    Args:
        color: Color code to validate
        
    Returns:
        True if valid hex color, False otherwise
    """
    hex_pattern = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
    return bool(hex_pattern.match(color))


# Rate limiting helpers
class RateLimitCheck(BaseModel):
    """Rate limit check result."""
    is_allowed: bool
    requests_made: int
    requests_limit: int
    reset_time: datetime
    retry_after: Optional[int] = None  # seconds


def check_rate_limit(
    identifier: str,
    limit: int = 10,
    window_seconds: int = 60,
    storage: Optional[Dict[str, Any]] = None
) -> RateLimitCheck:
    """
    Simple in-memory rate limit check.
    
    Args:
        identifier: Unique identifier (user_id, IP, etc.)
        limit: Request limit
        window_seconds: Time window in seconds
        storage: Optional storage dict (for testing)
        
    Returns:
        RateLimitCheck result
    """
    # Note: In production, use Redis for distributed rate limiting
    if storage is None:
        # This would be replaced with Redis in production
        storage = {}
    
    now = datetime.utcnow()
    window_start = now.timestamp() - window_seconds
    
    # Get or create request history
    if identifier not in storage:
        storage[identifier] = []
    
    # Remove old requests
    storage[identifier] = [
        ts for ts in storage[identifier]
        if ts > window_start
    ]
    
    # Check limit
    requests_made = len(storage[identifier])
    
    if requests_made >= limit:
        reset_time = datetime.fromtimestamp(
            min(storage[identifier]) + window_seconds
        )
        retry_after = int(reset_time.timestamp() - now.timestamp())
        
        return RateLimitCheck(
            is_allowed=False,
            requests_made=requests_made,
            requests_limit=limit,
            reset_time=reset_time,
            retry_after=retry_after
        )
    
    # Add current request
    storage[identifier].append(now.timestamp())
    
    return RateLimitCheck(
        is_allowed=True,
        requests_made=requests_made + 1,
        requests_limit=limit,
        reset_time=datetime.fromtimestamp(now.timestamp() + window_seconds)
    )


# Export commonly used validators
__all__ = [
    'validate_text_input',
    'validate_prompt_injection',
    'validate_sql_injection',
    'validate_file_upload',
    'sanitize_filename',
    'validate_json_structure',
    'validate_url',
    'validate_email',
    'validate_color_hex',
    'check_rate_limit',
    'TextInput',
    'FileUploadValidation',
    'SessionIdInput',
    'PresentationTitleInput',
    'RateLimitCheck'
]