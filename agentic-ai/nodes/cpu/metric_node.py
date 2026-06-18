"""
Metric Node Module — Phase 3.

LangGraph node responsible for populating the ``metrics`` section of
``CPUState``.  This is the **first real processing node** in the CPU
analysis pipeline.

Responsibilities:
    1. Update metadata to reflect that this node is executing.
    2. Delegate all metric work to ``CPUMetricService``.
    3. Record success / failure in metadata.
    4. Return the updated ``CPUState``.

This node performs **no** calculations, validations, or HTTP calls
directly — all of that is delegated to the service layer so the node
remains a thin orchestration wrapper.

Usage (within a LangGraph StateGraph):
    >>> from nodes.cpu.metric_node import run_metric_node
    >>>
    >>> graph.add_node("metric_node", run_metric_node)
"""

from __future__ import annotations

import logging
from typing import Any

from schemas.cpu_state import CPUState, ExecutionStatus
from services.cpu_metric_service import CPUMetricService
from services.exception_handler import AgentBaseException

logger = logging.getLogger(__name__)

# Module-level constant for the node name
_NODE_NAME: str = "metric_node"


def run_metric_node(state: CPUState) -> CPUState:
    """
    LangGraph node that collects and populates CPU metrics.

    Workflow:
        1. Mark metadata → status=RUNNING, current_node="metric_node".
        2. Invoke ``CPUMetricService.collect_and_populate()``.
        3. On success → append "metric_node" to visited_nodes.
        4. On failure → set status=FAILED with error message.

    Args:
        state: The current ``CPUState`` with ``inputs`` already populated.

    Returns:
        Updated ``CPUState`` with ``metrics`` populated and ``metadata``
        reflecting the outcome of this node's execution.
    """
    logger.info(
        "━━━ Metric Node START ━━━ pod='%s', namespace='%s'.",
        state.inputs.pod_name,
        state.inputs.namespace,
    )

    # --- Step 1: Mark as running ---
    state = state.mark_running(_NODE_NAME)
    logger.info("Metadata updated: status=RUNNING, current_node='%s'.", _NODE_NAME)

    try:
        # --- Step 2: Delegate to CPUMetricService ---
        service = CPUMetricService()
        state = service.collect_and_populate(state)

        # --- Step 3: Mark node completed ---
        state = state.mark_node_completed(_NODE_NAME)

        logger.info(
            "━━━ Metric Node SUCCESS ━━━ "
            "cpu=%.1f%%, trend=%s, throttle=%.1f%%, "
            "visited=%s.",
            state.metrics.cpu_usage,
            state.metrics.cpu_trend.value,
            state.metrics.throttling_percentage,
            state.metadata.visited_nodes,
        )

        return state

    except AgentBaseException as exc:
        # Domain-specific failure — already logged by the exception
        state = state.mark_failed(str(exc))
        logger.error(
            "━━━ Metric Node FAILED ━━━ %s", exc,
        )
        return state

    except Exception as exc:
        # Unexpected failure — log full traceback
        error_msg = f"Unexpected error in metric_node: {exc}"
        state = state.mark_failed(error_msg)
        logger.error(
            "━━━ Metric Node FAILED (unexpected) ━━━ %s",
            exc,
            exc_info=True,
        )
        return state
