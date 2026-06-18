"""
Recommendation Node Module.

Responsible for generating actionable CPU recommendations using
the Gemini LLM based on prior analysis results.
Acts as the third node in the CPU analysis graph pipeline.
"""

import logging
from typing import Any

from services.llm_service import get_llm
from prompts.cpu_prompt import (
    HIGH_CPU_RECOMMENDATION_PROMPT,
    NORMAL_CPU_RECOMMENDATION_PROMPT,
)

logger = logging.getLogger(__name__)

# CPU usage threshold for determining high vs normal recommendations
_HIGH_CPU_THRESHOLD: float = 80.0


def recommend_cpu_action(state: dict[str, Any]) -> dict[str, Any]:
    """
    Generate CPU recommendations based on analysis results.

    Selects the appropriate prompt template based on the CPU usage
    percentage (high vs. normal), then invokes the Gemini LLM to
    generate actionable recommendations.

    Args:
        state: The current graph state containing 'cpu_metrics'
               and 'analysis_result'.

    Returns:
        Updated state dictionary with 'recommendation' added.
    """
    cpu_metrics: dict[str, Any] = state.get("cpu_metrics", {})
    analysis_result: str = state.get("analysis_result", "No analysis available.")
    cpu_usage_percent: float = cpu_metrics.get("cpu_usage_percent", 0.0)

    logger.info(
        "Recommendation node: Generating recommendations for pod '%s' "
        "(CPU usage: %.1f%%).",
        cpu_metrics.get("pod_name", "unknown"),
        cpu_usage_percent,
    )

    # Select prompt template based on CPU usage severity
    if cpu_usage_percent >= _HIGH_CPU_THRESHOLD:
        logger.info("Recommendation node: Using HIGH CPU recommendation prompt.")
        prompt_template: str = HIGH_CPU_RECOMMENDATION_PROMPT
    else:
        logger.info("Recommendation node: Using NORMAL CPU recommendation prompt.")
        prompt_template = NORMAL_CPU_RECOMMENDATION_PROMPT

    # Format the recommendation prompt
    prompt: str = prompt_template.format(
        namespace=cpu_metrics.get("namespace", "unknown"),
        pod_name=cpu_metrics.get("pod_name", "unknown"),
        cpu_usage_cores=cpu_metrics.get("cpu_usage_cores", 0),
        cpu_limit_cores=cpu_metrics.get("cpu_limit_cores", 0),
        cpu_usage_percent=cpu_usage_percent,
        analysis_result=analysis_result,
    )

    # Invoke the Gemini LLM
    llm = get_llm()
    response = llm.invoke(prompt)
    recommendation: str = response.content

    logger.info("Recommendation node: Recommendations generated successfully.")

    return {**state, "recommendation": recommendation}
