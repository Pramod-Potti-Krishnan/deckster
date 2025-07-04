#!/usr/bin/env python3
"""Test script to see how Railway handles different logging formats."""

import logging
import sys
import os

# Test different logging scenarios
print("=== RAILWAY LOGGING TEST ===")

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("test-logger")

# Test 1: Direct list logging
test_list = ['http://localhost:3000', 'http://localhost:5173']
logger.info(f"Test 1 - Direct list: {test_list}")

# Test 2: List with special characters
special_list = ['value1;', 'value2;', 'value3;']
logger.info(f"Test 2 - List with semicolons: {special_list}")

# Test 3: String that looks like a list
fake_list = "['http://localhost:3000', 'http://localhost:5173']"
logger.info(f"Test 3 - String that looks like list: {fake_list}")

# Test 4: Custom formatted list
formatted = "[" + ", ".join(f"'{item}'" for item in test_list) + "]"
logger.info(f"Test 4 - Custom formatted: {formatted}")

# Test 5: JSON format
import json
json_list = json.dumps(test_list)
logger.info(f"Test 5 - JSON format: {json_list}")

# Test 6: Individual items
logger.info("Test 6 - Individual items:")
for i, item in enumerate(test_list):
    logger.info(f"  Item {i}: {item}")

# Test 7: Using print instead of logger
print(f"Test 7 - Using print: {test_list}")

# Test 8: Check if it's related to MockLogfire
try:
    # Simulate the MockLogfire behavior
    class MockLogger:
        def info(self, message, **kwargs):
            print(f"MockLogger: {message}")
    
    mock = MockLogger()
    mock.info(f"Test 8 - Mock logger: {test_list}")
except Exception as e:
    print(f"Test 8 failed: {e}")

# Test 9: Raw string representation
logger.info(f"Test 9 - repr(): {repr(test_list)}")
logger.info(f"Test 10 - str(): {str(test_list)}")

print("\n=== END TEST ===")