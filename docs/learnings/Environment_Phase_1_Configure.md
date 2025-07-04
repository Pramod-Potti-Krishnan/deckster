# Environment Configuration for Phase 1

This guide provides step-by-step instructions for configuring all required environment variables and services for Phase 1 of the presentation generator.

## Required Services Overview

For Phase 1, you need the following services:
- **Supabase** - Database with pgvector for similarity search
- **Redis** - Caching and pub/sub messaging
- **Anthropic API** - Primary LLM provider
- **OpenAI API** (Optional) - Fallback LLM provider
- **LogFire** (Optional) - Structured logging and observability

## Step 1: Create Environment File

1. Navigate to the presentation-generator directory:
```bash
cd /path/to/presentation-generator
```

2. Create a `.env` file (not `.env.example`):
```bash
touch .env
```

3. Copy the following template into your `.env` file:
```env
# ===========================
# MANDATORY FOR PHASE 1
# ===========================

# App Settings
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# Security - MUST CHANGE IN PRODUCTION
JWT_SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Redis Configuration (REQUIRED)
REDIS_URL=redis://localhost:6379/0

# LLM Configuration (AT LEAST ONE REQUIRED)
ANTHROPIC_API_KEY=your-anthropic-key
OPENAI_API_KEY=your-openai-key  # Optional fallback

# ===========================
# OPTIONAL FOR PHASE 1
# ===========================

# Pydantic AI Settings
PYDANTIC_AI_LOG_LEVEL=INFO
PYDANTIC_AI_MAX_RETRIES=3

# LogFire Configuration
LOGFIRE_TOKEN=your-logfire-token

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_WEBSOCKET_MESSAGES_PER_MINUTE=120

# Testing
TESTING=false
```

## Step 2: Set Up Supabase (MANDATORY)

