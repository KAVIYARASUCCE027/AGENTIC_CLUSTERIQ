"""
Tests for ActionPlannerPromptBuilder.
Validates metric and context injection without calling Gemini.
"""
import pytest
from datetime import datetime, timezone

from schemas.action_plan_input import (
    ActionPlanInputSchema, MetricsSnapshot, AnalyzerSummary, RootCauseSummary, RecommendationSummary
)
from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType
from enums.root_cause_type import RootCauseType
from enums.recommendation_type import RecommendationType
from prompts.action_planner_prompt_builder import ActionPlannerPromptBuilder


def _make_input() -> ActionPlanInputSchema:
    return ActionPlanInputSchema(
        pod_name="redis-pod",
        namespace="db-ns",
        timestamp=datetime.now(timezone.utc),
        metrics=MetricsSnapshot(
            cpu_usage=99.0, avg_cpu_5m=98.0, avg_cpu_15m=97.0,
            cpu_trend="STABLE", cpu_limit=2000.0, cpu_request=1000.0,
            restart_count=0, replica_count=1, throttling_percentage=55.0,
        ),
        analyzer_output=AnalyzerSummary(
            health_status=HealthStatus.CRITICAL, severity=Severity.CRITICAL,
            abnormality=AbnormalityType.SUSTAINED_HIGH_CPU,
            trend="STABLE", confidence=95,
            reasoning=["CPU is maxed out"], recommendations=[],
        ),
        root_cause_output=RootCauseSummary(
            root_cause=RootCauseType.CPU_LIMIT_REACHED, confidence=90,
            evidence=["Throttling at 55%"], reasoning=["Limit is too low for current workload"],
            source="GEMINI",
        ),
        recommendation_output=RecommendationSummary(
            recommendations=[RecommendationType.INCREASE_CPU_LIMIT, RecommendationType.ENABLE_HPA],
            reasoning=["Needs more CPU", "Needs horizontal scaling"],
            confidence=85,
        )
    )


class TestActionPlannerPromptBuilder:

    def test_build_returns_two_strings(self):
        builder = ActionPlannerPromptBuilder()
        system, user = builder.build(_make_input())
        assert isinstance(system, str) and len(system) > 0
        assert isinstance(user, str) and len(user) > 0

    def test_pod_name_injected(self):
        builder = ActionPlannerPromptBuilder()
        _, user = builder.build(_make_input())
        assert "redis-pod" in user

    def test_recommendations_injected(self):
        builder = ActionPlannerPromptBuilder()
        _, user = builder.build(_make_input())
        assert "INCREASE_CPU_LIMIT" in user
        assert "ENABLE_HPA" in user

    def test_root_cause_injected(self):
        builder = ActionPlannerPromptBuilder()
        _, user = builder.build(_make_input())
        assert "CPU_LIMIT_REACHED" in user

    def test_system_prompt_has_allowed_actions(self):
        builder = ActionPlannerPromptBuilder()
        system, _ = builder.build(_make_input())
        assert "PATCH_DEPLOYMENT" in system
        assert "KUBECTL_COMMAND" in system
