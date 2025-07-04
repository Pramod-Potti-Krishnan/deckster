"""
Compatibility layer for optional dependencies.
Provides fallbacks when certain packages are not available.
"""

import sys
import warnings

# Track available packages
AVAILABLE_PACKAGES = {
    'numpy': False,
    'asyncpg': False,
    'pydantic_ai': False,
    'langchain': False,
    'langgraph': False,
}

# Try importing optional packages
try:
    import numpy
    AVAILABLE_PACKAGES['numpy'] = True
except ImportError:
    warnings.warn("NumPy not available - some features may be limited")
    # Create mock numpy for basic compatibility
    class MockNumpy:
        def array(self, data):
            return data
        def zeros(self, shape):
            return [0] * shape[0] if isinstance(shape, tuple) else [0] * shape
    numpy = MockNumpy()

try:
    import asyncpg
    AVAILABLE_PACKAGES['asyncpg'] = True
except ImportError:
    warnings.warn("AsyncPG not available - using Supabase REST API only")

try:
    import pydantic_ai
    AVAILABLE_PACKAGES['pydantic_ai'] = True
except ImportError:
    warnings.warn("Pydantic AI not available - using fallback agent implementation")

try:
    import langchain
    AVAILABLE_PACKAGES['langchain'] = True
except ImportError:
    warnings.warn("LangChain not available - using direct API calls")

try:
    import langgraph
    AVAILABLE_PACKAGES['langgraph'] = True
except ImportError:
    warnings.warn("LangGraph not available - using simple workflow")

def check_requirements():
    """Check which packages are available."""
    print("Package Availability:")
    print("-" * 30)
    for package, available in AVAILABLE_PACKAGES.items():
        status = "✅" if available else "❌"
        print(f"{status} {package}")
    
    # Check if minimum requirements are met
    core_packages = ['numpy']  # Remove from core if not essential
    missing_core = [p for p in core_packages if not AVAILABLE_PACKAGES[p]]
    
    if missing_core:
        print(f"\n⚠️  Warning: Missing packages: {missing_core}")
        print("The application may have limited functionality.")
    else:
        print("\n✅ All core packages available!")
    
    return len(missing_core) == 0

# Export
__all__ = ['AVAILABLE_PACKAGES', 'check_requirements', 'numpy']