"""
API module for the presentation generator.
Provides FastAPI application and WebSocket endpoints.
"""

from .main import app
from .websocket import websocket_endpoint, ConnectionManager
from .middleware import setup_middleware, get_current_user

__all__ = [
    'app',
    'websocket_endpoint',
    'ConnectionManager',
    'setup_middleware',
    'get_current_user'
]