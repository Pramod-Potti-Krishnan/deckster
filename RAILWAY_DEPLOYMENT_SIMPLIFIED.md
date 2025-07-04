# Railway Deployment - Simplified Approach

Based on analysis of the working vibe-decker-api-ver-3, here's the simplified deployment approach:

## Key Success Factors from Working Version

1. **Use Dockerfile only** - No railway.json, nixpacks.toml, or Procfile needed
2. **Minimal dependencies** - Working version has only ~25 packages
3. **Standard pip install** - No need for `python -m pip` workarounds
4. **Health check included** - Railway uses this for monitoring
5. **Let Railway auto-detect** - Railway automatically uses Dockerfile when present

## Deployment Steps

### 1. Clean Up Configuration Files
```bash
# Remove complex configuration files
rm railway.json railway-docker.json railway-nixpacks.json nixpacks.toml railway.yml Procfile

# Keep only the Dockerfile
```

### 2. Ensure Dockerfile is Optimized
The updated Dockerfile now matches the working version pattern:
- Uses `python:3.11-slim`
- Installs minimal system dependencies
- Uses standard `pip install` (not `python -m pip`)
- Includes health check
- Handles PORT environment variable

### 3. Deploy to Railway
```bash
# Commit simplified setup
git add -A
git commit -m "Simplify Railway deployment - use Dockerfile only"
git push
```

### 4. Railway Will Automatically:
- Detect the Dockerfile
- Build the image
- Deploy using the CMD instruction
- Monitor health via the HEALTHCHECK

## Environment Variables to Set in Railway Dashboard

```
JWT_SECRET_KEY=your-secret-key
JWT_EXPIRY_HOURS=24
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
REDIS_URL=redis://default:password@host:port
ANTHROPIC_API_KEY=your-api-key
OPENAI_API_KEY=your-api-key
```

## Why This Works Better

1. **No Nixpacks complexity** - Direct control via Dockerfile
2. **No pip PATH issues** - Standard Python image has pip in PATH
3. **Proven pattern** - Exact approach used in working ver-3
4. **Faster builds** - Better Docker layer caching
5. **Predictable behavior** - No automatic pip upgrades

## If Deployment Still Fails

Check these common issues:
1. **Port binding** - Ensure app uses PORT env var
2. **Health endpoint** - Verify /health returns 200 OK
3. **Memory usage** - Railway free tier has limits
4. **Build timeout** - Reduce dependencies if needed

## Monitoring

Once deployed, Railway will:
- Show build logs in real-time
- Monitor the health endpoint
- Restart on failures (configured in Dockerfile)
- Provide deployment URL