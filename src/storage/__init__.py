"""
Storage module for the presentation generator.
Provides database and caching functionality.
"""

from .supabase import SupabaseStore, get_supabase
from .redis_cache import RedisCache, get_redis

__all__ = [
    'SupabaseStore',
    'get_supabase',
    'RedisCache', 
    'get_redis'
]