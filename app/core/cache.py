from typing import Any, Optional, Dict, Callable, Awaitable
from functools import wraps
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-memory cache implementation"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry["expires_at"] > datetime.now():
                    return entry["value"]
                else:
                    # Remove expired entry
                    del self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL"""
        async with self._lock:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": datetime.now(),
            }

    async def delete(self, key: str) -> None:
        """Delete specific key from cache"""
        async with self._lock:
            self._cache.pop(key, None)

    async def clear(self) -> None:
        """Clear all cache"""
        async with self._lock:
            self._cache.clear()

    async def cleanup_expired(self) -> None:
        """Remove expired entries"""
        async with self._lock:
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry["expires_at"] <= datetime.now()
            ]
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(
            1 for entry in self._cache.values() if entry["expires_at"] <= datetime.now()
        )
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
        }


# Global cache instance
cache = InMemoryCache()


def generate_cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    # Convert args and kwargs to a string representation
    key_data = {"args": args, "kwargs": kwargs}

    # Create a hash of the serialized data
    serialized = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode()).hexdigest()


def cached(ttl_seconds: int = 300, key_prefix: Optional[str] = None):
    """Decorator for caching function results"""

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            if key_prefix:
                func_name = f"{key_prefix}.{func_name}"

            cache_key = f"{func_name}:{generate_cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper

    return decorator


def cache_invalidate(*key_patterns: str):
    """Decorator for cache invalidation"""

    def decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache keys matching patterns
            for pattern in key_patterns:
                # Simple pattern matching - in production, use Redis with pattern support
                if pattern.endswith("*"):
                    prefix = pattern[:-1]
                    keys_to_delete = [
                        key for key in cache._cache.keys() if key.startswith(prefix)
                    ]
                    for key in keys_to_delete:
                        await cache.delete(key)
                        logger.debug(f"Invalidated cache key: {key}")
                else:
                    await cache.delete(pattern)
                    logger.debug(f"Invalidated cache key: {pattern}")

            return result

        return wrapper

    return decorator


class CacheManager:
    """Cache management utilities"""

    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Invalidate all cache entries for a user"""
        pattern = f"*user_id:{user_id}*"
        # In production with Redis, use SCAN with pattern
        keys_to_delete = [
            key for key in cache._cache.keys() if f"user_id:{user_id}" in key
        ]
        for key in keys_to_delete:
            await cache.delete(key)
        logger.info(
            f"Invalidated {len(keys_to_delete)} cache entries for user {user_id}"
        )

    @staticmethod
    async def invalidate_resource_cache(
        resource_type: str, resource_id: Optional[int] = None
    ):
        """Invalidate cache for specific resource type"""
        if resource_id:
            pattern = f"*{resource_type}*{resource_id}*"
        else:
            pattern = f"*{resource_type}*"

        keys_to_delete = [
            key
            for key in cache._cache.keys()
            if resource_type in key and (not resource_id or str(resource_id) in key)
        ]
        for key in keys_to_delete:
            await cache.delete(key)
        logger.info(
            f"Invalidated {len(keys_to_delete)} cache entries for {resource_type}"
        )

    @staticmethod
    async def warm_up_cache():
        """Warm up cache with frequently accessed data"""
        # This would typically load common data like faculties, roles, etc.
        logger.info("Cache warm-up completed")

    @staticmethod
    async def get_cache_stats() -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = cache.get_stats()

        # Add more detailed stats
        stats.update(
            {
                "cache_type": "in_memory",
                "timestamp": datetime.now().isoformat(),
            }
        )

        return stats


# Background task for cache cleanup
async def cache_cleanup_task():
    """Background task to cleanup expired cache entries"""
    while True:
        try:
            await cache.cleanup_expired()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error


# Cache configuration
CACHE_CONFIG = {
    "default_ttl": 300,  # 5 minutes
    "long_ttl": 3600,  # 1 hour
    "short_ttl": 60,  # 1 minute
}


# Common cache keys patterns
CACHE_KEYS = {
    "user_profile": "user:profile:{user_id}",
    "user_permissions": "user:permissions:{user_id}",
    "announcements_list": "announcements:list:page:{page}:category:{category}",
    "events_list": "events:list:filters:{filters_hash}",
    "courses_list": "courses:list",
    "faculties_list": "faculties:list",
    "locations_list": "locations:list",
    "rooms_list": "rooms:list",
}
