#!/usr/bin/env python
"""
Test if .env file is being loaded.
"""

import os

print("=== Testing .env Loading ===\n")

print("1. Before loading .env:")
print(f"   LOGFIRE_TOKEN from env: {os.getenv('LOGFIRE_TOKEN', 'NOT FOUND')}")
print(f"   JWT_SECRET_KEY from env: {os.getenv('JWT_SECRET_KEY', 'NOT FOUND')}")
print(f"   REDIS_URL from env: {os.getenv('REDIS_URL', 'NOT FOUND')}")

print("\n2. Loading .env file manually:")
from dotenv import load_dotenv
load_dotenv()

print("\n3. After loading .env:")
logfire_token = os.getenv('LOGFIRE_TOKEN', 'NOT FOUND')
jwt_key = os.getenv('JWT_SECRET_KEY', 'NOT FOUND')
redis_url = os.getenv('REDIS_URL', 'NOT FOUND')

print(f"   LOGFIRE_TOKEN: {logfire_token}")
print(f"   JWT_SECRET_KEY: {'*' * 10 if jwt_key != 'NOT FOUND' else 'NOT FOUND'}")
print(f"   REDIS_URL: {'*' * 10 if redis_url != 'NOT FOUND' else 'NOT FOUND'}")

print("\n4. Checking if LOGFIRE entries exist in .env:")
try:
    with open('.env', 'r') as f:
        env_content = f.read()
        has_logfire = 'LOGFIRE' in env_content
        print(f"   LOGFIRE mentioned in .env: {has_logfire}")
        
        # Count all env vars
        lines = [line.strip() for line in env_content.split('\n') if line.strip() and not line.startswith('#') and '=' in line]
        print(f"   Total env vars in .env: {len(lines)}")
        
        # Show all var names (not values)
        print("\n   Environment variables defined in .env:")
        for line in lines:
            var_name = line.split('=')[0]
            print(f"     - {var_name}")
except Exception as e:
    print(f"   Error reading .env: {e}")

print("\n5. ROOT CAUSE:")
if logfire_token == 'NOT FOUND':
    if has_logfire:
        print("   ✗ LOGFIRE_TOKEN is in .env but not loaded into environment")
        print("   ✗ The app is NOT calling load_dotenv()")
    else:
        print("   ✗ LOGFIRE_TOKEN is NOT in .env file")
        print("   ✗ You need to add it to .env")
else:
    print("   ✓ LOGFIRE_TOKEN successfully loaded from .env")