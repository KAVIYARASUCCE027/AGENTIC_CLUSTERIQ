"""
Tests for FallbackRecommendationService.
No Gemini API calls — purely deterministic rule verification.
"""
import pytest
from datetime import datetime, timezone

from schemas.recommendation_input import (
    RecommendationInputSchema, MetricsSnapshot, AnalyzerSummary, RootCauseSummary
)
from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType
from enums.root_cause_type import RootCauseType
from enums.recommendation_type import RecommendationType
from enums.recommendation_source import RecommendationSource
from services.fallback_recommendation_service import FallbackRecommendationService


def _make_input(root_cause: RootCauseType) -> RecommendationInputSchema:
    return RecommendationInputSchema(
        pod_name="test-pod",
        namespace="test-ns",
        timestamp=datetime.now(timezone.utc),
        metrics=MetricsSnapshot(
            cpu_usage=90.0, avg_cpu_5m=88.0, avg_cpu_15m=85.0,
            cpu_trend="INCREASING", cpu_limit=1000.0, cpu_request=500.0,
            restart_count=2, replica_count=1,
        ),
        analyzer_output=AnalyzerSummary(
            health_status=HealthStatus.CRITICAL, severity=Severity.HIGH,
            abnormality=AbnormalityType.SUSTAINED_HIGH_CPU,
        ),
        root_cause_output=RootCauseSummary(
            root_cause=root_cause, confidence=85,
            evidence=["CPU at 90%"], reasoning=["Sustained load"],
            source="FALLBACK",
        ),
    )


@pytest.fixture
def service():
    return FallbackRecommendationService()


class TestFallbackRecommendationService:

    def test_source_is_always_fallback(self, service):
        result = service.recommend(_make_input(RootCauseType.CPU_LIMIT_REACHED))
        assert result.source == RecommendationSource.FALLBACK

    def test_cpu_limit_reached(self, service):
        result = service.recommend(_make_input(RootCauseType.CPU_LIMIT_REACHED))
        assert RecommendationType.INCREASE_CPU_LIMIT in result.recommendations
        assert RecommendationType.ENABLE_HPA in result.recommendations
        assert result.confidence >= 80

    def test_insufficient_replicas(self, service):
        result = service.recommend(_make_input(RootCauseType.INSUFFICIENT_REPLICAS))
        assert RecommendationType.SCALE_UP_REPLICAS in result.recommendations
        assert RecommendationType.ENABLE_HPA in result.recommendations

    def test_pod_restarting(self, service):
        result = service.recommend(_make_input(RootCauseType.POD_RESTARTING))
        assert RecommendationType.INVESTIGATE_APPLICATION in result.recommendations

    def test_workload_spike(self, service):
        result = service.recommend(_make_input(RootCauseType.WORKLOAD_SPIKE))
        assert RecommendationType.ENABLE_HPA in result.recommendations

    def test_unknown_gets_monitor_closely(self, service):
        result = service.recommend(_make_input(RootCauseType.UNKNOWN))
        assert RecommendationType.MONITOR_CLOSELY in result.recommendations

    def test_reasoning_non_empty(self, service):
        result = service.recommend(_make_input(RootCauseType.CPU_LIMIT_REACHED))
        assert len(result.reasoning) > 0

    def test_possible_recommendations_populated(self, service):
        result = service.recommend(_make_input(RootCauseType.CPU_LIMIT_REACHED))
        assert len(result.possible_recommendations) > 0

    def test_confidence_level_derived_correctly(self, service):
        result = service.recommend(_make_input(RootCauseType.CPU_LIMIT_REACHED))
        from enums.confidence_level import ConfidenceLevel
        assert result.confidence_level == ConfidenceLevel.from_score(result.confidence)
