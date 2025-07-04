# Railway Deployment Round 7 - Environment Variable Loading Issue

## The Mystery
- MockLogfire was always being used despite LOGFIRE_TOKEN being in .env
- Test showed "Warning: logfire not available, using standard logging"
- But .env file clearly had: `LOGFIRE_TOKEN=pylf_v1_us_tTYDP3LDgtz160RMjvlYD0cNs1NzJxXHfzF77g3cDLTq`

## Root Cause: Timing Issue

### The Import Order Problem
```python
# In logger.py (BEFORE fix):
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")  # Returns None!
```

### Why It Failed:
1. **Module Import Time**: When `logger.py` imports, it immediately runs `os.getenv()`
2. **No .env Loaded Yet**: At this point, .env file hasn't been loaded
3. **Token is None**: So `LOGFIRE_TOKEN = None`
4. **Fallback Activated**: Code uses MockLogfire instead of real logfire
5. **Too Late**: Later, pydantic-settings loads .env, but logger already initialized

### The Timing Sequence:
```
1. Python imports src.utils.logger
2. logger.py runs os.getenv("LOGFIRE_TOKEN") → None
3. logger.py decides to use MockLogfire
4. ... later ...
5. Settings class instantiates
6. pydantic-settings loads .env file
7. But logger.py already made its decision!
```

## The Fix
Added explicit `load_dotenv()` at the top of logger.py:

```python
# Load environment variables from .env file BEFORE using them
from dotenv import load_dotenv
load_dotenv()

# NOW this works:
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")  # Gets the actual token!
```

## Key Learnings

### 1. Environment Variables Have Load Timing
- `os.getenv()` only sees what's already in the environment
- .env files must be explicitly loaded BEFORE checking variables
- Module-level code runs at import time, not runtime

### 2. Pydantic Settings vs Direct os.getenv()
- **Pydantic Settings**: Loads .env when Settings class is instantiated
- **Direct os.getenv()**: Only sees current environment
- They work at different times!

### 3. Common Patterns for .env Loading
```python
# Option 1: In the module that needs it
from dotenv import load_dotenv
load_dotenv()

# Option 2: In __init__.py at package root
# src/__init__.py
from dotenv import load_dotenv
load_dotenv()

# Option 3: In main.py before any imports
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from src.api.main import app
```

### 4. Debugging Environment Variables
Always check THREE things:
1. Is the variable in .env? ✓
2. Is .env being loaded? ✗ (This was our issue)
3. Is it loaded BEFORE you check it? ✗

### 5. Railway vs Local Differences
- Local: You might have vars in your shell environment
- Railway: Only has what you explicitly set or load
- This can mask issues locally that appear in deployment

## Why Previous Fixes Didn't Work

1. **Round 6**: We added LOGFIRE_TOKEN to Railway env vars
   - But the logger timing issue remained
   - MockLogfire was still used due to import timing

2. **MockLogfire Fix**: We fixed the API compatibility
   - This made the app work WITHOUT logfire
   - But didn't solve why logfire wasn't loading

## Testing Methodology

Created multiple test scripts:
1. `test_env_loading.py` - Showed .env wasn't loaded at module level
2. `test_logfire_token.py` - Verified token exists in .env
3. `fix_dotenv_loading.py` - Explained the timing issue
4. `test_logfire_fixed.py` - Confirmed the fix works

## The Complete Fix

1. ✅ LOGFIRE_TOKEN in .env file
2. ✅ load_dotenv() called BEFORE os.getenv()
3. ✅ MockLogfire handles API compatibility (as backup)
4. ✅ Real logfire loads when available

## Deployment Should Now Work Because:

1. **Environment variables load immediately** via load_dotenv()
2. **Logfire initializes properly** with token
3. **Fallback still works** if logfire unavailable
4. **No more timing issues** with variable loading

## Best Practices Learned

1. **Always load .env explicitly** when using os.getenv() at module level
2. **Check timing** of when variables are accessed vs loaded
3. **Use settings objects** for lazy loading when possible
4. **Test both with and without** environment variables
5. **Add logging** to show which path code is taking

This was a classic "works on my machine" issue where the problem was WHEN things happen, not WHAT happens!