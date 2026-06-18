"""
Memory Logger — Phase 9.

Structured logging for the Memory Agent pipeline.
"""
from __future__ import annotations

import logging
from typing import Optional


class MemoryLogger:
    """Structured logger for the Memory Agent pipeline stages."""

    def __init__(self, logger_name: str = "memory_agent") -> None:
        self._log = logging.getLogger(logger_name)

    def log_input(self, pod: str, namespace: str) -> None:
        self._log.info("[INPUT] memory requested for pod=%s/%s", namespace, pod)

    def log_save_latency(self, incident_id: str, elapsed_ms: int) -> None:
        self._log.info("[SAVE] incident_id=%s | latency=%dms", incident_id, elapsed_ms)

    def log_retrieval(self, similar_count: int, pattern_count: int, elapsed_ms: int) -> None:
        self._log.info(
            "[RETRIEVE] similar=%d | patterns=%d | latency=%dms",
            similar_count, pattern_count, elapsed_ms
        )

    def log_similarity_score(self, incident_id: str, score: float) -> None:
        self._log.debug("[SIMILARITY] matched incident_id=%s | score=%.2f", incident_id, score)

    def log_fallback_triggered(self, reason: str) -> None:
        self._log.warning("[FALLBACK] Memory layer degraded: %s", reason)

    def log_error(self, stage: str, error: str) -> None:
        self._log.error("[ERROR] stage=%s | error=%s", stage, error)
