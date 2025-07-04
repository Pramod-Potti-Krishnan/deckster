#!/usr/bin/env python
"""
Test if logfire now works with the dotenv fix.
"""

print("=== Testing Logfire with dotenv Fix ===\n")

# Import logger AFTER the fix
print("1. Importing logger module...")
from src.utils.logger import logger, LOGFIRE_AVAILABLE, LOGFIRE_TOKEN, LOGFIRE_PROJECT

print(f"   LOGFIRE_AVAILABLE: {LOGFIRE_AVAILABLE}")
print(f"   LOGFIRE_TOKEN: {'*' * 10 if LOGFIRE_TOKEN else 'NOT SET'}")
print(f"   LOGFIRE_PROJECT: {LOGFIRE_PROJECT}")
print(f"   Logger type: {type(logger)}")

if LOGFIRE_TOKEN and not LOGFIRE_AVAILABLE:
    print("\n   ⚠️ Token exists but logfire still not available!")
    print("   Possible issues:")
    print("   - logfire package not installed")
    print("   - Import error in logfire package")
elif LOGFIRE_TOKEN and LOGFIRE_AVAILABLE:
    print("\n   ✅ SUCCESS! Logfire is now working!")
    print("   The dotenv fix resolved the issue")
elif not LOGFIRE_TOKEN:
    print("\n   ❌ Still no token - check if .env file exists")

# Test logging
print("\n2. Testing logger calls:")
try:
    logger.info("Testing with dotenv fix", status="testing", user="developer")
    print("   ✅ Logger call succeeded")
except Exception as e:
    print(f"   ❌ Logger call failed: {e}")

print("\n3. Summary:")
if LOGFIRE_AVAILABLE:
    print("   ✅ Logfire is now properly initialized!")
    print("   ✅ The app will use real logfire logging")
    print("   ✅ Railway deployment should work with proper logging")
else:
    print("   ⚠️  Using MockLogfire fallback")
    print("   But the app will still work correctly")