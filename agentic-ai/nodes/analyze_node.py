"""
Analyze Node Module.

Responsible for analyzing CPU metrics using the Gemini LLM.
Acts as the second node in the CPU analysis graph pipeline.
"""

import logging
from typing import Any

from services.llm_service import get_llm
from prompts.cpu_prompt import CPU_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


def analyze_cpu(state: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze CPU metrics using the Gemini LLM.

    Takes the collected CPU metrics from the graph state, formats
    them into a structured prompt, and sends the prompt to the
    Gemini model for analysis.

    Args:
        state: The current graph state containing 'cpu_metrics'.

    Returns:
        Updated state dictionary with 'analysis_result' added.
    """
    cpu_metrics: dict[str, Any] = state.get("cpu_metrics", {})

    logger.info(
        "Analyze node: Analyzing CPU metrics for pod '%s'.",
        cpu_metrics.get("pod_name", "unknown"),
    )

    # Format the analysis prompt with actual metrics
    prompt: str = CPU_ANALYSIS_PROMPT.format(
        namespace=cpu_metrics.get("namespace", "unknown"),
        pod_name=cpu_metrics.get("pod_name", "unknown"),
        cpu_usage_cores=cpu_metrics.get("cpu_usage_cores", 0),
        cpu_limit_cores=cpu_metrics.get("cpu_limit_cores", 0),
        cpu_usage_percent=cpu_metrics.get("cpu_usage_percent", 0),
        timestamp=cpu_metrics.get("timestamp", "N/A"),
    )

    # Invoke the Gemini LLM
    llm = get_llm()
    response = llm.invoke(prompt)
    analysis_result: str = response.content

    logger.info("Analyze node: Analysis completed successfully.")

    return {**state, "analysis_result": analysis_result}
