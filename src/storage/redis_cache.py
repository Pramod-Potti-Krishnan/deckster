"""
Redis cache implementation for the presentation generator.
Handles session caching, task queues, and pub/sub for agent communication.
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio.client import PubSub
from functools import wraps
import pickle
import hashlib

from ..utils.logger import storage_logger, log_execution_time, log_error


# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Cache TTL settings (in seconds)
SESSION_TTL = 3600  # 1 hour
PRESENTATION_CACHE_TTL = 300  # 5 minutes
AGENT_RESULT_TTL = 600  # 10 minutes
DEFAULT_TTL = 300  # 5 minutes


class RedisCache:
    """Redis cache manager with session, caching, and pub/sub support."""
    
    def __init__(self, url: str = REDIS_URL, password: Optional[str] = REDIS_PASSWORD):
        """
        Initialize Redis cache client.
        
        Args:
            url: Redis connection URL
            password: Optional Redis password
        """
        self.url = url
        self.password = password
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[PubSub] = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._subscription_tasks: List[asyncio.Task] = []
        
        storage_logger.info("Redis cache initialized", url=url)
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis = redis.from_url(
                self.url,
                password=self.password,
                db=REDIS_DB,
                decode_responses=True,
                encoding="utf-8"
            )
            
            # Test connection
            await self.redis.ping()
            
            # Initialize pub/sub
            self.pubsub = self.redis.pubsub()
            
            storage_logger.info("Redis connected successfully")
        except Exception as e:
            log_error(e, "redis_connection_failed")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        try:
            # Cancel subscription tasks
            for task in self._subscription_tasks:
                task.cancel()
            
            # Close pub/sub
            if self.pubsub:
                await self.pubsub.close()
            
            # Close main connection
            if self.redis:
                await self.redis.close()
            
            storage_logger.info("Redis disconnected")
        except Exception as e:
            log_error(e, "redis_disconnect_failed")
    
    # Session Management
    @log_execution_time("redis.set_session")
    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        ttl: int = SESSION_TTL
    ) -> bool:
        """
        Store session data in Redis.
        
        Args:
            session_id: Session identifier
            data: Session data
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        key = f"session:{session_id}"
        
        try:
            # Add timestamp
            data["_last_updated"] = datetime.utcnow().isoformat()
            
            # Store as JSON
            result = await self.redis.setex(
                key,
                ttl,
                json.dumps(data)
            )
            
            storage_logger.debug(
                "Session stored",
                session_id=session_id,
                ttl=ttl
            )
            
            return result
        except Exception as e:
            log_error(e, "session_store_failed", {"session_id": session_id})
            return False
    
    @log_execution_time("redis.get_session")
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from Redis.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None
        """
        key = f"session:{session_id}"
        
        try:
            data = await self.redis.get(key)
            
            if data:
                # Extend TTL on access
                await self.redis.expire(key, SESSION_TTL)
                return json.loads(data)
            
            return None
        except Exception as e:
            log_error(e, "session_retrieve_failed", {"session_id": session_id})
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Redis.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted
        """
        key = f"session:{session_id}"
        
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            log_error(e, "session_delete_failed", {"session_id": session_id})
            return False
    
    async def extend_session_ttl(self, session_id: str, ttl: int = SESSION_TTL) -> bool:
        """
        Extend session TTL.
        
        Args:
            session_id: Session identifier
            ttl: New TTL in seconds
            
        Returns:
            True if extended
        """
        key = f"session:{session_id}"
        
        try:
            result = await self.redis.expire(key, ttl)
            return result
        except Exception as e:
            log_error(e, "session_ttl_extend_failed", {"session_id": session_id})
            return False
    
    # General Caching
    async def set_cache(
        self,
        key: str,
        value: Any,
        ttl: int = DEFAULT_TTL,
        namespace: str = "cache"
    ) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds
            namespace: Cache namespace
            
        Returns:
            True if successful
        """
        full_key = f"{namespace}:{key}"
        
        try:
            # Handle different value types
            if isinstance(value, (dict, list)):
                data = json.dumps(value)
            elif isinstance(value, (str, int, float, bool)):
                data = str(value)
            else:
                # Use pickle for complex objects
                data = pickle.dumps(value).hex()
            
            result = await self.redis.setex(full_key, ttl, data)
            
            storage_logger.debug(
                "Cache set",
                key=full_key,
                ttl=ttl
            )
            
            return result
        except Exception as e:
            log_error(e, "cache_set_failed", {"key": key})
            return False
    
    async def get_cache(
        self,
        key: str,
        namespace: str = "cache",
        default: Any = None
    ) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        full_key = f"{namespace}:{key}"
        
        try:
            data = await self.redis.get(full_key)
            
            if data is None:
                return default
            
            # Try to parse as JSON first
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                # Try as pickle
                try:
                    return pickle.loads(bytes.fromhex(data))
                except:
                    # Return as string
                    return data
                    
        except Exception as e:
            log_error(e, "cache_get_failed", {"key": key})
            return default
    
    async def delete_cache(self, key: str, namespace: str = "cache") -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key
            namespace: Cache namespace
            
        Returns:
            True if deleted
        """
        full_key = f"{namespace}:{key}"
        
        try:
            result = await self.redis.delete(full_key)
            return result > 0
        except Exception as e:
            log_error(e, "cache_delete_failed", {"key": key})
            return False
    
    # Agent Communication (Pub/Sub)
    async def publish_message(
        self,
        channel: str,
        message: Dict[str, Any]
    ) -> int:
        """
        Publish message to a channel.
        
        Args:
            channel: Channel name
            message: Message data
            
        Returns:
            Number of subscribers that received the message
        """
        try:
            # Add metadata
            message["_timestamp"] = datetime.utcnow().isoformat()
            message["_channel"] = channel
            
            # Publish
            subscribers = await self.redis.publish(
                f"agent:{channel}",
                json.dumps(message)
            )
            
            storage_logger.debug(
                "Message published",
                channel=channel,
                subscribers=subscribers
            )
            
            return subscribers
        except Exception as e:
            log_error(e, "publish_failed", {"channel": channel})
            return 0
    
    async def subscribe_channel(
        self,
        channel: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to a channel.
        
        Args:
            channel: Channel name
            callback: Async callback function
        """
        full_channel = f"agent:{channel}"
        
        # Store callback
        if full_channel not in self._subscribers:
            self._subscribers[full_channel] = []
        self._subscribers[full_channel].append(callback)
        
        # Subscribe if not already subscribed
        if full_channel not in [ch.decode() if isinstance(ch, bytes) else ch 
                                for ch in self.pubsub.channels]:
            await self.pubsub.subscribe(full_channel)
            
            # Start listener task
            task = asyncio.create_task(self._listen_channel(full_channel))
            self._subscription_tasks.append(task)
            
            storage_logger.info("Subscribed to channel", channel=channel)
    
    async def unsubscribe_channel(self, channel: str):
        """
        Unsubscribe from a channel.
        
        Args:
            channel: Channel name
        """
        full_channel = f"agent:{channel}"
        
        try:
            await self.pubsub.unsubscribe(full_channel)
            
            # Remove callbacks
            if full_channel in self._subscribers:
                del self._subscribers[full_channel]
            
            storage_logger.info("Unsubscribed from channel", channel=channel)
        except Exception as e:
            log_error(e, "unsubscribe_failed", {"channel": channel})
    
    async def _listen_channel(self, channel: str):
        """
        Internal method to listen to a channel.
        
        Args:
            channel: Full channel name
        """
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    # Parse message
                    try:
                        data = json.loads(message["data"])
                        
                        # Call all callbacks for this channel
                        callbacks = self._subscribers.get(channel, [])
                        for callback in callbacks:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(data)
                                else:
                                    callback(data)
                            except Exception as e:
                                log_error(e, "callback_failed", {
                                    "channel": channel,
                                    "callback": callback.__name__
                                })
                    except json.JSONDecodeError as e:
                        storage_logger.error(
                            "Invalid message format",
                            channel=channel,
                            error=str(e)
                        )
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            log_error(e, "channel_listener_failed", {"channel": channel})
    
    # Task Queue
    async def enqueue_task(
        self,
        queue: str,
        task: Dict[str, Any],
        priority: int = 0
    ) -> bool:
        """
        Add task to queue.
        
        Args:
            queue: Queue name
            task: Task data
            priority: Task priority (higher = more important)
            
        Returns:
            True if enqueued
        """
        queue_key = f"queue:{queue}"
        
        try:
            # Add task metadata
            task["_enqueued_at"] = datetime.utcnow().isoformat()
            task["_priority"] = priority
            
            # Add to sorted set (by priority)
            score = -priority  # Negative so higher priority comes first
            result = await self.redis.zadd(
                queue_key,
                {json.dumps(task): score}
            )
            
            storage_logger.debug(
                "Task enqueued",
                queue=queue,
                priority=priority
            )
            
            return result > 0
        except Exception as e:
            log_error(e, "enqueue_failed", {"queue": queue})
            return False
    
    async def dequeue_task(
        self,
        queue: str,
        timeout: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        Get task from queue.
        
        Args:
            queue: Queue name
            timeout: Blocking timeout in seconds (0 = non-blocking)
            
        Returns:
            Task data or None
        """
        queue_key = f"queue:{queue}"
        
        try:
            if timeout > 0:
                # Blocking pop
                result = await self.redis.bzpopmin(queue_key, timeout)
                if result:
                    _, task_json, _ = result
                    return json.loads(task_json)
            else:
                # Non-blocking pop
                result = await self.redis.zpopmin(queue_key, 1)
                if result:
                    task_json, _ = result[0]
                    return json.loads(task_json)
            
            return None
        except Exception as e:
            log_error(e, "dequeue_failed", {"queue": queue})
            return None
    
    async def get_queue_size(self, queue: str) -> int:
        """
        Get number of tasks in queue.
        
        Args:
            queue: Queue name
            
        Returns:
            Queue size
        """
        queue_key = f"queue:{queue}"
        
        try:
            return await self.redis.zcard(queue_key)
        except Exception as e:
            log_error(e, "queue_size_failed", {"queue": queue})
            return 0
    
    # Rate Limiting
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """
        Check rate limit for an identifier.
        
        Args:
            identifier: Unique identifier (e.g., user_id, IP)
            limit: Request limit
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, requests_made)
        """
        key = f"rate_limit:{identifier}"
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        try:
            # Remove old entries
            await self.redis.zremrangebyscore(key, "-inf", window_start)
            
            # Count current entries
            current_count = await self.redis.zcard(key)
            
            if current_count >= limit:
                return False, current_count
            
            # Add current request
            await self.redis.zadd(key, {str(now): now})
            
            # Set expiry
            await self.redis.expire(key, window_seconds)
            
            return True, current_count + 1
        except Exception as e:
            log_error(e, "rate_limit_check_failed", {"identifier": identifier})
            # Fail open in case of error
            return True, 0
    
    # Distributed Locking
    async def acquire_lock(
        self,
        resource: str,
        ttl: int = 30,
        retry_times: int = 3,
        retry_delay: float = 0.1
    ) -> Optional[str]:
        """
        Acquire a distributed lock.
        
        Args:
            resource: Resource to lock
            ttl: Lock TTL in seconds
            retry_times: Number of retries
            retry_delay: Delay between retries
            
        Returns:
            Lock token if acquired, None otherwise
        """
        lock_key = f"lock:{resource}"
        lock_token = hashlib.sha256(
            f"{resource}:{datetime.utcnow().timestamp()}".encode()
        ).hexdigest()
        
        for _ in range(retry_times):
            try:
                # Try to set lock
                result = await self.redis.set(
                    lock_key,
                    lock_token,
                    nx=True,  # Only set if not exists
                    ex=ttl
                )
                
                if result:
                    storage_logger.debug(
                        "Lock acquired",
                        resource=resource,
                        token=lock_token[:8]
                    )
                    return lock_token
                
                # Wait before retry
                await asyncio.sleep(retry_delay)
            except Exception as e:
                log_error(e, "lock_acquire_failed", {"resource": resource})
                
        return None
    
    async def release_lock(self, resource: str, token: str) -> bool:
        """
        Release a distributed lock.
        
        Args:
            resource: Resource to unlock
            token: Lock token
            
        Returns:
            True if released
        """
        lock_key = f"lock:{resource}"
        
        try:
            # Lua script to ensure we only delete our own lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = await self.redis.eval(lua_script, 1, lock_key, token)
            
            if result:
                storage_logger.debug(
                    "Lock released",
                    resource=resource,
                    token=token[:8]
                )
            
            return bool(result)
        except Exception as e:
            log_error(e, "lock_release_failed", {"resource": resource})
            return False
    
    # Cache Decorators
    def cache_result(
        self,
        ttl: int = DEFAULT_TTL,
        key_prefix: str = "",
        namespace: str = "func_cache"
    ):
        """
        Decorator to cache function results.
        
        Args:
            ttl: Cache TTL in seconds
            key_prefix: Optional key prefix
            namespace: Cache namespace
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
                
                # Try to get from cache
                cached = await self.get_cache(cache_key, namespace)
                if cached is not None:
                    storage_logger.debug(
                        "Cache hit",
                        function=func.__name__,
                        key=cache_key
                    )
                    return cached
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Cache result
                await self.set_cache(cache_key, result, ttl, namespace)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, we need to run in event loop
                loop = asyncio.get_event_loop()
                return loop.run_until_complete(
                    async_wrapper(*args, **kwargs)
                )
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        
        return decorator
    
    # Health Check
    async def health_check(self) -> bool:
        """
        Check Redis connection health.
        
        Returns:
            True if healthy
        """
        try:
            result = await self.redis.ping()
            return result
        except Exception:
            return False


# Singleton instance
_redis_instance: Optional[RedisCache] = None


async def get_redis() -> RedisCache:
    """Get Redis cache instance."""
    global _redis_instance
    
    if _redis_instance is None:
        _redis_instance = RedisCache()
        await _redis_instance.connect()
    
    return _redis_instance


# Export main components
__all__ = [
    'RedisCache',
    'get_redis'
]