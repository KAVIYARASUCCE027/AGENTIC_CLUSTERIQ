"""
Prometheus Service Module.

Provides methods to fetch Kubernetes metrics from Prometheus.
Currently returns mock data for development and testing purposes.
Will be replaced with actual Prometheus API calls in future phases.
"""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def get_cpu_metrics(namespace: str = "default", pod_name: str = "nginx") -> dict[str, Any]:
    """
    Retrieve CPU metrics for a specified pod in a namespace.

    Currently returns mock data simulating Prometheus CPU usage metrics.

    Args:
        namespace: The Kubernetes namespace of the target pod.
        pod_name: The name of the target pod.

    Returns:
        A dictionary containing CPU usage metrics with the following keys:
            - namespace: The Kubernetes namespace.
            - pod_name: The pod name.
            - cpu_usage_cores: Current CPU usage in cores.
            - cpu_limit_cores: CPU limit allocated to the pod.
            - cpu_usage_percent: CPU usage as a percentage of the limit.
            - timestamp: ISO 8601 timestamp of the measurement.
    """
    logger.info(
        "Fetching CPU metrics for pod '%s' in namespace '%s'.",
        pod_name,
        namespace,
    )

    # Mock CPU metrics data
    mock_metrics: dict[str, Any] = {
        "namespace": namespace,
        "pod_name": pod_name,
        "cpu_usage_cores": 0.75,
        "cpu_limit_cores": 1.0,
        "cpu_usage_percent": 75.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "CPU metrics retrieved: %.1f%% usage for pod '%s'.",
        mock_metrics["cpu_usage_percent"],
        pod_name,
    )

    return mock_metrics


def get_memory_metrics(namespace: str = "default", pod_name: str = "nginx") -> dict[str, Any]:
    """
    Retrieve memory metrics for a specified pod in a namespace.

    Currently returns mock data simulating Prometheus memory usage metrics.

    Args:
        namespace: The Kubernetes namespace of the target pod.
        pod_name: The name of the target pod.

    Returns:
        A dictionary containing memory usage metrics with the following keys:
            - namespace: The Kubernetes namespace.
            - pod_name: The pod name.
            - memory_usage_mb: Current memory usage in megabytes.
            - memory_limit_mb: Memory limit allocated to the pod.
            - memory_usage_percent: Memory usage as a percentage of the limit.
            - timestamp: ISO 8601 timestamp of the measurement.
    """
    logger.info(
        "Fetching memory metrics for pod '%s' in namespace '%s'.",
        pod_name,
        namespace,
    )

    # Mock memory metrics data
    mock_metrics: dict[str, Any] = {
        "namespace": namespace,
        "pod_name": pod_name,
        "memory_usage_mb": 256.0,
        "memory_limit_mb": 512.0,
        "memory_usage_percent": 50.0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info(
        "Memory metrics retrieved: %.1f%% usage for pod '%s'.",
        mock_metrics["memory_usage_percent"],
        pod_name,
    )

    return mock_metrics
