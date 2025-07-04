# Round 11 Urgent Fixes - Deployment Issues

## Issues Found in Railway Logs

### 1. **CORS Origins Environment Variable Missing** ✅ RESOLVED
```
INFO:presentation-generator:[DEBUG] CORS_ORIGINS raw: 'NOT SET'
```
**Issue**: This was actually expected behavior - CORS_ORIGINS was intentionally removed as an environment variable in Round 9 to reduce complexity.

**Fix**: Updated default CORS origins in settings.py to be clean (no semicolons). No environment variable needed.

### 2. **Supabase RLS Policy Blocking Sessions** (Critical)
```
ERROR: new row violates row-level security policy for table "sessions"
```
**Issue**: Supabase Row Level Security is blocking session creation.

**Immediate Fix Options**:

#### Option A: Disable RLS for Sessions Table (Quick Fix)
```sql
-- In Supabase SQL Editor
ALTER TABLE sessions DISABLE ROW LEVEL SECURITY;
```

#### Option B: Create Proper RLS Policy 
```sql
-- In Supabase SQL Editor
CREATE POLICY "Allow service to manage sessions" 
ON sessions FOR ALL 
TO service_role 
USING (true);
```

#### Option C: Use Service Key for Session Operations
Update Supabase client to use service key for admin operations.

### 3. **Default CORS Values Still Have Semicolons**
The default CORS values in settings.py need to be updated to not have semicolons.

## Immediate Action Plan

### Backend Team (High Priority)

1. **Fix Default CORS Origins**
2. **Add Supabase Session Bypass** 
3. **Deploy Emergency Fix**

### DevOps/Database Team (Critical)

1. **Fix Supabase RLS** (Choose one):
   - Quick: Disable RLS on sessions table
   - Proper: Add service role policy
   - Alternative: Use service key for sessions

## Quick Fixes to Deploy Now

These changes will allow WebSocket connections to work immediately.