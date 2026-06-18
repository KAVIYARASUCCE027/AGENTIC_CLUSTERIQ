"""
Exception Handler Module — Phase 3.

Defines a hierarchy of custom exceptions for the Metric Service layer.
Every exception carries a structured message and is automatically logged
at the appropriate severity level when raised.

Exception Hierarchy:
    AgentBaseException
    ├── SpringBootConnectionException   — HTTP / network failures
    ├── MetricFetchException            — Logical fetch failures (bad status, empty body)
    ├── MetricValidationException       — Out-of-range or invalid metric values
    ├── CacheException                  — TTL cache read / write errors
    └── CalculatorException             — Derived-metric computation errors

Design Notes:
    • All exceptions inherit from ``AgentBaseException`` so callers can
      catch the entire family with a single ``except`` clause when needed.
    • Each subclass logs its message on construction so the call-site
      never has to remember to log before raising.
    • String representation includes the exception class name for
      unambiguous identification in aggregated log streams.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Base Exception
# =============================================================================

class AgentBaseException(Exception):
    """
    Root exception for the K8S Agentic AI metric pipeline.

    All domain-specific exceptions inherit from this class so that
    upstream callers can catch the entire family generically.

    Attributes:
        message: Human-readable error description.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:  # noqa: D105
        return f"[{self.__class__.__name__}] {self.message}"


# =============================================================================
# Connection Exceptions
# =============================================================================

class SpringBootConnectionException(AgentBaseException):
    """
    Raised when the Spring Boot backend is unreachable or returns a
    non-recoverable HTTP error (e.g. 5xx, connection refused, timeout).
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        self.status_code = status_code
        detail = message if status_code is None else f"{message} (HTTP {status_code})"
        logger.error("Spring Boot connection failure: %s", detail)
        super().__init__(detail)


# =============================================================================
# Fetch Exceptions
# =============================================================================

class MetricFetchException(AgentBaseException):
    """
    Raised when metrics cannot be retrieved from the backend even though
    the connection itself succeeded (e.g. 404 pod not found, empty payload).
    """

    def __init__(self, message: str) -> None:
        logger.error("Metric fetch failed: %s", message)
        super().__init__(message)


# =============================================================================
# Validation Exceptions
# =============================================================================

class MetricValidationException(AgentBaseException):
    """
    Raised when a metric value falls outside its acceptable range or
    violates a business constraint (e.g. cpu_usage > 100, replica_count < 1).
    """

    def __init__(self, field: str, value: object, reason: str) -> None:
        self.field = field
        self.value = value
        detail = f"Validation failed for '{field}' = {value!r}: {reason}"
        logger.warning("Metric validation error: %s", detail)
        super().__init__(detail)


# =============================================================================
# Cache Exceptions
# =============================================================================

class CacheException(AgentBaseException):
    """
    Raised when the TTL cache cannot be read from or written to.

    This is a non-fatal exception — callers should fall through to
    a live API call when the cache is unavailable.
    """

    def __init__(self, message: str) -> None:
        logger.warning("Cache error: %s", message)
        super().__init__(message)


# =============================================================================
# Calculator Exceptions
# =============================================================================

class CalculatorException(AgentBaseException):
    """
    Raised when a derived-metric calculation fails (e.g. division by
    zero in throttling percentage, insufficient data for trend detection).
    """

    def __init__(self, message: str) -> None:
        logger.error("Calculator error: %s", message)
        super().__init__(message)
