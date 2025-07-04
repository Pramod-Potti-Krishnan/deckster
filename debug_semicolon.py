#!/usr/bin/env python3
"""Debug script to find where semicolons are being added to CORS origins."""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== SEMICOLON DEBUG SCRIPT ===\n")

# 1. Check the raw file bytes
print("1. Checking settings.py file bytes:")
with open('src/config/settings.py', 'rb') as f:
    content = f.read()
    
    # Find the default CORS origins line
    search_patterns = [
        b'default=["http://localhost:3000", "http://localhost:5173"]',
        b"default=['http://localhost:3000', 'http://localhost:5173']",
        b'localhost:3000',
        b'localhost:5173'
    ]
    
    for pattern in search_patterns:
        idx = content.find(pattern)
        if idx != -1:
            # Show context around the match
            start = max(0, idx - 30)
            end = min(len(content), idx + len(pattern) + 30)
            chunk = content[start:end]
            
            print(f"\nFound pattern: {pattern}")
            print(f"Position: {idx}")
            print(f"Context bytes: {chunk}")
            print(f"Context string: {chunk.decode('utf-8', errors='replace')}")
            
            # Check for any unusual characters
            for i, byte in enumerate(chunk):
                if byte > 127:  # Non-ASCII
                    print(f"  Non-ASCII byte at offset {i}: 0x{byte:02x}")

# 2. Import and check the actual settings
print("\n\n2. Importing settings module:")
try:
    from src.config.settings import Settings, get_settings
    
    # Create a fresh settings instance with no environment variables
    print("\nCreating settings with NO environment variables:")
    # Clear CORS_ORIGINS if it exists
    old_cors = os.environ.pop('CORS_ORIGINS', None)
    
    settings = Settings()
    print(f"Default cors_origins: {settings.cors_origins}")
    print(f"Type: {type(settings.cors_origins)}")
    
    if isinstance(settings.cors_origins, list):
        for i, origin in enumerate(settings.cors_origins):
            print(f"  [{i}] = '{origin}' (length: {len(origin)})")
            # Check each character
            for j, char in enumerate(origin):
                if ord(char) > 127 or char == ';':
                    print(f"    Character {j}: '{char}' (Unicode: U+{ord(char):04X})")
    
    # Restore the environment variable if it existed
    if old_cors:
        os.environ['CORS_ORIGINS'] = old_cors
        
except Exception as e:
    print(f"Error importing settings: {e}")
    import traceback
    traceback.print_exc()

# 3. Check dotenv loading
print("\n\n3. Checking .env file:")
try:
    from dotenv import dotenv_values
    
    env_values = dotenv_values('.env')
    if 'CORS_ORIGINS' in env_values:
        cors_value = env_values['CORS_ORIGINS']
        print(f"CORS_ORIGINS in .env: '{cors_value}'")
        print(f"Length: {len(cors_value)}")
        
        # Check for special characters
        for i, char in enumerate(cors_value):
            if ord(char) > 127 or char in ';:':
                print(f"  Character {i}: '{char}' (Unicode: U+{ord(char):04X})")
    else:
        print("CORS_ORIGINS not found in .env file")
        
except Exception as e:
    print(f"Error reading .env: {e}")

# 4. Test the validator directly
print("\n\n4. Testing parse_cors_origins validator:")
try:
    from src.config.settings import Settings
    
    # Get the validator method
    validator = Settings.parse_cors_origins
    
    # Test with different inputs
    test_cases = [
        "https://www.deckster.xyz",
        "https://www.deckster.xyz,https://deckster.xyz",
        '["https://www.deckster.xyz","https://deckster.xyz"]',
        None  # This will trigger default value processing
    ]
    
    for test_input in test_cases:
        print(f"\nTesting with: {repr(test_input)}")
        try:
            result = validator(test_input)
            print(f"  Result: {result}")
            if isinstance(result, list):
                for item in result:
                    print(f"    - '{item}' (has semicolon: {';' in item})")
        except Exception as e:
            print(f"  Error: {e}")
            
except Exception as e:
    print(f"Error testing validator: {e}")

# 5. Check Python string representation
print("\n\n5. Testing Python string representation:")
test_list = ["http://localhost:3000", "http://localhost:5173"]
print(f"Normal list: {test_list}")
print(f"String repr: {repr(test_list)}")
print(f"Using f-string: {f'{test_list}'}")

# Check if logging is adding semicolons
print("\n\n6. Testing logging output:")
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")
logger.info(f"Test CORS: {test_list}")

print("\n=== END OF DEBUG ===")