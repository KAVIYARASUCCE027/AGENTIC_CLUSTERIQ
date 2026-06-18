"""
Root Cause Prompt Builder — Phase 6.

Loads system prompt and user template from disk, injects live metric
values from RootCauseInputSchema, and returns the final prompts ready
for the Gemini service.

Keeping prompt construction separate from the Gemini call ensures the
service stays a thin HTTP wrapper and the prompt logic is independently
testable.
"""
from __future__ import annotations

import logging
from pathlib import Path

from schemas.root_cause_input import RootCauseInputSchema

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parent
_SYSTEM_PROMPT_FILE = _PROMPTS_DIR / "root_cause_system_prompt.txt"
_TEMPLATE_FILE      = _PROMPTS_DIR / "root_cause_template.txt"


def _load_file(path: Path) -> str:
    """Load and return the contents of a prompt file."""
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


class RootCausePromptBuilder:
    """
    Builds the (system_prompt, user_prompt) tuple for the Root Cause Agent.

    Usage:
        builder = RootCausePromptBuilder()
        system, user = builder.build(input_schema)
    """

    def __init__(self) -> None:
        self._system_prompt_template = _load_file(_SYSTEM_PROMPT_FILE)
        self._user_template = _load_file(_TEMPLATE_FILE)
        logger.debug("RootCausePromptBuilder: Prompt files loaded.")

    def build(self, inp: RootCauseInputSchema) -> tuple[str, str]:
        """
        Inject metric values into the user template.

        Args:
            inp: Validated input schema built from CPUState.

        Returns:
            (system_prompt, user_prompt) strings ready for Gemini.
        """
        # Format analyzer reasoning as a bulleted list
        reasoning_text = "\n".join(
            f"  - {r}" for r in inp.analyzer_reasoning
        ) if inp.analyzer_reasoning else "  - No prior reasoning available."

        user_prompt = self._user_template.format(
            pod_name=inp.pod_name,
            namespace=inp.namespace,
            severity=inp.severity.value,
            abnormality=inp.abnormality.value,
            current_cpu_usage=inp.cpu_metrics.current_cpu_usage,
            avg_cpu_5m=inp.cpu_metrics.avg_cpu_5m,
            avg_cpu_15m=inp.cpu_metrics.avg_cpu_15m,
            cpu_trend=inp.cpu_metrics.cpu_trend,
            throttling_percentage=inp.cpu_metrics.throttling_percentage,
            cpu_limit=inp.cpu_metrics.cpu_limit,
            cpu_request=inp.cpu_metrics.cpu_request,
            restart_count=inp.restart_metrics.restart_count,
            current_replicas=inp.replica_metrics.current_replicas,
            analyzer_reasoning=reasoning_text,
        )

        logger.debug("RootCausePromptBuilder: User prompt built for %s/%s.",
                     inp.namespace, inp.pod_name)

        return self._system_prompt_template, user_prompt
