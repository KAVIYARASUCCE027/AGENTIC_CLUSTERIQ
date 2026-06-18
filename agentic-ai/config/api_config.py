"""
API Configuration Module — Phase 3.

Centralises all Spring Boot REST endpoint definitions in a single
location so that URL changes are propagated project-wide by editing
one file.

Design Notes:
    • Uses ``SPRING_BOOT_BASE_URL`` from ``config.settings`` as the
      root prefix for every endpoint.
    • Each endpoint is a classmethod that builds the full URL, making
      the call sites clean and typo-resistant.
    • The class is stateless — all methods are pure functions of
      their arguments.

Usage:
    >>> from config.api_config import SpringBootEndpoints
    >>>
    >>> url = SpringBootEndpoints.cpu_metrics("nginx")
    >>> # → "http://localhost:8080/api/pods/nginx/cpu"
"""

from __future__ import annotations

import logging

from config.settings import get_settings

logger = logging.getLogger(__name__)


class SpringBootEndpoints:
    """
    Registry of Spring Boot REST API endpoints.

    All methods return fully-qualified URLs by combining the configured
    ``SPRING_BOOT_BASE_URL`` with the resource path.
    """

    # -----------------------------------------------------------------
    # Pod Metric Endpoints
    # -----------------------------------------------------------------

    @classmethod
    def _base(cls) -> str:
        """Return the base URL with trailing slash stripped."""
        return get_settings().SPRING_BOOT_BASE_URL.rstrip("/")

    @classmethod
    def cpu_metrics(cls, pod_name: str) -> str:
        """
        GET /api/pods/{podName}/cpu

        Returns current CPU utilisation, limit, and request for the pod.
        """
        url = f"{cls._base()}/api/pods/{pod_name}/cpu"
        logger.debug("Resolved CPU metrics endpoint: %s", url)
        return url

    @classmethod
    def restart_count(cls, pod_name: str) -> str:
        """
        GET /api/pods/{podName}/restarts

        Returns the container restart count for the pod.
        """
        url = f"{cls._base()}/api/pods/{pod_name}/restarts"
        logger.debug("Resolved restart count endpoint: %s", url)
        return url

    @classmethod
    def replica_count(cls, pod_name: str) -> str:
        """
        GET /api/pods/{podName}/replicas

        Returns the current replica count for the pod's owner deployment.
        """
        url = f"{cls._base()}/api/pods/{pod_name}/replicas"
        logger.debug("Resolved replica count endpoint: %s", url)
        return url

    @classmethod
    def pod_details(cls, pod_name: str) -> str:
        """
        GET /api/pods/{podName}/details

        Returns extended pod metadata (node name, cluster, labels, etc.).
        """
        url = f"{cls._base()}/api/pods/{pod_name}/details"
        logger.debug("Resolved pod details endpoint: %s", url)
        return url
