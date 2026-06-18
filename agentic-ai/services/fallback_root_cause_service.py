"""
Fallback Root Cause Service — Phase 6.

Provides a deterministic, rule-based root cause determination when:
  - Gemini API is unavailable or fails all retries
  - Gemini returns confidence < 60
  - Gemini returns root_cause == UNKNOWN

Rules mirror the Phase 5 Analyzer heuristics but produce
RootCauseOutputState rather than AnalyzerOutputState.

This guarantees production reliability with zero external dependencies.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import config.analyzer_constants as constants
from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource
from schemas.root_cause_input import RootCauseInputSchema
from schemas.root_cause_output import RootCauseOutputState, CandidateCause
from utils.root_cause_logger import RootCauseLogger

logger = logging.getLogger(__name__)
rc_logger = RootCauseLogger("services.fallback_root_cause_service")


class FallbackRootCauseService:
    """
    Deterministic rule-based fallback for root cause analysis.

    Rules evaluated in priority order:
        1. CPU Spike      — high current, low average
        2. Limit Reached  — CPU near configured limit
        3. Pod Restarting — high restart count
        4. Replica Issue  — high CPU with single replica
        5. Sustained High — all averages high
        6. UNKNOWN        — no rules matched
    """

    def analyze(self, inp: RootCauseInputSchema) -> RootCauseOutputState:
        """
        Evaluate deterministic rules and return the best-matching root cause.

        Args:
            inp: Validated input schema from CPUState.

        Returns:
            RootCauseOutputState with source=FALLBACK.
        """
        cpu   = inp.cpu_metrics.current_cpu_usage
        avg5  = inp.cpu_metrics.avg_cpu_5m
        avg15 = inp.cpu_metrics.avg_cpu_15m
        limit = inp.cpu_metrics.cpu_limit
        restarts = inp.restart_metrics.restart_count
        replicas = inp.replica_metrics.current_replicas

        evidence:  list[str] = []
        reasoning: list[str] = []
        candidates: list[CandidateCause] = []
        root_cause = RootCauseType.UNKNOWN
        confidence = 0

        # ── Rule 1: CPU Spike ───────────────────────────────────────────────
        if (cpu >= constants.SPIKE_CURRENT_MIN and
                avg5 <= constants.SPIKE_AVG_MAX):
            root_cause = RootCauseType.WORKLOAD_SPIKE
            confidence = 85
            evidence.append(f"Current CPU is {cpu}% but 5m average is only {avg5}%.")
            reasoning.append("A large gap between current and 5m average indicates a sudden spike.")
            candidates.append(CandidateCause(cause=RootCauseType.APPLICATION_BUG, confidence=40))
            candidates.append(CandidateCause(cause=RootCauseType.INSUFFICIENT_REPLICAS, confidence=30))

        # ── Rule 2: CPU Limit Reached ───────────────────────────────────────
        elif limit > 0 and cpu >= constants.THROTTLING_LIMIT_THRESHOLD:
            root_cause = RootCauseType.CPU_LIMIT_REACHED
            confidence = 88
            evidence.append(f"CPU usage {cpu}% is at or near configured limit of {limit} millicores.")
            reasoning.append("Pod is throttled because it cannot burst beyond its CPU limit.")
            candidates.append(CandidateCause(cause=RootCauseType.RESOURCE_REQUEST_TOO_LOW, confidence=60))
            candidates.append(CandidateCause(cause=RootCauseType.INSUFFICIENT_REPLICAS, confidence=50))

        # ── Rule 3: Pod Restarting ──────────────────────────────────────────
        elif restarts > constants.RESTART_THRESHOLD:
            root_cause = RootCauseType.POD_RESTARTING
            confidence = 82
            evidence.append(f"Pod has restarted {restarts} times (threshold: {constants.RESTART_THRESHOLD}).")
            reasoning.append("Frequent restarts indicate a crash loop, OOMKill, or liveness probe failure.")
            candidates.append(CandidateCause(cause=RootCauseType.APPLICATION_BUG, confidence=65))
            candidates.append(CandidateCause(cause=RootCauseType.CPU_LIMIT_REACHED, confidence=50))

        # ── Rule 4: Insufficient Replicas ───────────────────────────────────
        elif cpu > constants.CPU_REPLICA_THRESHOLD and replicas == constants.REPLICA_MIN_COUNT:
            root_cause = RootCauseType.INSUFFICIENT_REPLICAS
            confidence = 80
            evidence.append(f"CPU is {cpu}% with only {replicas} replica running.")
            reasoning.append("High CPU concentrated on a single replica suggests under-provisioning.")
            candidates.append(CandidateCause(cause=RootCauseType.WORKLOAD_SPIKE, confidence=55))
            candidates.append(CandidateCause(cause=RootCauseType.CPU_LIMIT_REACHED, confidence=45))

        # ── Rule 5: Sustained High CPU ──────────────────────────────────────
        elif (cpu >= constants.SUSTAINED_CURRENT_MIN and
              avg5 >= constants.SUSTAINED_5M_MIN and
              avg15 >= constants.SUSTAINED_15M_MIN):
            root_cause = RootCauseType.RESOURCE_REQUEST_TOO_LOW
            confidence = 75
            evidence.append(
                f"CPU sustained above 85%: current={cpu}%, 5m={avg5}%, 15m={avg15}%."
            )
            reasoning.append("Sustained high CPU across all time windows suggests under-provisioned resources.")
            candidates.append(CandidateCause(cause=RootCauseType.APPLICATION_BUG, confidence=55))
            candidates.append(CandidateCause(cause=RootCauseType.CPU_LIMIT_REACHED, confidence=50))

        else:
            root_cause = RootCauseType.UNKNOWN
            confidence = 20
            evidence.append(f"CPU={cpu}%, 5m={avg5}%, restarts={restarts}, replicas={replicas}.")
            reasoning.append("No deterministic rule matched the current metric pattern.")
            candidates.append(CandidateCause(cause=RootCauseType.APPLICATION_BUG, confidence=25))

        rc_logger.log_fallback_triggered(
            f"rule matched: {root_cause.value} (confidence={confidence})"
        )
        rc_logger.log_parsed_output(root_cause.value, confidence, RootCauseSource.FALLBACK.value)

        return RootCauseOutputState(
            root_cause=root_cause,
            confidence=confidence,
            evidence=evidence,
            reasoning=reasoning,
            possible_causes=candidates,
            source=RootCauseSource.FALLBACK,
            model_name="fallback",
            execution_time_ms=0,
            timestamp=datetime.now(timezone.utc),
        )
