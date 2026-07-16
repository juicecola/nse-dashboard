"""
Minimal in-process TTL cache.

Why not `functools.lru_cache`: it never expires, so a code deploy would be
needed to see new data. Why not a library like cachetools: one dependency
for ~15 lines of logic isn't worth it here.

This is per-process memory, which is exactly right for this app's shape:
Render runs a single worker (WEB_CONCURRENCY=1), and the free tier's
cold-start on idle already clears the cache naturally, so there's no
cross-worker invalidation problem to solve.
"""
import functools
import os
import time

DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

_registry: list["_TTLCache"] = []


class _TTLCache:
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self.store: dict[tuple, tuple[float, object]] = {}

    def clear(self):
        self.store.clear()


def ttl_cache(seconds: int = DEFAULT_TTL_SECONDS):
    """Decorator: cache a function's return value per distinct set of args."""

    def decorator(func):
        cache = _TTLCache(seconds)
        _registry.append(cache)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.monotonic()
            hit = cache.store.get(key)
            if hit is not None:
                expires_at, value = hit
                if now < expires_at:
                    return value
            value = func(*args, **kwargs)
            cache.store[key] = (now + cache.ttl_seconds, value)
            return value

        wrapper.cache_clear = cache.clear
        return wrapper

    return decorator


def clear_all_caches():
    for cache in _registry:
        cache.clear()
