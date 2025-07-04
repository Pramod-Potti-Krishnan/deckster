#!/usr/bin/env python3
"""Test Redis Cloud connection - Fixed version"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_redis_connection():
    """Test Redis connection with various operations."""
    
    # Your Redis URL
    redis_url = "redis://default:KgcqcsrnMJcZA0ibVdCxJKRXpom7z5ER@redis-13447.c245.us-east-1-3.ec2.redns.redis-cloud.com:13447"
    
    print("🔄 Testing Redis Cloud connection...")
    print(f"Host: redis-13447.c245.us-east-1-3.ec2.redns.redis-cloud.com")
    print(f"Port: 13447")
    print("-" * 50)
    
    try:
        import redis.asyncio as redis
        
        # Connect to Redis
        client = redis.from_url(redis_url)
        
        # Test 1: Ping
        print("1. Testing PING...")
        pong = await client.ping()
        print(f"   ✅ PING response: {pong}")
        
        # Test 2: Set a key
        print("\n2. Testing SET...")
        await client.set("test_key", "Hello from Python 3.13!")
        print("   ✅ SET successful")
        
        # Test 3: Get the key
        print("\n3. Testing GET...")
        value = await client.get("test_key")
        print(f"   ✅ GET response: {value.decode() if value else 'None'}")
        
        # Test 4: Test expiration
        print("\n4. Testing EXPIRE...")
        await client.setex("temp_key", 10, "This expires in 10 seconds")
        ttl = await client.ttl("temp_key")
        print(f"   ✅ Key TTL: {ttl} seconds")
        
        # Test 5: Delete keys
        print("\n5. Cleaning up...")
        await client.delete("test_key", "temp_key")
        print("   ✅ Cleanup successful")
        
        # Test 6: Info
        print("\n6. Redis INFO...")
        info = await client.info()
        print(f"   ✅ Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   ✅ Connected clients: {info.get('connected_clients', 'Unknown')}")
        print(f"   ✅ Used memory: {info.get('used_memory_human', 'Unknown')}")
        
        # Close connection - use aclose() for redis 5.0+
        await client.aclose()
        
        print("\n✅ All Redis tests passed!")
        print("Your Redis Cloud connection is working perfectly!")
        
    except ImportError:
        print("❌ Error: redis package not installed")
        print("Run: pip install redis")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())