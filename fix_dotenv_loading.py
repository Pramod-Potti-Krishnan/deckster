"""
Fix for .env loading issue - analysis and solution.
"""

print("=== ROOT CAUSE ANALYSIS ===\n")

print("THE PROBLEM:")
print("1. LOGFIRE_TOKEN IS in .env file (line 27)")
print("2. But logger.py can't see it")
print("3. Because of TIMING issue:\n")

print("WHAT HAPPENS:")
print("1. logger.py imports and immediately calls os.getenv('LOGFIRE_TOKEN')")
print("2. At this point, .env is NOT loaded yet")
print("3. So LOGFIRE_TOKEN = None")
print("4. MockLogfire is used instead of real logfire")
print("5. Later, pydantic-settings loads .env, but it's too late\n")

print("THE FIX:")
print("Add load_dotenv() at the TOP of logger.py before os.getenv() calls\n")

fix_code = '''# At the top of src/utils/logger.py, after imports:
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# NOW these will work:
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")
LOGFIRE_PROJECT = os.getenv("LOGFIRE_PROJECT", "presentation-generator")
'''

print(fix_code)

print("\nWHY THIS WORKS:")
print("1. load_dotenv() explicitly loads .env file")
print("2. Environment variables are available immediately")
print("3. LOGFIRE_TOKEN will be found")
print("4. Real logfire will be used instead of MockLogfire")

print("\nALTERNATIVE FIXES:")
print("1. Add load_dotenv() in src/__init__.py (loads for entire package)")
print("2. Lazy load logfire configuration (delay until first use)")
print("3. Use settings object instead of os.getenv()")

print("\nBUT the simplest fix is adding load_dotenv() in logger.py!")