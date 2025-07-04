"""
Root-level entry point for Railway deployment.
This matches the pattern from the working vibe-decker-api-ver-3.
"""

# Import the FastAPI app from the src module
from src.api.main import app

# This allows Railway to run: uvicorn main:app
__all__ = ['app']