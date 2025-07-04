# Railway Deployment Round 8: CORS Configuration Fix

## Date: July 4, 2025

## Issue Encountered
Frontend at https://www.deckster.xyz was unable to connect to the backend API due to CORS policy blocking requests.

### Error Messages
```
Access to fetch at 'https://deckster-production.up.railway.app/api/dev/token' 
from origin 'https://www.deckster.xyz' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Root Causes Identified

### 1. Old Deployment Running
- Railway was running commit `1e9eb77` 
- CORS fixes were in commit `9eb8f48`
- Changes weren't deployed to Railway

### 2. CORS Configuration Issues
- Backend was only allowing localhost origins
- CORS headers weren't being added to error responses (401 Unauthorized)
- Preflight OPTIONS requests weren't handled properly

### 3. Environment Variable Not Updated
- CORS_ORIGINS in Railway needed to include production domains

## Solutions Implemented

### 1. Updated Environment Configuration
Updated `.env` and Railway environment variables:
```
CORS_ORIGINS=["https://www.deckster.xyz","https://deckster.xyz","https://*.vercel.app","http://localhost:3000","http://localhost:5173"]
```

### 2. Fixed Middleware Configuration
Updated `src/api/middleware.py`:
- Read CORS origins from settings instead of hardcoding
- Added logging for CORS configuration
- Added HEAD method support
- Added max_age for preflight caching

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Dynamic from environment
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=3600  # Cache preflight for 1 hour
)
```

### 3. Added Debug Logging
Updated `src/api/main.py` to log configuration at startup:
```python
logger.info(f"APP_ENV: {settings.app_env}")
logger.info(f"CORS origins configured: {settings.cors_origins}")
logger.info(f"Development mode: {settings.is_development}")
```

### 4. Created Test Endpoint
Added `/api/health/cors` endpoint for testing CORS without authentication:
```python
@app.get("/api/health/cors")
async def cors_test():
    return {
        "status": "ok",
        "cors_test": True,
        "environment": settings.app_env,
        "cors_origins": settings.cors_origins,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Testing Procedures

### 1. Test CORS Headers
```bash
curl -I https://deckster-production.up.railway.app/api/health/cors \
  -H "Origin: https://www.deckster.xyz"
```

Should return headers including:
```
Access-Control-Allow-Origin: https://www.deckster.xyz
Access-Control-Allow-Credentials: true
```

### 2. Test from Frontend
```javascript
// Test CORS endpoint
fetch('https://deckster-production.up.railway.app/api/health/cors')
  .then(r => r.json())
  .then(console.log)

// Test dev token endpoint
fetch('https://deckster-production.up.railway.app/api/dev/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 'test_user' })
})
```

## Lessons Learned

### 1. Always Verify Deployment
- Check Railway deployment logs for the commit hash
- Ensure the latest code is actually deployed

### 2. CORS Middleware Order Matters
- CORS middleware should be one of the first middlewares
- Must be added before authentication middleware

### 3. Environment Variable Format
- Railway requires exact JSON format for arrays
- Use double quotes, no spaces after commas
- Example: `["origin1","origin2"]`

### 4. Debug Endpoints Are Valuable
- Create endpoints that don't require auth for testing
- Log configuration at startup for visibility

### 5. CORS Headers on Errors
- Default CORS middleware may not add headers to error responses
- Need to ensure all responses include CORS headers

## Configuration Checklist

- [ ] Update CORS_ORIGINS in `.env` for local development
- [ ] Update CORS_ORIGINS in Railway environment variables
- [ ] Set APP_ENV appropriately (development/production)
- [ ] Push code changes to trigger Railway deployment
- [ ] Verify correct commit is deployed in Railway
- [ ] Test CORS with curl from command line
- [ ] Test from actual frontend application

## Related Files Modified
- `/src/api/middleware.py` - Dynamic CORS configuration
- `/src/api/main.py` - Debug logging and test endpoint
- `/.env` - Local CORS origins
- `/docs/deployment/railway-cors-setup.md` - Setup guide

## Next Steps
1. Monitor Railway logs for CORS configuration on startup
2. Implement proper authentication flow with Google OAuth
3. Consider implementing a more robust CORS handling for error responses