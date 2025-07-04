"""
Debug version of main.py with detailed error logging.
Use this temporarily to get better error messages from Railway.
"""

import sys
import traceback

print("=== RAILWAY DEBUG MODE ===")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[:2]}")

try:
    print("\n1. Attempting to import from src.api.main...")
    from src.api.main import app
    print("   ✓ Import successful!")
    
except ImportError as e:
    print(f"   ✗ ImportError: {e}")
    print("\n2. Trying to trace the import chain...")
    
    # Test each import level
    try:
        print("   - Testing: import src")
        import src
        print("     ✓ src imported")
    except Exception as e2:
        print(f"     ✗ src failed: {e2}")
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("   - Testing: import src.api")
        import src.api
        print("     ✓ src.api imported")
    except Exception as e2:
        print(f"     ✗ src.api failed: {e2}")
        print("\n   Checking src.__init__.py imports...")
        try:
            # Check what's failing in src/__init__.py
            print("     - Testing individual imports from src/__init__.py")
            from src.api.main import app as test_app
            print("       ✓ Direct import works")
        except Exception as e3:
            print(f"       ✗ Direct import failed: {e3}")
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("   - Testing: import src.api.main")
        import src.api.main
        print("     ✓ src.api.main imported")
    except Exception as e2:
        print(f"     ✗ src.api.main failed: {e2}")
        print("\n   This is likely where the issue is. Full traceback:")
        traceback.print_exc()
        
        # Try to identify specific missing imports
        print("\n3. Testing specific imports that might be failing...")
        test_imports = [
            "src.api.websocket",
            "src.api.middleware", 
            "src.config.settings",
            "src.storage",
            "src.utils.logger",
            "src.utils.auth",
            "src.models.messages"
        ]
        
        for imp in test_imports:
            try:
                exec(f"import {imp}")
                print(f"   ✓ {imp}")
            except Exception as e3:
                print(f"   ✗ {imp}: {e3}")
        
        sys.exit(1)

except Exception as e:
    print(f"   ✗ Unexpected error: {type(e).__name__}: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)

print("\n=== APP LOADED SUCCESSFULLY ===")
print("Railway should be able to start the application")

# Export the app
__all__ = ['app']