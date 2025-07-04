#!/usr/bin/env python
"""
Simple test to reproduce the exact Railway error.
"""

import os

# Remove LOGFIRE_TOKEN to simulate Railway
os.environ.pop('LOGFIRE_TOKEN', None)

print("Testing logger without LOGFIRE_TOKEN (Railway scenario)...\n")

# This is exactly what happens in main.py
from src.utils.logger import logger
from src.config.settings import get_settings

settings = get_settings()

print(f"1. logger type: {type(logger)}")
print(f"2. logger class: {logger.__class__.__name__}")
print(f"3. Is logger callable? {callable(logger)}")

# This is line 34 from main.py that's failing
print("\n4. Attempting the exact failing call:")
print('   logger.info("Starting Presentation Generator API", version=settings.app_version)')

try:
    logger.info("Starting Presentation Generator API", version=settings.app_version)
    print("   ✓ SUCCESS! The call worked.")
except TypeError as e:
    print(f"   ✗ FAILED with: {e}")
    print(f"   This is the exact Railway error!")
    
    # Let's see what's happening
    print("\n5. Debugging:")
    print(f"   - logger object: {logger}")
    print(f"   - dir(logger): {[x for x in dir(logger) if not x.startswith('_')]}")
    
    # Check if info exists
    if hasattr(logger, 'info'):
        info_attr = getattr(logger, 'info')
        print(f"   - logger.info exists: {info_attr}")
        print(f"   - type(logger.info): {type(info_attr)}")
        print(f"   - callable(logger.info): {callable(info_attr)}")
    else:
        print("   - logger.info DOES NOT EXIST")