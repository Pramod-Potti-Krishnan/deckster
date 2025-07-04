#!/usr/bin/env python
"""
Diagnose the exact logger issue causing 'Logger' object is not callable.
"""

import os
import sys

# Remove LOGFIRE_TOKEN to simulate Railway environment
original_token = os.environ.pop('LOGFIRE_TOKEN', None)

print("=== Diagnosing Logger Issue ===")
print("Simulating Railway environment (no LOGFIRE_TOKEN)...\n")

try:
    # Step 1: Import and examine logger
    print("1. Importing logger module...")
    from src.utils.logger import logger, LOGFIRE_AVAILABLE, logfire
    
    print(f"   LOGFIRE_AVAILABLE: {LOGFIRE_AVAILABLE}")
    print(f"   type(logfire): {type(logfire)}")
    print(f"   type(logger): {type(logger)}")
    print(f"   logger is logfire: {logger is logfire}")
    print(f"   id(logger): {id(logger)}")
    print(f"   id(logfire): {id(logfire)}")
    
    # Step 2: Check logger attributes
    print("\n2. Logger attributes:")
    print(f"   hasattr(logger, 'info'): {hasattr(logger, 'info')}")
    print(f"   callable(logger): {callable(logger)}")
    if hasattr(logger, 'info'):
        print(f"   callable(logger.info): {callable(logger.info)}")
        print(f"   type(logger.info): {type(logger.info)}")
    
    # Step 3: Check what happens with __getattr__
    print("\n3. Testing attribute access:")
    try:
        info_method = logger.info
        print(f"   logger.info retrieved: {info_method}")
        print(f"   type(logger.info): {type(info_method)}")
    except Exception as e:
        print(f"   Error accessing logger.info: {e}")
    
    # Step 4: Try the actual failing call
    print("\n4. Testing the failing call:")
    try:
        # First check if we can access info
        if hasattr(logger, 'info'):
            print("   logger.info exists")
            # Try to call it
            logger.info("Test message", version="1.0.0")
            print("   ✓ logger.info() call succeeded!")
        else:
            print("   ✗ logger.info does not exist!")
            print(f"   Available attributes: {[attr for attr in dir(logger) if not attr.startswith('_')]}")
    except Exception as e:
        print(f"   ✗ Error calling logger.info: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Test if logger itself is being called
    print("\n5. Testing if logger is being called as function:")
    try:
        # This might be what's happening
        logger("test")
    except TypeError as e:
        print(f"   ✓ Confirmed: {e}")
        print("   This matches the Railway error!")
    
    # Step 6: Debug MockLogfire
    print("\n6. Debugging MockLogfire:")
    if not LOGFIRE_AVAILABLE:
        print(f"   MockLogfire class: {logfire.__class__}")
        print(f"   MockLogfire._logger: {logfire._logger if hasattr(logfire, '_logger') else 'N/A'}")
        
        # Test direct method access
        if hasattr(logfire, 'info'):
            print("   logfire.info exists and is callable")
        
        # Test __getattr__
        print("\n   Testing __getattr__ behavior:")
        test_attr = logfire.some_random_attribute
        print(f"   logfire.some_random_attribute: {test_attr}")
        print(f"   type: {type(test_attr)}")

finally:
    # Restore token
    if original_token:
        os.environ['LOGFIRE_TOKEN'] = original_token

print("\n=== Analysis Complete ===")
print("Check the output above to understand the exact issue.")