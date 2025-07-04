#!/usr/bin/env python
"""
Test logger initialization to debug Railway deployment issues.
Run with and without LOGFIRE_TOKEN to test both scenarios.
"""

import os
import sys

# Test 1: Check if logfire can be imported
print("=== TEST 1: Import logfire ===")
try:
    import logfire
    print("✓ logfire imported successfully")
    print(f"  Version: {logfire.__version__ if hasattr(logfire, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"✗ Failed to import logfire: {e}")
    print("  This explains 'Warning: logfire not available'")

# Test 2: Check environment variables
print("\n=== TEST 2: Environment Variables ===")
env_vars = {
    'LOGFIRE_TOKEN': os.getenv('LOGFIRE_TOKEN'),
    'LOGFIRE_PROJECT': os.getenv('LOGFIRE_PROJECT', 'presentation-generator'),
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'APP_ENV': os.getenv('APP_ENV', 'development')
}

for key, value in env_vars.items():
    if value and key == 'LOGFIRE_TOKEN':
        print(f"{key}: {'*' * 10} (hidden)")
    else:
        print(f"{key}: {value}")

# Test 3: Import our logger module
print("\n=== TEST 3: Import Logger Module ===")
try:
    from src.utils.logger import logger, LOGFIRE_AVAILABLE
    print(f"✓ Logger imported successfully")
    print(f"  LOGFIRE_AVAILABLE: {LOGFIRE_AVAILABLE}")
    print(f"  Logger type: {type(logger)}")
    print(f"  Logger object: {logger}")
except Exception as e:
    print(f"✗ Failed to import logger: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test the exact failing call
print("\n=== TEST 4: Test Logger Call ===")
try:
    # This is the exact call that's failing in main.py
    class MockSettings:
        app_version = "1.0.0"
    
    settings = MockSettings()
    
    print("Testing: logger.info('Starting...', version=settings.app_version)")
    
    # Try different approaches
    try:
        # Original approach (failing)
        logger.info("Starting Presentation Generator API", version=settings.app_version)
        print("✓ Logfire-style call succeeded")
    except TypeError as e:
        print(f"✗ Logfire-style call failed: {e}")
        
        # Try standard logger approach
        print("\nTrying standard logger approach...")
        if hasattr(logger, 'info') and callable(getattr(logger, 'info')):
            logger.info(f"Starting Presentation Generator API - version={settings.app_version}")
            print("✓ Standard logger call succeeded")
        else:
            print(f"✗ logger.info is not callable. Logger attributes: {dir(logger)}")

except Exception as e:
    print(f"✗ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check logger configuration
print("\n=== TEST 5: Logger Configuration ===")
if LOGFIRE_AVAILABLE:
    print("Logfire is available - checking configuration")
    if hasattr(logfire, 'DEFAULT_LOGFIRE_INSTANCE'):
        print(f"  Default instance: {logfire.DEFAULT_LOGFIRE_INSTANCE}")
else:
    print("Logfire not available - using fallback")
    print(f"  Logger class: {logger.__class__}")
    print(f"  Logger methods: {[m for m in dir(logger) if not m.startswith('_')]}")

# Test 6: Suggest fixes
print("\n=== RECOMMENDATIONS ===")
if not LOGFIRE_AVAILABLE:
    print("1. Logfire is not available. Possible causes:")
    print("   - Package not installed (check requirements.txt)")
    print("   - Import error (check dependencies)")
    print("   - Need to fix MockLogfire class to handle logfire API")
    print("\n2. Quick fix: Update MockLogfire in logger.py to handle keyword args")
else:
    print("1. Logfire is available but might not be configured properly")
    print("2. Check if LOGFIRE_TOKEN is set correctly")

print("\nTo test without logfire:")
print("  1. Rename .env: mv .env .env.backup")
print("  2. Run this script again")
print("  3. Restore: mv .env.backup .env")