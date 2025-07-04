# Railway Debug Logging Implementation

## Date: July 4, 2025

## Purpose
Add debug logging to identify if Railway adds semicolons to all environment variables, not just CORS_ORIGINS.

## Changes Made

### 1. Enhanced Startup Logging in main.py
Added comprehensive debug logging to check raw environment variable values:

```python
# Debug logging to check if Railway adds semicolons to all environment variables
import os
logger.info("[DEBUG] Checking raw environment variables:")
logger.info(f"[DEBUG] CORS_ORIGINS raw: '{os.environ.get('CORS_ORIGINS', 'NOT SET')}'")
logger.info(f"[DEBUG] APP_ENV raw: '{os.environ.get('APP_ENV', 'NOT SET')}'")
logger.info(f"[DEBUG] LOG_LEVEL raw: '{os.environ.get('LOG_LEVEL', 'NOT SET')}'")
logger.info(f"[DEBUG] JWT_ALGORITHM raw: '{os.environ.get('JWT_ALGORITHM', 'NOT SET')}'")
logger.info(f"[DEBUG] ALLOWED_FILE_EXTENSIONS raw: '{os.environ.get('ALLOWED_FILE_EXTENSIONS', 'NOT SET')}'")
logger.info(f"[DEBUG] FALLBACK_LLM_MODELS raw: '{os.environ.get('FALLBACK_LLM_MODELS', 'NOT SET')}'")
```

### 2. CORS Origins Parser Debug Logging
Added debug print statements to track the parsing process:

```python
@field_validator("cors_origins", mode="before")
def parse_cors_origins(cls, v):
    """Parse CORS origins from string or list."""
    if isinstance(v, str):
        # Debug logging
        print(f"[DEBUG] parse_cors_origins received string value: '{v}'")
        print(f"[DEBUG] String length: {len(v)}")
        print(f"[DEBUG] Contains semicolons: {';' in v}")
        
        # ... parsing logic ...
        
        print(f"[DEBUG] After cleaning semicolons: '{cleaned}'")
        result = [origin.strip() for origin in cleaned.split(",") if origin.strip()]
        print(f"[DEBUG] Final parsed result: {result}")
        return result
    return v
```

### 3. Fixed OPTIONS Preflight Authentication
Modified AuthenticationMiddleware to skip authentication for OPTIONS requests:

```python
async def dispatch(self, request: Request, call_next: Callable) -> Response:
    """Process request with authentication."""
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # ... rest of the authentication logic ...
```

### 4. Middleware Setup Order Logging
Added logging to show the exact order of middleware setup:

```python
logger.info("[DEBUG] Middleware setup order (outer to inner):")
logger.info("[DEBUG] 1. Adding CORSMiddleware (handles OPTIONS preflight)")
# ... middleware setup ...
logger.info("[DEBUG] 6. Adding AuthenticationMiddleware (now skips OPTIONS)")
```

## Expected Debug Output

When deployed to Railway, you should see:

1. **Raw Environment Variables**: Shows if semicolons appear in any variables
2. **Parser Debug Output**: Shows exactly what the CORS parser receives and how it processes the value
3. **Middleware Order**: Confirms that CORS middleware is set up first (outermost)

## What to Look For

1. **Semicolon Pattern**: Check if semicolons appear in:
   - Only CORS_ORIGINS
   - All list-type variables (ALLOWED_FILE_EXTENSIONS, FALLBACK_LLM_MODELS)
   - Simple string variables (APP_ENV, LOG_LEVEL)

2. **Parser Behavior**: The debug output will show:
   - The exact string received
   - Whether semicolons are detected
   - The cleaned string after semicolon removal
   - The final parsed list

3. **OPTIONS Request Handling**: With the fix, OPTIONS requests should:
   - Skip authentication middleware
   - Be handled by CORS middleware
   - Return proper CORS headers without 401 errors

## Next Steps After Deployment

1. Review the debug logs to identify the semicolon pattern
2. If semicolons are Railway-specific to certain variables, document the pattern
3. If the issue persists, consider alternative environment variable formats
4. Once debugging is complete, remove the debug logging for production

## Files Modified
- `/src/api/main.py` - Added startup debug logging
- `/src/config/settings.py` - Added parser debug output
- `/src/api/middleware.py` - Fixed OPTIONS authentication, added setup logging