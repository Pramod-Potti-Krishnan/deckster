#!/usr/bin/env python3
"""Test Redis Cloud connection"""

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
        
        # Close connection
        await client.close()
        
        print("\n✅ All Redis tests passed!")
        print("Your Redis Cloud connection is working perfectly!")
        
    except ImportError:
        print("❌ Error: redis package not installed")
        print("Run: pip install redis")
    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {e}")
        print("\nTroubleshooting:")
        print("1. Check if the Redis Cloud instance is active")
        print("2. Verify the password is correct")
        print("3. Check if your IP is allowed (if IP restrictions are enabled)")

# Test with the app's Redis client
async def test_app_redis():
    """Test using the app's Redis client."""
    print("\n" + "="*50)
    print("Testing with app's Redis client...")
    
    try:
        from src.storage.redis_cache import RedisCache
        
        # Create client with your URL
        client = RedisCache(
            url="redis://default:KgcqcsrnMJcZA0ibVdCxJKRXpom7z5ER@redis-13447.c245.us-east-1-3.ec2.redns.redis-cloud.com:13447"
        )
        
        # Connect
        await client.connect()
        
        # Test health check
        health = await client.health_check()
        print(f"✅ Health check: {'Passed' if health else 'Failed'}")
        
        # Test cache operations
        await client.set_cache("test_cache", {"message": "Hello from cache!"})
        cached = await client.get_cache("test_cache")
        print(f"✅ Cache test: {cached}")
        
        # Disconnect
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ App client test failed: {e}")

if __name__ == "__main__":
    # Run both tests
    asyncio.run(test_redis_connection())
    asyncio.run(test_app_redis())