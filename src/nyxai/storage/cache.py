"""In-memory cache management.

This module provides async in-memory cache operations and caching decorators.
"""

import functools
import hashlib
import json
import time
from collections.abc import Callable
from typing import Any, TypeVar

from nyxai.config import get_settings

F = TypeVar("F", bound=Callable[..., Any])


class CacheItem:
    """Cache item with expiration."""

    def __init__(self, value: Any, ttl: int | None = None):
        """Initialize cache item.

        Args:
            value: The cached value.
            ttl: Time to live in seconds. If None, no expiration.
        """
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if the item is expired.

        Returns:
            bool: True if expired, False otherwise.
        """
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


class CacheManager:
    """Manages in-memory cache operations.

    This class provides an async interface to an in-memory cache,
    with support for key expiration and serialization.

    Example:
        >>> cache = CacheManager()
        >>> await cache.set("key", {"data": "value"}, ttl=300)
        >>> value = await cache.get("key")
        >>> await cache.delete("key")
        >>> await cache.close()
    """

    def __init__(self) -> None:
        """Initialize the cache manager."""
        self._cache: dict[str, CacheItem] = {}

    async def connect(self) -> None:
        """Initialize the cache (no-op for in-memory)."""
        pass

    async def close(self) -> None:
        """Close the cache (no-op for in-memory)."""
        self._cache.clear()

    async def get(self, key: str) -> Any | None:
        """Get a value from cache.

        Args:
            key: The cache key.

        Returns:
            Any | None: The cached value or None if not found or expired.
        """
        item = self._cache.get(key)
        if item is None:
            return None
        if item.is_expired():
            del self._cache[key]
            return None
        return item.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set a value in cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl: Time to live in seconds. If None, no expiration.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self._cache[key] = CacheItem(value, ttl)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache.

        Args:
            key: The cache key.

        Returns:
            bool: True if key was deleted, False otherwise.
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache.

        Args:
            key: The cache key.

        Returns:
            bool: True if key exists and is not expired, False otherwise.
        """
        item = self._cache.get(key)
        if item is None:
            return False
        if item.is_expired():
            del self._cache[key]
            return False
        return True

    async def ttl(self, key: str) -> int:
        """Get the remaining TTL of a key.

        Args:
            key: The cache key.

        Returns:
            int: TTL in seconds, -1 if no expiration, -2 if key doesn't exist or expired.
        """
        item = self._cache.get(key)
        if item is None:
            return -2
        if item.is_expired():
            del self._cache[key]
            return -2
        if item.ttl is None:
            return -1
        remaining = item.ttl - (time.time() - item.created_at)
        return max(0, int(remaining))

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key.

        Args:
            key: The cache key.
            seconds: Expiration time in seconds.

        Returns:
            bool: True if expiration was set, False otherwise.
        """
        item = self._cache.get(key)
        if item is None:
            return False
        if item.is_expired():
            del self._cache[key]
            return False
        item.ttl = seconds
        item.created_at = time.time()
        return True

    async def keys(self, pattern: str = "*") -> list[str]:
        """Get keys matching a pattern.

        Args:
            pattern: The pattern to match (e.g., "user:*").

        Returns:
            list[str]: List of matching keys.
        """
        import fnmatch
        # Clean expired keys first
        self._clean_expired()
        return [key for key in self._cache if fnmatch.fnmatch(key, pattern)]

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern.

        Args:
            pattern: The pattern to match.

        Returns:
            int: Number of keys deleted.
        """
        import fnmatch
        # Clean expired keys first
        self._clean_expired()
        keys_to_delete = [key for key in self._cache if fnmatch.fnmatch(key, pattern)]
        for key in keys_to_delete:
            del self._cache[key]
        return len(keys_to_delete)

    async def health_check(self) -> bool:
        """Check cache health (always true for in-memory).

        Returns:
            bool: Always True.
        """
        return True

    def _clean_expired(self) -> None:
        """Clean up expired items from the cache."""
        expired_keys = [key for key, item in self._cache.items() if item.is_expired()]
        for key in expired_keys:
            del self._cache[key]


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
