# Redis Cloud Setup Guide

This guide explains how to use Redis Cloud (Redis Labs) for both local development and Railway deployment instead of local Redis.

## Option 1: Redis Cloud (Recommended for Production)

### Step 1: Create Redis Cloud Database

1. **Log in to Redis Cloud**
   - Go to [app.redislabs.com](https://app.redislabs.com)
   - Sign in to your account

2. **Create New Database**
   - Click "New Database" or "Create Database"
   - Choose **Free Plan** (30MB) for development/testing
   - Select your preferred cloud provider (AWS/GCP/Azure)
   - Choose region closest to your users

3. **Configure Database Settings**
   - Database name: `presentation-generator-dev` (or your preference)
   - Modules: None needed for Phase 1
   - Data persistence: Yes (recommended)
   - Replication: Not needed for free tier

4. **Get Connection Details**
   After creation, you'll see:
   - **Endpoint**: `redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345`
   - **Password**: `YourRedisPassword123`
   - **Port**: Usually included in endpoint

### Step 2: Update Environment Configuration

#### For Local Development (.env)
```env
# Redis Cloud Configuration
REDIS_URL=redis://:YourRedisPassword123@redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345/0

# Or if using TLS (recommended)
REDIS_URL=rediss://:YourRedisPassword123@redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345/0
```

#### For Railway Deployment
In Railway dashboard:
1. Go to your service
2. Click "Variables"
3. Add:
```
REDIS_URL=redis://:YourRedisPassword123@redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com:12345/0
```

### Step 3: Test Redis Cloud Connection

```bash
# Install redis-cli if needed
sudo apt install redis-tools  # Ubuntu/WSL
# or
brew install redis  # macOS

# Test connection
redis-cli -h redis-xxxxx.c1.us-east-1-2.ec2.cloud.redislabs.com -p 12345 -a YourRedisPassword123 ping
# Should return: PONG
```

### Step 4: Update Code for Redis Cloud

The existing code should work, but ensure TLS support:

```python
# In src/storage/redis_cache.py, the connection already supports URLs:
self.redis = await aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)
```

## Option 2: Railway Redis Plugin (Alternative)

Railway also offers a Redis plugin:

1. **In Railway Dashboard**
   - Click "New Service"
   - Choose "Database" → "Redis"
   - Railway will provision Redis automatically

2. **Connect to Your Service**
   - Railway automatically injects `REDIS_URL`
   - No manual configuration needed

## Connection String Formats

### Redis Cloud (Standard)
```
redis://:[PASSWORD]@[HOST]:[PORT]/[DATABASE_NUMBER]
redis://:abc123@redis-12345.c1.us-east-1-2.ec2.cloud.redislabs.com:16379/0
```

### Redis Cloud (with TLS/SSL)
```
rediss://:[PASSWORD]@[HOST]:[PORT]/[DATABASE_NUMBER]
rediss://:abc123@redis-12345.c1.us-east-1-2.ec2.cloud.redislabs.com:16379/0
```

### Local Redis (for comparison)
```
redis://localhost:6379/0
redis://:password@localhost:6379/0  # with password
```

## Environment Variables for Different Stages

### Development (.env.development)
```env
# Use Redis Cloud free tier
REDIS_URL=redis://:dev_password@redis-dev.cloud.redislabs.com:12345/0
```

### Staging (.env.staging)
```env
# Use Redis Cloud paid tier with more memory
REDIS_URL=rediss://:staging_password@redis-staging.cloud.redislabs.com:12345/0
```

### Production (.env.production)
```env
# Use Redis Cloud with HA and clustering
REDIS_URL=rediss://:prod_password@redis-prod-cluster.cloud.redislabs.com:12345/0
```

## Redis Cloud Advantages

1. **No Local Setup** - Works immediately
2. **Persistent Storage** - Data survives restarts
3. **Monitoring** - Built-in dashboards
4. **Scaling** - Easy to upgrade
5. **High Availability** - Automatic failover (paid tiers)
6. **Backups** - Automated backups (paid tiers)

## Testing Redis Cloud Connection

### Python Test Script
```python
import asyncio
import aioredis
import os
from dotenv import load_dotenv

load_dotenv()

async def test_redis_cloud():
    redis_url = os.getenv('REDIS_URL')
    print(f"Connecting to: {redis_url.split('@')[1]}")  # Hide password
    
    try:
        redis = await aioredis.from_url(redis_url)
        
        # Test basic operations
        await redis.set('test_key', 'Hello from Redis Cloud!')
        value = await redis.get('test_key')
        print(f"Retrieved: {value}")
        
        # Test expiration
        await redis.setex('temp_key', 5, 'This expires in 5 seconds')
        
        # Test pub/sub
        pubsub = redis.pubsub()
        await pubsub.subscribe('test_channel')
        
        print("✅ Redis Cloud connection successful!")
        
        await redis.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test_redis_cloud())
```

## Monitoring and Management

### Redis Cloud Dashboard
1. **Memory Usage** - Monitor your 30MB limit
2. **Connections** - Active connection count
3. **Commands/sec** - Performance metrics
4. **Slow Log** - Identify slow operations

### Clean Up Commands
```bash
# Connect to Redis Cloud
redis-cli -h your-host -p your-port -a your-password

# Check memory usage
INFO memory

# Clear specific patterns
SCAN 0 MATCH session:* COUNT 100
DEL key1 key2 key3

# Clear everything (careful!)
FLUSHDB
```

## Cost Considerations

### Free Tier Limits
- 30MB RAM
- 1 Database
- No replication
- Limited to 30 connections

### When to Upgrade
- Memory usage > 25MB consistently
- Need for replication/HA
- More than 20 concurrent connections
- Production deployment

## Migration from Local to Redis Cloud

1. **Export Local Data** (if needed)
```bash
# Dump local Redis
redis-cli --rdb dump.rdb

# Or specific keys
redis-cli --scan --pattern "*" | while read key; do
    echo "SET $key $(redis-cli GET $key)" >> backup.txt
done
```

2. **Import to Redis Cloud**
```bash
# Use redis-cli with cloud credentials
redis-cli -h redis-cloud-host -p port -a password < backup.txt
```

## Railway Deployment Configuration

### railway.toml
```toml
[deploy]
startCommand = "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"

[build]
builder = "NIXPACKS"

[variables]
PYTHON_VERSION = "3.11"
```

### Environment Variables in Railway
```
# These go in Railway dashboard
APP_ENV=production
REDIS_URL=redis://:<password>@<redis-cloud-endpoint>:<port>/0
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key
SUPABASE_SERVICE_KEY=your-service-key
JWT_SECRET_KEY=your-production-secret
ANTHROPIC_API_KEY=your-anthropic-key
```

## Troubleshooting

### Connection Timeout
- Check firewall rules
- Verify Redis Cloud allows your IP
- Try with `rediss://` for TLS

### Authentication Failed
- Password might contain special characters - URL encode them
- Check password is correct in Redis Cloud dashboard

### SSL/TLS Issues
```python
# If having SSL issues, you might need:
import ssl
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Then pass ssl=ssl_context to connection
```

## Summary

Using Redis Cloud instead of local Redis:
1. ✅ Works for both local development and Railway
2. ✅ No need to manage Redis infrastructure
3. ✅ Free tier is sufficient for development
4. ✅ Easy to scale when needed
5. ✅ Same code works with just URL change

Just update your `REDIS_URL` in both local `.env` and Railway variables, and you're good to go!