# Railway Deployment Guide

This guide ensures successful deployment of the Deckster API to Railway.

## Files Created for Railway

1. **Procfile** - Primary start command specification
   ```
   web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```

2. **railway.json** - Railway-specific configuration
3. **runtime.txt** - Python version specification (3.11.9)
4. **start.sh** - Backup start script
5. **nixpacks.toml** - Nixpacks build configuration
6. **.railway/railway.toml** - Additional Railway configuration

## Environment Variables Required in Railway

### Mandatory Variables
```env
# App Settings
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Security
JWT_SECRET_KEY=your-production-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis
REDIS_URL=redis://default:password@redis-cloud.com:port

# AI Services
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...  # Optional fallback
```

### Railway Auto-Set Variables
- `PORT` - Automatically set by Railway
- `RAILWAY_ENVIRONMENT` - Set to "production"

## Deployment Steps

1. **Push Changes to Git**
   ```bash
   git add Procfile railway.json runtime.txt start.sh nixpacks.toml .railway/
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **In Railway Dashboard**
   - Go to your project
   - Click "Variables"
   - Add all required environment variables
   - Deploy should trigger automatically

3. **Monitor Deployment**
   - Check build logs for any errors
   - Once deployed, visit the provided URL
   - Test health endpoint: `https://your-app.railway.app/health`

## Troubleshooting

### If deployment still fails:

1. **Check Python Version**
   - Railway might not support Python 3.13 yet
   - runtime.txt specifies 3.11.9 which is stable

2. **Check Logs**
   ```
   railway logs
   ```

3. **Verify Start Command**
   - The Procfile should be sufficient
   - Railway will use it automatically

4. **Environment Variables**
   - Ensure all required variables are set
   - Check for typos in variable names

5. **Dependencies**
   - Ensure requirements.txt is in root directory
   - All packages should be pip-installable

## Testing Deployment

Once deployed, test these endpoints:

1. Health Check:
   ```
   GET https://your-app.railway.app/health
   ```

2. Detailed Health:
   ```
   GET https://your-app.railway.app/health/detailed
   ```

3. API Documentation:
   ```
   https://your-app.railway.app/docs
   ```

## Notes

- The app uses Python 3.11 for Railway compatibility (not 3.13)
- Port is dynamically assigned by Railway
- Health checks ensure automatic restarts if needed
- Logs are available in Railway dashboard