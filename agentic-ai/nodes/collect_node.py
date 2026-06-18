"""
Collect Node Module.

Responsible for collecting CPU metrics from Prometheus (currently mock data).
Acts as the first node in the CPU analysis graph pipeline.
"""

import logging
from typing import Any

from services.prometheus_service import get_cpu_metrics

logger = logging.getLogger(__name__)


def collect_cpu_data(state: dict[str, Any]) -> dict[str, Any]:
    """
    Collect CPU metrics for a specified pod.

    Fetches CPU metrics from the Prometheus service and adds them
    to the graph state for downstream nodes to consume.

    Args:
        state: The current graph state containing 'namespace' and 'pod_name'.

    Returns:
        Updated state dictionary with 'cpu_metrics' added.
    """
    namespace: str = state.get("namespace", "default")
    pod_name: str = state.get("pod_name", "nginx")

    logger.info(
        "Collect node: Fetching CPU metrics for pod '%s' in namespace '%s'.",
        pod_name,
        namespace,
    )

    cpu_metrics: dict[str, Any] = get_cpu_metrics(
        namespace=namespace,
        pod_name=pod_name,
    )

    logger.info(
        "Collect node: CPU metrics collected — %.1f%% usage.",
        cpu_metrics["cpu_usage_percent"],
    )

    return {**state, "cpu_metrics": cpu_metrics}
