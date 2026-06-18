"""
Tests for FallbackActionPlannerService.
No Gemini API calls — purely deterministic rule verification.
"""
import pytest
from datetime import datetime, timezone

from schemas.action_plan_input import (
    ActionPlanInputSchema, MetricsSnapshot, AnalyzerSummary, RootCauseSummary, RecommendationSummary
)
from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType
from enums.root_cause_type import RootCauseType
from enums.recommendation_type import RecommendationType
from enums.action_type import ActionType
from enums.action_source import ActionSource
from services.fallback_action_planner_service import FallbackActionPlannerService


def _make_input(recs) -> ActionPlanInputSchema:
    return ActionPlanInputSchema(
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
            root_cause=RootCauseType.CPU_LIMIT_REACHED, confidence=85,
            evidence=[], reasoning=[], source="FALLBACK",
        ),
        recommendation_output=RecommendationSummary(
            recommendations=recs,
            reasoning=["Test reasoning"],
            confidence=85,
        )
    )


@pytest.fixture
def service():
    return FallbackActionPlannerService()


class TestFallbackActionPlannerService:

    def test_source_is_always_fallback(self, service):
        result = service.plan_action(_make_input([RecommendationType.INCREASE_CPU_LIMIT]))
        assert result.source == ActionSource.FALLBACK

    def test_increase_cpu_limit_produces_patch(self, service):
        result = service.plan_action(_make_input([RecommendationType.INCREASE_CPU_LIMIT]))
        assert any(act.action_type == ActionType.PATCH_DEPLOYMENT for act in result.actions)
        assert result.confidence >= 80

    def test_scale_up_produces_kubectl(self, service):
        result = service.plan_action(_make_input([RecommendationType.SCALE_UP_REPLICAS]))
        assert any(act.action_type == ActionType.KUBECTL_COMMAND for act in result.actions)

    def test_investigate_produces_ticket(self, service):
        result = service.plan_action(_make_input([RecommendationType.INVESTIGATE_APPLICATION]))
        assert any(act.action_type == ActionType.CREATE_TICKET for act in result.actions)

    def test_unknown_gets_manual_investigation(self, service):
        result = service.plan_action(_make_input([RecommendationType.NO_ACTION_REQUIRED]))
        assert any(act.action_type == ActionType.MANUAL_INVESTIGATION for act in result.actions)

    def test_empty_recommendations_gets_manual_investigation(self, service):
        result = service.plan_action(_make_input([]))
        assert any(act.action_type == ActionType.MANUAL_INVESTIGATION for act in result.actions)

    def test_rollback_strategy_populated(self, service):
        result = service.plan_action(_make_input([RecommendationType.INCREASE_CPU_LIMIT]))
        assert result.rollback_strategy is not None
        assert len(result.rollback_strategy) > 0
