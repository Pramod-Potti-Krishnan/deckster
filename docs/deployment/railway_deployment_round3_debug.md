# Railway Deployment Round 3 - Systematic Debugging

## Current Status
- Fixed `magic` import by adding python-magic, python-magic-bin, and Pillow
- Deployment still crashes during import
- Error occurs at `src/api/__init__.py` line 6

## Debugging Strategy

### 1. Comprehensive Import Testing
Created `test_all_imports.py` to:
- Simulate Railway's exact import sequence
- Test every module in the dependency chain
- Identify ALL missing imports at once

**Usage:**
```bash
cd /path/to/project
python test_all_imports.py
```

### 2. Enhanced Error Logging
Created `main_debug.py` to:
- Wrap imports in try/except blocks
- Print detailed error messages
- Trace the exact failure point

**To use on Railway:**
```bash
# Temporarily replace main.py
mv main.py main_original.py
mv main_debug.py main.py
# Deploy and check logs
# Restore after debugging
mv main.py main_debug.py
mv main_original.py main.py
```

### 3. Minimal Deployment Test
Created `main_minimal.py` to:
- Test basic Railway deployment works
- Verify environment variables
- Test imports individually via endpoints

**To deploy minimal version:**
```dockerfile
# In Dockerfile, change:
CMD ["sh", "-c", "uvicorn main_minimal:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

## Debugging Process

### Step 1: Local Testing
```bash
# Run comprehensive import test
python test_all_imports.py

# If errors found, fix them and test again
pip install missing-package
python test_all_imports.py
```

### Step 2: Deploy Debug Version
If local tests pass but Railway fails:
1. Use `main_debug.py` to get detailed error logs
2. Check Railway logs for specific import that fails
3. Add missing package to requirements-prod.txt

### Step 3: Minimal Test
If still failing:
1. Deploy `main_minimal.py`
2. Visit `/test-imports` endpoint
3. See which imports fail in Railway environment

### Step 4: Gradual Addition
Once minimal works:
1. Add imports one by one to main_minimal.py
2. Deploy after each addition
3. Identify the exact import causing issues

## Common Issues and Solutions

### 1. Import Order Matters
Some imports might work locally but fail on Railway due to initialization order:
```python
# Bad - imports at module level might fail
from .storage import get_redis

# Good - import inside functions
def startup():
    from .storage import get_redis
    redis = get_redis()
```

### 2. Circular Imports
Check for circular import chains:
- `src/__init__.py` imports from `src.api.main`
- `src.api.main` imports from `src`
- This creates a loop

### 3. Missing System Dependencies
Even with python packages installed, might need system libs:
```dockerfile
RUN apt-get update && apt-get install -y \
    libmagic1 \     # for python-magic
    libpq-dev \     # for psycopg2
    libjpeg-dev \   # for Pillow
    libpng-dev      # for Pillow
```

### 4. Environment-Specific Imports
Some imports might only work with certain env vars:
```python
# This might fail if SUPABASE_URL not set
from .storage import get_supabase
```

## Next Actions

1. **Run `test_all_imports.py` locally** - Share the output
2. **If local passes**, deploy with `main_debug.py` for better error messages
3. **If specific import fails**, add to requirements-prod.txt
4. **If circular import**, refactor the import structure

## Lessons Learned

1. **Test the exact import chain** - Don't assume "it works locally"
2. **Railway's environment is minimal** - No pre-installed packages
3. **Import errors cascade** - One missing import can hide others
4. **Debugging needs visibility** - Add logging/endpoints to see what's happening

## Progress Tracking

- [x] Added python-magic dependencies
- [x] Created comprehensive debugging tools
- [ ] Identified actual failing import
- [ ] Fixed all import issues
- [ ] Successful Railway deployment

This systematic approach will find the issue instead of guessing.