"""Redis cache connection and management.

This module provides async Redis client operations and caching decorators.
"""

import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any, TypeVar

import redis.asyncio as redis
from redis.asyncio import Redis

from nyxai.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])


class CacheManager:
    """Manages Redis cache connections and operations.

    This class provides an async interface to Redis for caching,
    with support for key expiration and serialization.

    Example:
        >>> cache = CacheManager()
        >>> await cache.set("key", {"data": "value"}, ttl=300)
        >>> value = await cache.get("key")
        >>> await cache.delete("key")
        >>> await cache.close()
    """

    def __init__(self) -> None:
        """Initialize the cache manager without connection."""
        self._redis: Redis | None = None

    async def connect(self) -> None:
        """Initialize the Redis connection."""
        if self._redis is None:
            settings = get_settings()
            redis_settings = settings.redis

            self._redis = redis.from_url(
                str(redis_settings.url),
                password=redis_settings.password,
                socket_timeout=redis_settings.socket_timeout,
                socket_connect_timeout=redis_settings.socket_connect_timeout,
                decode_responses=True,
            )

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None

    @property
    def client(self) -> Redis:
        """Get the Redis client.

        Raises:
            RuntimeError: If the client has not been connected.

        Returns:
            Redis: The async Redis client.
        """
        if self._redis is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._redis

    async def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key: The cache key.

        Returns:
            Any | None: The cached value or None if not found.
        """
        value = await self.client.get(key)
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in cache.

        Args:
            key: The cache key.
            value: The value to cache (will be JSON serialized).
            ttl: Time to live in seconds. If None, no expiration.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            serialized = json.dumps(value, default=str)
            await self.client.set(key, serialized, ex=ttl)
            return True
        except (TypeError, json.JSONDecodeError):
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache.

        Args:
            key: The cache key.

        Returns:
            bool: True if key was deleted, False otherwise.
        """
        result = await self.client.delete(key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: The cache key.

        Returns:
            bool: True if key exists, False otherwise.
        """
        return await self.client.exists(key) > 0

    async def ttl(self, key: str) -> int:
        """Get the remaining TTL of a key.

        Args:
            key: The cache key.

        Returns:
            int: TTL in seconds, -1 if no expiration, -2 if key doesn't exist.
        """
        return await self.client.ttl(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key.

        Args:
            key: The cache key.
            seconds: Expiration time in seconds.

        Returns:
            bool: True if expiration was set, False otherwise.
        """
        return await self.client.expire(key, seconds)

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching a pattern.

        Args:
            pattern: The pattern to match (e.g., "user:*").

        Returns:
            list[str]: List of matching keys.
        """
        return [key async for key in self.client.scan_iter(match=pattern)]

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: The pattern to match.

        Returns:
            int: Number of keys deleted.
        """
        keys = await self.keys(pattern)
        if keys:
            return await self.client.delete(*keys)
        return 0

    async def health_check(self) -> bool:
        """Check Redis connectivity.

        Returns:
            bool: True if Redis is reachable, False otherwise.
        """
        try:
            return await self.client.ping()
        except Exception:
            return False


# Global cache manager instance
_cache_manager: CacheManager | None = None


async def init_cache() -> CacheManager:
    """Initialize the global cache manager.

    Returns:
        CacheManager: The initialized cache manager instance.
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        await _cache_manager.connect()
    return _cache_manager


async def close_cache() -> None:
    """Close the global cache manager."""
    global _cache_manager
    if _cache_manager is not None:
        await _cache_manager.close()
        _cache_manager = None


def get_redis_client() -> Redis:
    """Get the global Redis client.

    Raises:
        RuntimeError: If the cache manager has not been initialized.

    Returns:
        Redis: The async Redis client.
    """
    if _cache_manager is None:
        raise RuntimeError("Cache not initialized. Call init_cache() first.")
    return _cache_manager.client


def _generate_cache_key(prefix: str, func: Callable[..., Any], args: Any, kwargs: Any) -> str:
    """Generate a cache key from function call arguments.

    Args:
        prefix: Key prefix.
        func: The function being decorated.
        args: Positional arguments.
        kwargs: Keyword arguments.

    Returns:
        str: The generated cache key.
    """
    # Create a unique key based on function name and arguments
    key_data = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
    hash_value = hashlib.md5(key_data.encode()).hexdigest()  # noqa: S324
    return f"{prefix}:{hash_value}"


def cache_result(
    prefix: str = "cache",
    ttl: int = 300,
    key_func: Callable[..., str] | None = None,
) -> Callable[[F], F]:
    """Decorator to cache function results in Redis.

    Args:
        prefix: Key prefix for cache entries.
        ttl: Time to live in seconds.
        key_func: Optional custom key generation function.

    Returns:
        Callable: The decorator function.

    Example:
        >>> @cache_result(prefix="user", ttl=600)
        ... async def get_user(user_id: int) -> dict:
        ...     return await fetch_user_from_db(user_id)
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            if _cache_manager is None:
                # Cache not initialized, call function directly
                return await func(*args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(prefix, func, args, kwargs)

            # Try to get from cache
            cached_value = await _cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = await func(*args, **kwargs)
            await _cache_manager.set(cache_key, result, ttl=ttl)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            # For sync functions, we can't use async cache
            # This is a limitation - sync functions won't be cached
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper  # type: ignore[return-value]

    return decorator


# Need to import asyncio for the cache_result decorator
import asyncio  # noqa: E402
