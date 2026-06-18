"""
Root Cause Logger — Phase 6.

Structured, opinionated logger for the Root Cause Agent pipeline.
Logs each stage: input metrics, prompt, raw response, parsed output,
errors, retries, and execution time for full observability.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional


def get_root_cause_logger(name: str) -> logging.Logger:
    """Return a named logger for root cause pipeline stages."""
    return logging.getLogger(name)


class RootCauseLogger:
    """
    Structured logger for the Root Cause Agent.
    Provides named log methods for each pipeline stage.
    """

    def __init__(self, logger_name: str = "root_cause_agent") -> None:
        self._log = logging.getLogger(logger_name)

    def log_input(self, pod: str, namespace: str, severity: str, cpu: float) -> None:
        self._log.info(
            "[INPUT] pod=%s/%s | severity=%s | cpu=%.2f%%",
            namespace, pod, severity, cpu
        )

    def log_prompt(self, system_len: int, user_len: int) -> None:
        self._log.debug(
            "[PROMPT] system_chars=%d | user_chars=%d", system_len, user_len
        )

    def log_raw_response(self, raw: str) -> None:
        # Truncate long responses for readability
        self._log.debug("[RAW_RESPONSE] %.300s%s", raw, "…" if len(raw) > 300 else "")

    def log_parsed_output(self, root_cause: str, confidence: int, source: str) -> None:
        self._log.info(
            "[PARSED] root_cause=%s | confidence=%d | source=%s",
            root_cause, confidence, source
        )

    def log_execution_time(self, node: str, elapsed_ms: int) -> None:
        self._log.info("[TIMING] %s completed in %dms", node, elapsed_ms)

    def log_retry(self, attempt: int, max_attempts: int, error: str) -> None:
        self._log.warning(
            "[RETRY] attempt=%d/%d | error=%s", attempt, max_attempts, error
        )

    def log_fallback_triggered(self, reason: str) -> None:
        self._log.warning("[FALLBACK] Triggered: %s", reason)

    def log_error(self, stage: str, error: str) -> None:
        self._log.error("[ERROR] stage=%s | error=%s", stage, error)
