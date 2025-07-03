"""
JWT authentication utilities for the presentation generator.
Handles token creation, validation, and WebSocket authentication.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Union, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import secrets
from fastapi import HTTPException, status, WebSocket, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


# Models
class TokenData(BaseModel):
    """JWT token payload data."""
    user_id: str
    session_id: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    issued_at: datetime


class UserCredentials(BaseModel):
    """User credentials for authentication."""
    email: str
    password: str


class User(BaseModel):
    """User model for authentication."""
    user_id: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    roles: List[str] = Field(default_factory=lambda: ["user"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# JWT utilities
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    
    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    # Create token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Extract token data
        token_data = TokenData(
            user_id=payload.get("user_id"),
            session_id=payload.get("session_id"),
            email=payload.get("email"),
            roles=payload.get("roles", []),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            metadata=payload.get("metadata", {})
        )
        
        if not token_data.user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )
        
        return token_data
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def validate_token(token: str) -> bool:
    """
    Validate a JWT token without raising exceptions.
    
    Args:
        token: JWT token to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        decode_token(token)
        return True
    except HTTPException:
        return False


# Token generation helpers
def generate_user_token(user: User, session_id: Optional[str] = None) -> Token:
    """
    Generate a token for a user.
    
    Args:
        user: User object
        session_id: Optional session ID to include in token
        
    Returns:
        Token object with access token and metadata
    """
    # Token data
    token_data = {
        "user_id": user.user_id,
        "email": user.email,
        "roles": user.roles,
        "metadata": user.metadata
    }
    
    if session_id:
        token_data["session_id"] = session_id
    
    # Create token
    access_token = create_access_token(token_data)
    
    return Token(
        access_token=access_token,
        expires_in=JWT_EXPIRY_HOURS * 3600,
        issued_at=datetime.now(timezone.utc)
    )


# WebSocket authentication
async def get_jwt_from_websocket(websocket: WebSocket) -> Optional[str]:
    """
    Extract JWT token from WebSocket connection.
    
    First checks headers, then waits for first message with token.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        JWT token string or None
    """
    # Check Authorization header
    auth_header = websocket.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]
    
    # Check custom header (some WebSocket clients don't support Authorization header)
    token_header = websocket.headers.get("x-auth-token")
    if token_header:
        return token_header
    
    # Check query parameters (fallback for clients that can't set headers)
    token_param = websocket.query_params.get("token")
    if token_param:
        return token_param
    
    # Wait for first message with token
    try:
        first_message = await websocket.receive_json()
        return first_message.get("token")
    except Exception:
        return None


async def authenticate_websocket(websocket: WebSocket) -> TokenData:
    """
    Authenticate a WebSocket connection.
    
    Args:
        websocket: WebSocket connection to authenticate
        
    Returns:
        Decoded token data
        
    Raises:
        Exception: If authentication fails
    """
    token = await get_jwt_from_websocket(websocket)
    
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        raise Exception("No authentication token provided")
    
    try:
        token_data = decode_token(token)
        return token_data
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        raise Exception(f"Authentication failed: {e.detail}")


# HTTP authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = security
) -> TokenData:
    """
    Get current user from JWT token in HTTP request.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return decode_token(token)


# Role-based access control
def require_roles(required_roles: List[str]):
    """
    Decorator to require specific roles for an endpoint.
    
    Args:
        required_roles: List of roles required (user must have at least one)
    """
    async def role_checker(token_data: TokenData = Depends(get_current_user)):
        user_roles = set(token_data.roles)
        required = set(required_roles)
        
        if not user_roles.intersection(required):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        
        return token_data
    
    return role_checker


# Session token utilities
def create_session_token(
    user_id: str,
    session_id: str,
    additional_data: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a session-specific token.
    
    Args:
        user_id: User ID
        session_id: Session ID
        additional_data: Optional additional data to include
        
    Returns:
        Encoded JWT token
    """
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "type": "session"
    }
    
    if additional_data:
        data["metadata"] = additional_data
    
    return create_access_token(data)


def validate_session_token(token: str, expected_session_id: str) -> bool:
    """
    Validate a session token and check session ID.
    
    Args:
        token: JWT token
        expected_session_id: Expected session ID
        
    Returns:
        True if valid and session ID matches
    """
    try:
        token_data = decode_token(token)
        return token_data.session_id == expected_session_id
    except HTTPException:
        return False


# Utility functions
def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(length)


def is_token_expired(token: str) -> bool:
    """
    Check if a token is expired without raising exceptions.
    
    Args:
        token: JWT token to check
        
    Returns:
        True if expired, False if valid
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}  # Decode without verifying expiration
        )
        
        exp = payload.get("exp")
        if not exp:
            return True
        
        # Check expiration
        expiration = datetime.fromtimestamp(exp, tz=timezone.utc)
        return expiration <= datetime.now(timezone.utc)
        
    except JWTError:
        return True


def refresh_token_if_needed(
    token: str,
    refresh_threshold_hours: int = 1
) -> Optional[str]:
    """
    Refresh a token if it's close to expiration.
    
    Args:
        token: Current JWT token
        refresh_threshold_hours: Hours before expiration to refresh
        
    Returns:
        New token if refreshed, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        
        exp = payload.get("exp")
        if not exp:
            return None
        
        expiration = datetime.fromtimestamp(exp, tz=timezone.utc)
        time_until_expiry = expiration - datetime.now(timezone.utc)
        
        # Refresh if within threshold
        if time_until_expiry <= timedelta(hours=refresh_threshold_hours):
            # Remove old expiration claims
            payload.pop("exp", None)
            payload.pop("iat", None)
            
            # Create new token
            return create_access_token(payload)
        
        return None
        
    except JWTError:
        return None


# Development/testing utilities
def create_test_token(
    user_id: str = "test_user",
    roles: List[str] = None,
    expired: bool = False
) -> str:
    """
    Create a test token for development/testing.
    
    Args:
        user_id: Test user ID
        roles: User roles
        expired: Whether to create an expired token
        
    Returns:
        JWT token for testing
    """
    if roles is None:
        roles = ["user"]
    
    data = {
        "user_id": user_id,
        "email": f"{user_id}@test.com",
        "roles": roles,
        "metadata": {"test": True}
    }
    
    if expired:
        expires_delta = timedelta(hours=-1)  # Already expired
    else:
        expires_delta = None  # Use default
    
    return create_access_token(data, expires_delta)