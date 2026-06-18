"""
Action Planner Logger — Phase 8.

Structured logger for the Action Planner Agent pipeline.
"""
from __future__ import annotations

import logging
from typing import List


class ActionPlannerLogger:
    """Structured logger for the Action Planner Agent pipeline stages."""

    def __init__(self, logger_name: str = "action_planner_agent") -> None:
        self._log = logging.getLogger(logger_name)

    def log_input(self, pod: str, namespace: str, recommendations: List[str]) -> None:
        self._log.info(
            "[INPUT] pod=%s/%s | recs=%s",
            namespace, pod, recommendations
        )

    def log_prompt(self, system_len: int, user_len: int) -> None:
        self._log.debug("[PROMPT] system_chars=%d | user_chars=%d", system_len, user_len)

    def log_raw_response(self, raw: str) -> None:
        self._log.debug("[RAW_RESPONSE] %.300s%s", raw, "…" if len(raw) > 300 else "")

    def log_parsed_output(self, step_count: int, confidence: int, source: str) -> None:
        self._log.info(
            "[PARSED] step_count=%d | confidence=%d | source=%s",
            step_count, confidence, source
        )

    def log_execution_time(self, node: str, elapsed_ms: int) -> None:
        self._log.info("[TIMING] %s completed in %dms", node, elapsed_ms)

    def log_retry(self, attempt: int, max_attempts: int, error: str) -> None:
        self._log.warning("[RETRY] attempt=%d/%d | error=%s", attempt, max_attempts, error)

    def log_fallback_triggered(self, reason: str) -> None:
        self._log.warning("[FALLBACK] Triggered: %s", reason)

    def log_error(self, stage: str, error: str) -> None:
        self._log.error("[ERROR] stage=%s | error=%s", stage, error)
