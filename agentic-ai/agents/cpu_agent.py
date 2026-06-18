"""
CPU Agent Module.

Provides the high-level CPU analysis agent that orchestrates the
LangGraph pipeline and returns structured results.
"""

import logging
from typing import Any

from graph.cpu_graph import build_cpu_graph
from memory.conversation_memory import save_message

logger = logging.getLogger(__name__)


def run_cpu_agent(namespace: str, pod_name: str) -> dict[str, Any]:
    """
    Execute the CPU analysis agent pipeline.

    Orchestrates the full CPU analysis workflow:
        1. Collect CPU metrics from Prometheus
        2. Analyze metrics using Gemini LLM
        3. Generate actionable recommendations

    Saves the interaction to conversation memory for future reference.

    Args:
        namespace: The Kubernetes namespace of the target pod.
        pod_name: The name of the target pod.

    Returns:
        A dictionary containing:
            - status: 'success' or 'error'
            - message: The combined analysis and recommendation result,
                       or an error description.

    Raises:
        No exceptions are raised; all errors are caught and returned
        in the response dictionary.
    """
    logger.info(
        "CPU Agent: Starting analysis for pod '%s' in namespace '%s'.",
        pod_name,
        namespace,
    )

    try:
        # Build the LangGraph pipeline
        cpu_graph = build_cpu_graph()

        # Prepare initial state
        initial_state: dict[str, Any] = {
            "namespace": namespace,
            "pod_name": pod_name,
        }

        # Execute the graph
        logger.info("CPU Agent: Executing graph pipeline...")
        result: dict[str, Any] = cpu_graph.invoke(initial_state)

        # Extract results
        analysis: str = result.get("analysis_result", "No analysis available.")
        recommendation: str = result.get("recommendation", "No recommendation available.")

        # Combine output
        combined_output: str = (
            f"## CPU Analysis\n\n{analysis}\n\n"
            f"---\n\n"
            f"## Recommendations\n\n{recommendation}"
        )

        # Save to conversation memory
        save_message(
            role="user",
            content=f"Analyze CPU for pod '{pod_name}' in namespace '{namespace}'.",
        )
        save_message(role="assistant", content=combined_output)

        logger.info("CPU Agent: Analysis completed successfully.")

        return {
            "status": "success",
            "message": combined_output,
        }

    except Exception as exc:
        error_msg: str = f"CPU Agent failed: {exc}"
        logger.error(error_msg, exc_info=True)

        return {
            "status": "error",
            "message": error_msg,
        }
