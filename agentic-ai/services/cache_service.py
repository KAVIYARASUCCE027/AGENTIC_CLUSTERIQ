"""
Cache Service Module — Phase 3.

Provides a lightweight, thread-safe, in-memory TTL cache for metric
responses.  Designed to reduce redundant Spring Boot API calls during
bursts of analysis requests for the same pod.

Features:
    • Configurable TTL (time-to-live) per entry.
    • Automatic expiration — stale entries are evicted on read.
    • Cache-hit / cache-miss logging for observability.
    • Thread-safe via ``threading.Lock``.
    • Singleton access via ``get_cache_service()``.

Architecture Note:
    This is an **application-level** cache — it does NOT replace Redis or
    Memcached for multi-process / multi-node deployments.  Its purpose is
    to absorb duplicate calls within a single uvicorn worker process.

Usage:
    >>> from services.cache_service import get_cache_service
    >>>
    >>> cache = get_cache_service(ttl_seconds=60)
    >>> cache.get("pod:nginx:cpu")        # None on first call
    >>> cache.set("pod:nginx:cpu", data)
    >>> cache.get("pod:nginx:cpu")        # returns data (within TTL)
"""

from __future__ import annotations

import logging
import threading
import time
from functools import lru_cache
from typing import Any, Optional

from services.exception_handler import CacheException

logger = logging.getLogger(__name__)


class CacheEntry:
    """
    Internal wrapper that pairs a cached value with its expiration time.

    Attributes:
        value: The cached object.
        expires_at: UNIX timestamp after which this entry is stale.
    """

    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl_seconds: float) -> None:
        self.value = value
        self.expires_at = time.monotonic() + ttl_seconds


class CacheService:
    """
    Thread-safe, in-memory TTL cache for metric responses.

    Args:
        ttl_seconds: Default time-to-live for every cache entry.
    """

    def __init__(self, ttl_seconds: float = 60.0) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        logger.info(
            "CacheService initialised with TTL = %.1fs.", self._ttl,
        )

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value, or ``None`` if the key is missing or expired.
        """
        try:
            with self._lock:
                entry = self._store.get(key)

                if entry is None:
                    logger.debug("Cache MISS: key='%s' (not found).", key)
                    return None

                if time.monotonic() > entry.expires_at:
                    # Entry has expired — evict it
                    del self._store[key]
                    logger.info("Cache MISS: key='%s' (expired).", key)
                    return None

                logger.info("Cache HIT: key='%s'.", key)
                return entry.value

        except Exception as exc:
            raise CacheException(f"Failed to read cache key '{key}': {exc}") from exc

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache.
            ttl_seconds: Optional per-entry TTL override.  Falls back to
                the service-wide default when ``None``.
        """
        try:
            effective_ttl = ttl_seconds if ttl_seconds is not None else self._ttl
            with self._lock:
                self._store[key] = CacheEntry(value, effective_ttl)
            logger.info(
                "Cache SET: key='%s' (TTL=%.1fs).", key, effective_ttl,
            )
        except Exception as exc:
            raise CacheException(f"Failed to write cache key '{key}': {exc}") from exc

    def invalidate(self, key: str) -> bool:
        """
        Remove a specific key from the cache.

        Args:
            key: The cache key to remove.

        Returns:
            ``True`` if the key existed and was removed, ``False`` otherwise.
        """
        with self._lock:
            removed = self._store.pop(key, None) is not None

        if removed:
            logger.info("Cache INVALIDATED: key='%s'.", key)
        else:
            logger.debug("Cache INVALIDATE (no-op): key='%s' not found.", key)

        return removed

    def clear(self) -> int:
        """
        Remove all entries from the cache.

        Returns:
            The number of entries that were evicted.
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()

        logger.info("Cache CLEARED: %d entries evicted.", count)
        return count

    def size(self) -> int:
        """Return the current number of entries (including potentially expired ones)."""
        with self._lock:
            return len(self._store)

    # -----------------------------------------------------------------
    # Cache Key Builders
    # -----------------------------------------------------------------

    @staticmethod
    def build_pod_metric_key(namespace: str, pod_name: str, metric_type: str) -> str:
        """
        Build a deterministic cache key for a pod metric.

        Args:
            namespace: Kubernetes namespace.
            pod_name: Pod name.
            metric_type: Metric category (e.g. ``"cpu"``, ``"restarts"``).

        Returns:
            A colon-delimited cache key string.
        """
        return f"pod:{namespace}:{pod_name}:{metric_type}"


# =============================================================================
# Singleton Accessor
# =============================================================================

@lru_cache(maxsize=1)
def get_cache_service(ttl_seconds: float = 60.0) -> CacheService:
    """
    Return a process-wide singleton ``CacheService`` instance.

    The TTL is only honoured on the **first** call; subsequent calls
    return the same instance regardless of the ``ttl_seconds`` argument.

    Args:
        ttl_seconds: Default TTL for cache entries.

    Returns:
        The singleton ``CacheService``.
    """
    return CacheService(ttl_seconds=ttl_seconds)
