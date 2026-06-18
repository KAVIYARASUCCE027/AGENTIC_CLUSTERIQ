"""
Fallback Recommendation Service — Phase 7.

Provides deterministic rule-based recommendations when:
  - Gemini API is unavailable or fails all retries
  - Gemini returns confidence < 60
  - Invalid response received

Rules are keyed on RootCauseType from Phase 6 output.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from enums.recommendation_type import RecommendationType
from enums.recommendation_source import RecommendationSource
from enums.confidence_level import ConfidenceLevel
from enums.root_cause_type import RootCauseType
from schemas.recommendation_input import RecommendationInputSchema
from schemas.recommendation_output import RecommendationOutputState, CandidateRecommendation
from utils.recommendation_logger import RecommendationLogger

logger = logging.getLogger(__name__)
rec_logger = RecommendationLogger("services.fallback_recommendation_service")

# Deterministic rule mapping: root_cause → (primary_recs, candidates, confidence, reasoning)
_RULES: dict[RootCauseType, dict] = {
    RootCauseType.CPU_LIMIT_REACHED: {
        "recommendations": [RecommendationType.INCREASE_CPU_LIMIT, RecommendationType.ENABLE_HPA],
        "reasoning": [
            "CPU usage is at or near the configured limit causing throttling.",
            "Increasing the CPU limit will allow the pod to burst beyond its current ceiling.",
            "Enabling HPA will distribute load across replicas automatically.",
        ],
        "confidence": 88,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.INCREASE_CPU_REQUEST, confidence=70, priority="MEDIUM", description="Align request with actual usage pattern."),
            CandidateRecommendation(recommendation=RecommendationType.REVIEW_DEPLOYMENT, confidence=60, priority="LOW", description="Review resource configuration against workload profile."),
        ],
    },
    RootCauseType.INSUFFICIENT_REPLICAS: {
        "recommendations": [RecommendationType.SCALE_UP_REPLICAS, RecommendationType.ENABLE_HPA],
        "reasoning": [
            "CPU load is concentrated on too few replicas.",
            "Scaling up replicas will distribute traffic and reduce per-pod CPU load.",
            "HPA will automate future scaling based on CPU thresholds.",
        ],
        "confidence": 85,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.INCREASE_CPU_LIMIT, confidence=65, priority="MEDIUM", description="Temporary relief while scaling is applied."),
        ],
    },
    RootCauseType.POD_RESTARTING: {
        "recommendations": [RecommendationType.INVESTIGATE_APPLICATION, RecommendationType.RESTART_POD],
        "reasoning": [
            "Frequent restarts indicate a crash loop, OOMKill, or liveness probe failure.",
            "Investigate previous pod logs to identify the crash reason.",
            "Restarting the pod may temporarily restore service while root cause is investigated.",
        ],
        "confidence": 82,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.REVIEW_DEPLOYMENT, confidence=65, priority="MEDIUM", description="Check resource limits and probe configuration."),
        ],
    },
    RootCauseType.WORKLOAD_SPIKE: {
        "recommendations": [RecommendationType.ENABLE_HPA, RecommendationType.SCALE_UP_REPLICAS],
        "reasoning": [
            "Sudden CPU spike detected against a low baseline average.",
            "HPA will automatically scale replicas during future spikes.",
            "Scaling up manually now provides immediate relief.",
        ],
        "confidence": 83,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.INVESTIGATE_APPLICATION, confidence=55, priority="LOW", description="Check for background jobs or traffic bursts."),
        ],
    },
    RootCauseType.RESOURCE_REQUEST_TOO_LOW: {
        "recommendations": [RecommendationType.INCREASE_CPU_REQUEST, RecommendationType.REVIEW_DEPLOYMENT],
        "reasoning": [
            "Sustained CPU usage across all time windows indicates under-provisioned resource requests.",
            "Increasing CPU request ensures the scheduler places the pod on a node with sufficient capacity.",
        ],
        "confidence": 78,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.INCREASE_CPU_LIMIT, confidence=65, priority="MEDIUM", description="Increase both request and limit together."),
        ],
    },
    RootCauseType.NODE_RESOURCE_CONTENTION: {
        "recommendations": [RecommendationType.CHECK_NODE_UTILIZATION, RecommendationType.REVIEW_DEPLOYMENT],
        "reasoning": [
            "Possible noisy-neighbor effect from other workloads on the same node.",
            "Checking node utilization will confirm if the node is over-committed.",
            "Moving the pod to a less contended node may resolve the issue.",
        ],
        "confidence": 75,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.SCALE_UP_REPLICAS, confidence=50, priority="LOW", description="Spread pod across multiple nodes."),
        ],
    },
    RootCauseType.APPLICATION_BUG: {
        "recommendations": [RecommendationType.INVESTIGATE_APPLICATION, RecommendationType.MONITOR_CLOSELY],
        "reasoning": [
            "Metrics suggest an application-level performance issue.",
            "Review code, thread pools, and external dependency calls.",
            "Monitor closely after any fix to confirm recovery.",
        ],
        "confidence": 72,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.RESTART_POD, confidence=50, priority="MEDIUM", description="Temporary relief if pod is in degraded state."),
        ],
    },
    RootCauseType.UNKNOWN: {
        "recommendations": [RecommendationType.MONITOR_CLOSELY, RecommendationType.REVIEW_DEPLOYMENT],
        "reasoning": [
            "Root cause could not be determined from available metrics.",
            "Monitor the pod closely and collect additional telemetry.",
        ],
        "confidence": 40,
        "candidates": [
            CandidateRecommendation(recommendation=RecommendationType.INVESTIGATE_APPLICATION, confidence=35, priority="LOW", description="Manual investigation recommended."),
        ],
    },
}


class FallbackRecommendationService:
    """
    Deterministic fallback recommendation service keyed on root cause.
    """

    def recommend(self, inp: RecommendationInputSchema) -> RecommendationOutputState:
        root_cause = inp.root_cause_output.root_cause
        rule = _RULES.get(root_cause, _RULES[RootCauseType.UNKNOWN])

        rec_logger.log_fallback_triggered(f"root_cause={root_cause.value}")
        rec_logger.log_parsed_output(
            [r.value for r in rule["recommendations"]],
            rule["confidence"],
            RecommendationSource.FALLBACK.value
        )

        return RecommendationOutputState(
            recommendations=rule["recommendations"],
            reasoning=rule["reasoning"],
            confidence=rule["confidence"],
            confidence_level=ConfidenceLevel.from_score(rule["confidence"]),
            source=RecommendationSource.FALLBACK,
            possible_recommendations=rule["candidates"],
            model_name="fallback",
            execution_time_ms=0,
            timestamp=datetime.now(timezone.utc),
        )