### 2.1 Create Supabase Account
1. Go to [https://supabase.com](https://supabase.com)
2. Sign up for a free account
3. Create a new project (remember your database password)

### 2.2 Enable pgvector Extension
1. In Supabase Dashboard, go to **SQL Editor**
2. Run the following command:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2.3 Get Supabase Credentials
1. In your project dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_KEY` (keep this secret!)

### 2.4 Update .env File
```env
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 2.5 Run Database Setup
```bash
cd presentation-generator
python scripts/setup_db.py
```

## Step 3: Set Up Redis (MANDATORY)

You have three options for Redis setup:

### Option A: Redis Cloud (RECOMMENDED for Production/Railway)

#### A.1 Create Redis Cloud Account
1. Go to [app.redislabs.com](https://app.redislabs.com)
2. Sign up or log in
3. Create a new database:
   - Choose **Free Plan** (30MB)
   - Select cloud provider (AWS/GCP/Azure)
   - Choose region closest to your deployment
   - Database name: `presentation-generator`

#### A.2 Get Connection Details
After creation, you'll see:
- **Endpoint**: `redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345`
- **Password**: `YourRedisPassword123`

#### A.3 Update .env File
```env
# Redis Cloud Configuration
REDIS_URL=redis://:YourRedisPassword123@redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345/0

# Or with TLS (recommended for production)
REDIS_URL=rediss://:YourRedisPassword123@redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345/0
```

### Option B: Railway Redis Plugin

If deploying to Railway, you can use their Redis plugin:
1. In Railway dashboard, click "New Service"
2. Choose "Database" → "Redis"
3. Railway automatically injects `REDIS_URL`

### Option C: Local Redis Installation (Development Only)

#### On Ubuntu/Debian/WSL:
```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

#### On macOS:
```bash
brew install redis
brew services start redis
```

#### Docker:
```bash
docker run -d --name redis-phase1 -p 6379:6379 redis:alpine
```

#### Update .env for local:
```env
REDIS_URL=redis://localhost:6379/0
```

### 3.1 Verify Redis Connection
```bash
# For Redis Cloud
redis-cli -h redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com -p 12345 -a YourRedisPassword123 ping

# For local Redis
redis-cli ping

# Should return: PONG
```

## Step 4: Set Up JWT Secret (MANDATORY)

### 4.1 Generate Secure Secret Key
```bash
# Option 1: Using OpenSSL
openssl rand -hex 32

# Option 2: Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Option 3: Using UUID
python -c "import uuid; print(str(uuid.uuid4()).replace('-', '') + str(uuid.uuid4()).replace('-', ''))"
```

### 4.2 Update .env File
```env
JWT_SECRET_KEY=64-character-hex-string-from-above
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

**⚠️ IMPORTANT**: Never commit the actual JWT secret to version control!

## Step 5: Set Up Anthropic API (MANDATORY)

### 5.1 Get API Key
1. Go to [https://console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new API key
5. Copy the key (starts with `sk-ant-api03-...`)

### 5.2 Update .env File
```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

## Step 6: Set Up OpenAI API (OPTIONAL - Fallback)

### 6.1 Get API Key
1. Go to [https://platform.openai.com](https://platform.openai.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new API key
5. Copy the key (starts with `sk-...`)

### 6.2 Update .env File
```env
OPENAI_API_KEY=sk-your-openai-key-here
```

## Step 7: Set Up LogFire (OPTIONAL)

### 7.1 Get LogFire Token
1. Go to [https://logfire.pydantic.dev](https://logfire.pydantic.dev)
2. Sign up for an account
3. Create a new project
4. Get your API token

### 7.2 Update .env File
```env
LOGFIRE_TOKEN=your-logfire-token-here
```

## Step 8: Verify Configuration

### 8.1 Create Verification Script
Create `verify_env.py` in the project root:
```python
#!/usr/bin/env python3
"""Verify environment configuration for Phase 1."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(name: str, required: bool = True) -> bool:
    """Check if environment variable is set."""
    value = os.getenv(name)
    if value:
        # Hide sensitive data
        display_value = value[:10] + "..." if len(value) > 10 else value
        print(f"✓ {name} is set: {display_value}")
        return True
    else:
        if required:
            print(f"✗ {name} is NOT set (REQUIRED)")
        else:
            print(f"- {name} is not set (optional)")
        return not required

print("Phase 1 Environment Configuration Check")
print("=" * 40)

# Check mandatory variables
mandatory_ok = all([
    check_env_var("JWT_SECRET_KEY"),
    check_env_var("SUPABASE_URL"),
    check_env_var("SUPABASE_ANON_KEY"),
    check_env_var("SUPABASE_SERVICE_KEY"),
    check_env_var("REDIS_URL"),
    check_env_var("ANTHROPIC_API_KEY"),
])

print("\nOptional configurations:")
check_env_var("OPENAI_API_KEY", required=False)
check_env_var("LOGFIRE_TOKEN", required=False)

if mandatory_ok:
    print("\n✅ All mandatory environment variables are configured!")
    sys.exit(0)
else:
    print("\n❌ Some mandatory environment variables are missing!")
    sys.exit(1)
```

### 8.2 Run Verification
```bash
python verify_env.py
```

## Step 9: Test Connections

### 9.1 Test Supabase Connection
```python
python -c "
from src.storage.supabase import SupabaseClient
import asyncio

async def test():
    client = SupabaseClient()
    result = await client.health_check()
    print('Supabase connection:', 'OK' if result else 'FAILED')

asyncio.run(test())
"
```

### 9.2 Test Redis Connection
```python
python -c "
from src.storage.redis_cache import RedisCache
import asyncio

async def test():
    client = RedisCache()
    result = await client.health_check()
    print('Redis connection:', 'OK' if result else 'FAILED')

asyncio.run(test())
"
```

### 9.3 Test LLM Connection
```python
python -c "
import anthropic
import os

client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
try:
    # Simple test
    response = client.messages.create(
        model='claude-3-haiku-20240307',
        max_tokens=10,
        messages=[{'role': 'user', 'content': 'Say OK'}]
    )
    print('Anthropic API:', 'OK')
except Exception as e:
    print('Anthropic API:', 'FAILED -', str(e))
"
```

## Environment Variables Summary

### Mandatory for Phase 1:
| Variable | Purpose | Example |
|----------|---------|---------|
| `JWT_SECRET_KEY` | Authentication token signing | 64-char hex string |
| `SUPABASE_URL` | Database endpoint | https://xxx.supabase.co |
| `SUPABASE_ANON_KEY` | Public API key | eyJ... |
| `SUPABASE_SERVICE_KEY` | Admin API key | eyJ... |
| `REDIS_URL` | Cache/messaging | redis://localhost:6379/0 |
| `ANTHROPIC_API_KEY` | Primary LLM | sk-ant-api03-... |

### Optional for Phase 1:
| Variable | Purpose | When to Use |
|----------|---------|-------------|
| `OPENAI_API_KEY` | Fallback LLM | If Anthropic fails |
| `LOGFIRE_TOKEN` | Observability | Production monitoring |
| `RATE_LIMIT_*` | API limits | Production deployment |

## Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Use strong JWT secret** - At least 256 bits of entropy
3. **Rotate keys regularly** - Especially in production
4. **Use environment-specific files** - `.env.development`, `.env.production`
5. **Restrict service keys** - Only use where necessary

## Troubleshooting

### Issue: "Connection refused" for Redis
```bash
# Check if Redis is running
sudo systemctl status redis-server
# or
ps aux | grep redis

# Start Redis
sudo systemctl start redis-server
```

### Issue: "Invalid API key" for Supabase
- Verify you copied the complete key
- Check you're using service_role key where needed
- Ensure project is active (not paused)

### Issue: "Anthropic API key invalid"
- Keys start with `sk-ant-api03-`
- Check for whitespace in the key
- Verify account has available credits

## Next Steps

Once all environment variables are configured:

1. Run the database setup:
   ```bash
   python scripts/setup_db.py
   ```

2. Start the application:
   ```bash
   uvicorn src.api.main:app --reload
   ```

3. Run tests to verify everything works:
   ```bash
   pytest tests/unit/
   ```

Your Phase 1 environment is now fully configured! 🎉