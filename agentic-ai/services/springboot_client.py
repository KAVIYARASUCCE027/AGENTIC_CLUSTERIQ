"""
Spring Boot Client Module — Phase 3.

Low-level HTTP client responsible for all communication with the
Spring Boot backend.  This module is a **pure transport layer** — it
handles HTTP requests, timeouts, retries, error mapping, and JSON
parsing, but contains **zero business logic**.

Responsibilities:
    • Execute GET requests against Spring Boot REST endpoints.
    • Apply connection / read timeouts from ``config.settings``.
    • Retry transient failures via ``retry_service``.
    • Map HTTP errors to domain-specific exceptions.
    • Log every request / response cycle for observability.
    • Return validated Pydantic response models.

Usage:
    >>> from services.springboot_client import SpringBootClient
    >>>
    >>> client = SpringBootClient()
    >>> cpu_data = client.get_cpu_metrics("nginx")
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from pydantic import BaseModel, Field

from config.api_config import SpringBootEndpoints
from config.settings import get_settings
from services.exception_handler import (
    MetricFetchException,
    SpringBootConnectionException,
)
from services.retry_service import with_retry

logger = logging.getLogger(__name__)


# =============================================================================
# Response Models — Spring Boot JSON Contracts
# =============================================================================

class CPUMetricResponse(BaseModel):
    """
    Response contract for ``GET /api/pods/{podName}/cpu``.

    Maps the Spring Boot JSON body into a type-safe Python object.
    """

    cpu_usage: float = Field(
        ..., description="Current CPU utilisation percentage.",
    )
    cpu_limit: float = Field(
        ..., description="CPU limit assigned to the pod (millicores).",
    )
    cpu_request: float = Field(
        ..., description="CPU request configured for the pod (millicores).",
    )
    throttling_percentage: float = Field(
        default=0.0,
        description="Percentage of CPU cycles throttled.",
    )


class RestartCountResponse(BaseModel):
    """Response contract for ``GET /api/pods/{podName}/restarts``."""

    restart_count: int = Field(
        ..., description="Number of container restarts.",
    )


class ReplicaCountResponse(BaseModel):
    """Response contract for ``GET /api/pods/{podName}/replicas``."""

    replica_count: int = Field(
        ..., description="Current number of running replicas.",
    )


class PodDetailsResponse(BaseModel):
    """Response contract for ``GET /api/pods/{podName}/details``."""

    pod_name: str = Field(..., description="Kubernetes pod name.")
    namespace: str = Field(..., description="Kubernetes namespace.")
    node_name: str = Field(default="", description="Worker node name.")
    cluster_name: str = Field(default="", description="Cluster identifier.")
    cpu_history: list[float] = Field(
        default_factory=list,
        description="Historical CPU usage data points (newest first).",
    )


# =============================================================================
# Client
# =============================================================================

class SpringBootClient:
    """
    HTTP client for the Spring Boot Kubernetes metrics backend.

    Instantiate once and reuse — the underlying ``requests.Session``
    keeps TCP connections alive for better performance.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._timeout: int = settings.REQUEST_TIMEOUT
        self._max_retries: int = settings.MAX_RETRIES
        self._retry_delay: float = settings.RETRY_DELAY

        # Persistent session for connection pooling
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "K8S-CPU-Agent/3.0",
        })

        logger.info(
            "SpringBootClient initialised — "
            "base_url=%s, timeout=%ds, max_retries=%d.",
            settings.SPRING_BOOT_BASE_URL,
            self._timeout,
            self._max_retries,
        )

    # -----------------------------------------------------------------
    # Internal Helpers
    # -----------------------------------------------------------------

    def _get(self, url: str) -> dict[str, Any]:
        """
        Execute a GET request with retry and timeout handling.

        Args:
            url: Fully-qualified URL to call.

        Returns:
            Parsed JSON response body as a dictionary.

        Raises:
            SpringBootConnectionException: On network / timeout / 5xx errors.
            MetricFetchException: On 4xx or unexpected response shape.
        """

        @with_retry(
            max_retries=self._max_retries,
            base_delay=self._retry_delay,
            retryable_exceptions=(
                ConnectionError,
                TimeoutError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ),
        )
        def _do_request() -> dict[str, Any]:
            logger.info("HTTP GET → %s (timeout=%ds)", url, self._timeout)

            try:
                response = self._session.get(url, timeout=self._timeout)
            except requests.exceptions.ConnectionError as exc:
                raise SpringBootConnectionException(
                    f"Cannot connect to Spring Boot at {url}: {exc}",
                ) from exc
            except requests.exceptions.Timeout as exc:
                raise SpringBootConnectionException(
                    f"Request to {url} timed out after {self._timeout}s.",
                ) from exc
            except requests.exceptions.RequestException as exc:
                raise SpringBootConnectionException(
                    f"Unexpected request error for {url}: {exc}",
                ) from exc

            # --- Handle non-2xx responses ---
            if response.status_code >= 500:
                raise SpringBootConnectionException(
                    f"Server error from {url}",
                    status_code=response.status_code,
                )
            if response.status_code >= 400:
                raise MetricFetchException(
                    f"Client error from {url} — HTTP {response.status_code}: "
                    f"{response.text[:200]}",
                )

            # --- Parse JSON ---
            try:
                data: dict[str, Any] = response.json()
            except ValueError as exc:
                raise MetricFetchException(
                    f"Invalid JSON response from {url}: {exc}",
                ) from exc

            logger.info("HTTP GET ← %s — %d OK.", url, response.status_code)
            return data

        return _do_request()

    # -----------------------------------------------------------------
    # Public API — one method per Spring Boot endpoint
    # -----------------------------------------------------------------

    def get_cpu_metrics(self, pod_name: str) -> CPUMetricResponse:
        """
        Fetch current CPU metrics for a pod.

        Args:
            pod_name: Kubernetes pod name.

        Returns:
            Validated ``CPUMetricResponse``.
        """
        url = SpringBootEndpoints.cpu_metrics(pod_name)
        data = self._get(url)
        logger.info(
            "CPU metrics received for pod '%s': usage=%.1f%%.",
            pod_name,
            data.get("cpu_usage", 0),
        )
        return CPUMetricResponse(**data)

    def get_restart_count(self, pod_name: str) -> RestartCountResponse:
        """
        Fetch the container restart count for a pod.

        Args:
            pod_name: Kubernetes pod name.

        Returns:
            Validated ``RestartCountResponse``.
        """
        url = SpringBootEndpoints.restart_count(pod_name)
        data = self._get(url)
        logger.info(
            "Restart count received for pod '%s': %d.",
            pod_name,
            data.get("restart_count", 0),
        )
        return RestartCountResponse(**data)

    def get_replica_count(self, pod_name: str) -> ReplicaCountResponse:
        """
        Fetch the current replica count for a pod.

        Args:
            pod_name: Kubernetes pod name.

        Returns:
            Validated ``ReplicaCountResponse``.
        """
        url = SpringBootEndpoints.replica_count(pod_name)
        data = self._get(url)
        logger.info(
            "Replica count received for pod '%s': %d.",
            pod_name,
            data.get("replica_count", 0),
        )
        return ReplicaCountResponse(**data)

    def get_pod_details(self, pod_name: str) -> PodDetailsResponse:
        """
        Fetch extended pod details (node, cluster, CPU history).

        Args:
            pod_name: Kubernetes pod name.

        Returns:
            Validated ``PodDetailsResponse``.
        """
        url = SpringBootEndpoints.pod_details(pod_name)
        data = self._get(url)
        logger.info(
            "Pod details received for pod '%s' on node '%s'.",
            pod_name,
            data.get("node_name", "unknown"),
        )
        return PodDetailsResponse(**data)
