"""
Retry Service Module — Phase 3.

Provides a production-grade retry decorator with exponential backoff,
configurable max attempts, and jitter.  Designed for wrapping unreliable
I/O calls (Spring Boot REST, network, cache) without leaking retry
logic into business code.

Features:
    • Exponential backoff with optional jitter to avoid thundering-herd.
    • Per-attempt structured logging (attempt number, delay, exception).
    • Configurable exception allow-list so only transient failures retry.
    • Raises the **last** exception unchanged when retries are exhausted.

Usage:
    >>> from services.retry_service import with_retry
    >>>
    >>> @with_retry(max_retries=3, base_delay=1.0)
    ... def fetch_data():
    ...     return requests.get(url, timeout=5).json()
"""

from __future__ import annotations

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Sequence, Type

logger = logging.getLogger(__name__)

# Default transient exceptions that warrant a retry
_DEFAULT_RETRYABLE: tuple[Type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Sequence[Type[Exception]] | None = None,
) -> Callable:
    """
    Decorator factory that wraps a function with retry-on-failure logic.

    Args:
        max_retries:
            Maximum number of retry attempts **after** the first call.
            Total attempts = 1 + max_retries.
        base_delay:
            Initial delay in seconds before the first retry.
        max_delay:
            Upper bound on the delay between retries (caps exponential growth).
        backoff_factor:
            Multiplier applied to the delay after each retry.
        jitter:
            If ``True``, adds ±25 % random jitter to each delay to prevent
            thundering-herd effects across concurrent callers.
        retryable_exceptions:
            Exception types that should trigger a retry.  Defaults to
            ``(ConnectionError, TimeoutError, OSError)``.

    Returns:
        A decorator that applies retry logic to the wrapped function.

    Raises:
        The last exception raised by the wrapped function after all
        retries have been exhausted.
    """
    retry_on: tuple[Type[Exception], ...] = (
        tuple(retryable_exceptions) if retryable_exceptions else _DEFAULT_RETRYABLE
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None
            delay = base_delay

            for attempt in range(1, max_retries + 2):  # 1-indexed, +1 for initial try
                try:
                    return func(*args, **kwargs)
                except retry_on as exc:
                    last_exception = exc

                    if attempt > max_retries:
                        logger.error(
                            "Retry exhausted for '%s' after %d attempts. "
                            "Last error: %s",
                            func.__name__,
                            attempt,
                            exc,
                        )
                        raise

                    # Calculate sleep with optional jitter
                    sleep_time = min(delay, max_delay)
                    if jitter:
                        sleep_time *= 1.0 + random.uniform(-0.25, 0.25)

                    logger.warning(
                        "Attempt %d/%d for '%s' failed: %s — "
                        "retrying in %.2fs…",
                        attempt,
                        max_retries + 1,
                        func.__name__,
                        exc,
                        sleep_time,
                    )

                    time.sleep(sleep_time)
                    delay *= backoff_factor

            # Should never reach here, but satisfy type checkers
            if last_exception is not None:
                raise last_exception  # pragma: no cover

        return wrapper
    return decorator
