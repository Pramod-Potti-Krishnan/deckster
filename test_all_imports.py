#!/usr/bin/env python
"""
Comprehensive import test that simulates Railway's exact startup sequence.
This will help identify ALL missing dependencies at once.
"""

import sys
import traceback
from pathlib import Path

# Add current directory to Python path (simulating Railway's PYTHONPATH)
sys.path.insert(0, str(Path(__file__).parent))

def test_import_chain():
    """Test the exact import chain that Railway uses."""
    errors = []
    
    print("Testing Railway import chain...\n")
    print("=" * 60)
    
    # Step 1: Test main.py import
    print("1. Testing: import main")
    try:
        import main
        print("   ✓ main imported successfully")
    except Exception as e:
        print(f"   ✗ main import failed: {type(e).__name__}: {e}")
        errors.append(("main", e, traceback.format_exc()))
        return errors  # Can't continue if main fails
    
    # Step 2: Test the app import from main
    print("\n2. Testing: from main import app")
    try:
        from main import app
        print("   ✓ app imported successfully")
    except Exception as e:
        print(f"   ✗ app import failed: {type(e).__name__}: {e}")
        errors.append(("main.app", e, traceback.format_exc()))
        return errors
    
    # Step 3: Test uvicorn's import method
    print("\n3. Testing: uvicorn's import_from_string('main:app')")
    try:
        from uvicorn.importer import import_from_string
        loaded_app = import_from_string("main:app")
        print("   ✓ uvicorn import successful")
    except Exception as e:
        print(f"   ✗ uvicorn import failed: {type(e).__name__}: {e}")
        errors.append(("uvicorn.import", e, traceback.format_exc()))
    
    # Step 4: Test individual module imports
    print("\n4. Testing individual imports:")
    
    test_imports = [
        ("src", "Core src module"),
        ("src.api", "API module"),
        ("src.api.main", "Main API module"),
        ("src.api.websocket", "WebSocket module"),
        ("src.api.middleware", "Middleware module"),
        ("src.config", "Config module"),
        ("src.config.settings", "Settings module"),
        ("src.storage", "Storage module"),
        ("src.storage.redis_cache", "Redis module"),
        ("src.storage.supabase", "Supabase module"),
        ("src.utils", "Utils module"),
        ("src.utils.auth", "Auth utils"),
        ("src.utils.logger", "Logger utils"),
        ("src.utils.validators", "Validators"),
        ("src.models", "Models module"),
        ("src.models.messages", "Message models"),
        ("src.agents", "Agents module"),
        ("src.workflows", "Workflows module"),
    ]
    
    for module_name, description in test_imports:
        try:
            exec(f"import {module_name}")
            print(f"   ✓ {module_name} - {description}")
        except Exception as e:
            print(f"   ✗ {module_name} - {description}: {type(e).__name__}: {e}")
            errors.append((module_name, e, traceback.format_exc()))
    
    return errors

def check_environment():
    """Check environment setup."""
    print("\n5. Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Current directory: {Path.cwd()}")
    print(f"   PYTHONPATH: {sys.path[:3]}...")  # First 3 entries
    
    # Check if we're in the right directory
    expected_files = ["main.py", "src", "requirements.txt", "Dockerfile"]
    missing_files = [f for f in expected_files if not Path(f).exists()]
    if missing_files:
        print(f"   ⚠️  Missing expected files: {missing_files}")
    else:
        print("   ✓ All expected files present")

def main():
    """Run all import tests."""
    print("Railway Import Chain Tester")
    print("This simulates exactly how Railway loads your app")
    print("=" * 60)
    
    # Check environment first
    check_environment()
    
    # Test imports
    errors = test_import_chain()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    if not errors:
        print("✓ All imports successful! Railway should be able to start the app.")
        print("\nIf Railway still fails, the issue might be:")
        print("- Environment variables not set")
        print("- Different Python version")
        print("- System dependencies missing")
    else:
        print(f"✗ Found {len(errors)} import error(s):\n")
        for module, error, _ in errors:
            print(f"  - {module}: {type(error).__name__} - {str(error)[:100]}...")
        
        print("\nDetailed error for first failure:")
        print("-" * 60)
        print(errors[0][2])
        
        print("\nTo fix:")
        print("1. Install missing packages")
        print("2. Check import paths")
        print("3. Verify all dependencies are in requirements-prod.txt")

if __name__ == "__main__":
    main()