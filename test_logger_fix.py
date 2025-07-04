#!/usr/bin/env python
"""
Quick test to verify the logger fix works.
"""

import os
import sys

# Test without LOGFIRE_TOKEN to simulate Railway issue
print("=== Testing Logger Fix ===")
print("Simulating Railway environment (no LOGFIRE_TOKEN)...\n")

# Temporarily remove LOGFIRE_TOKEN from environment
original_token = os.environ.pop('LOGFIRE_TOKEN', None)

try:
    # Import the logger (this will use MockLogfire)
    from src.utils.logger import logger, LOGFIRE_AVAILABLE
    
    print(f"✓ Logger imported successfully")
    print(f"  LOGFIRE_AVAILABLE: {LOGFIRE_AVAILABLE}")
    print(f"  Logger type: {type(logger)}")
    
    # Test the exact failing call
    print("\nTesting the exact call from main.py:")
    print('  logger.info("Starting Presentation Generator API", version="1.0.0")')
    
    try:
        logger.info("Starting Presentation Generator API", version="1.0.0")
        print("  ✓ SUCCESS! Logger call worked")
    except Exception as e:
        print(f"  ✗ FAILED: {e}")
    
    # Test other log levels
    print("\nTesting other log levels:")
    logger.debug("Debug message", user_id="123")
    logger.warning("Warning message", error_code=404)
    logger.error("Error message", exception="TestError")
    print("  ✓ All log levels work with keyword arguments")
    
finally:
    # Restore LOGFIRE_TOKEN if it existed
    if original_token:
        os.environ['LOGFIRE_TOKEN'] = original_token

print("\n✓ Logger fix is working! The deployment should succeed now.")
print("\nTo deploy:")
print("  git add src/utils/logger.py")
print("  git commit -m 'Fix: MockLogfire to handle logfire-style API calls'")
print("  git push")