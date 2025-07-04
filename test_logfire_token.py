#!/usr/bin/env python
"""
Test if logfire works WITH token (normal local environment).
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=== Testing Logfire WITH Token ===\n")

# Check environment
print("1. Environment variables:")
token = os.getenv('LOGFIRE_TOKEN')
project = os.getenv('LOGFIRE_PROJECT')
print(f"   LOGFIRE_TOKEN: {'*' * 10 if token else 'NOT SET'}")
print(f"   LOGFIRE_PROJECT: {project or 'NOT SET'}")

# Try to import logfire
print("\n2. Testing logfire import:")
try:
    import logfire
    print("   ✓ logfire package imported successfully")
    print(f"   logfire version: {getattr(logfire, '__version__', 'unknown')}")
except ImportError as e:
    print(f"   ✗ Failed to import logfire: {e}")

# Import our logger
print("\n3. Testing our logger:")
try:
    from src.utils.logger import logger, LOGFIRE_AVAILABLE
    print(f"   ✓ Logger imported")
    print(f"   LOGFIRE_AVAILABLE: {LOGFIRE_AVAILABLE}")
    print(f"   Logger type: {type(logger)}")
    
    # If it's MockLogfire when token exists, something's wrong
    if token and not LOGFIRE_AVAILABLE:
        print("   ⚠️  WARNING: Token exists but logfire not available!")
        print("   Possible issues:")
        print("   - Logfire package not installed correctly")
        print("   - Token format issue")
        print("   - Import error in logfire")
    
    # Test logging
    print("\n4. Testing logger call:")
    logger.info("Test with logfire token", user="test", action="verify")
    print("   ✓ Logger call succeeded")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Summary:")
if LOGFIRE_AVAILABLE:
    print("   ✓ Logfire is working properly locally")
    print("   Railway might have different issue")
else:
    print("   ✗ Logfire not working even locally")
    print("   Check token and package installation")