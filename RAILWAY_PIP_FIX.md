# Railway Deployment - Pip Not Found Fix

## Root Cause
Railway's Nixpacks is injecting a `pip install --upgrade pip` command before our custom configuration, but `pip` is not in the PATH.

## Solutions Implemented

### Solution 1: Enhanced Nixpacks Configuration
Updated `nixpacks.toml` to:
1. Install `python3-pip` via apt packages
2. Use `python -m ensurepip` to ensure pip is available
3. Use `python -m pip` for all pip commands
4. Added explicit phase dependencies

### Solution 2: Custom Dockerfile (Fallback)
Created a `Dockerfile` that:
1. Uses official Python 3.11 image
2. Handles pip installation properly
3. Uses `python -m pip` commands
4. Properly handles PORT environment variable

### Solution 3: Railway Configuration Options
- `railway.json` - Uses Nixpacks (default)
- `railway-docker.json` - Uses Dockerfile

## Deployment Steps

### Option A: Try Nixpacks First (Recommended)
```bash
# Commit the updated nixpacks configuration
git add nixpacks.toml railway.json
git commit -m "Fix Railway pip not found - enhanced nixpacks config"
git push
```

### Option B: Use Dockerfile If Nixpacks Fails
```bash
# Rename to use Docker configuration
mv railway.json railway-nixpacks.json
mv railway-docker.json railway.json

# Commit and push
git add railway.json railway-nixpacks.json Dockerfile
git commit -m "Switch to Dockerfile for Railway deployment"
git push
```

### Option C: Manual Railway Settings
In Railway dashboard:
1. Go to your service settings
2. Under "Build" section, you can:
   - Set custom build command: `python -m pip install -r requirements-prod.txt`
   - Or switch to Dockerfile mode

## What Each File Does

1. **nixpacks.toml** - Configures the Nixpacks build system
   - Installs Python 3.11 and gcc
   - Ensures pip is available via apt and ensurepip
   - Uses `python -m pip` for installations

2. **Dockerfile** - Custom Docker build
   - Complete control over the build process
   - Guaranteed to have pip available
   - More predictable but slightly larger image

3. **railway.json** - Railway configuration
   - Specifies which builder to use
   - Sets deployment parameters

## Expected Outcome
The deployment should now succeed because:
1. Pip will be properly installed and available
2. All pip commands use `python -m pip` syntax
3. Fallback to Dockerfile if Nixpacks continues to fail