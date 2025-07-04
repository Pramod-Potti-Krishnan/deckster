"""
Minimal FastAPI app for testing Railway deployment.
If this works, we know Railway basics are fine and can add imports gradually.
"""

from fastapi import FastAPI
from datetime import datetime
import os

# Create minimal app
app = FastAPI(
    title="Deckster Minimal Test",
    version="0.0.1",
    description="Testing Railway deployment"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "minimal app running",
        "timestamp": datetime.utcnow().isoformat(),
        "python_version": os.sys.version,
        "env_vars_count": len(os.environ)
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/env-check")
async def env_check():
    """Check which environment variables are set."""
    expected_vars = [
        "JWT_SECRET_KEY",
        "SUPABASE_URL", 
        "REDIS_URL",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY"
    ]
    
    return {
        "set_vars": [var for var in expected_vars if os.getenv(var)],
        "missing_vars": [var for var in expected_vars if not os.getenv(var)],
        "port": os.getenv("PORT", "not set")
    }

# Test imports one by one
@app.get("/test-imports")
async def test_imports():
    """Test importing modules one by one."""
    results = {}
    
    test_modules = [
        "pydantic",
        "redis", 
        "supabase",
        "anthropic",
        "openai",
        "passlib",
        "jose",
        "magic",
        "PIL"
    ]
    
    for module in test_modules:
        try:
            exec(f"import {module}")
            results[module] = "✓ success"
        except ImportError as e:
            results[module] = f"✗ {str(e)}"
        except Exception as e:
            results[module] = f"✗ {type(e).__name__}: {str(e)}"
    
    return results

print("Minimal app created successfully")