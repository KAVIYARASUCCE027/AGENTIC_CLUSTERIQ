"""
Tests for RecommendationPromptBuilder.
Validates metric and context injection without calling Gemini.
"""
import pytest
from datetime import datetime, timezone

from schemas.recommendation_input import (
    RecommendationInputSchema, MetricsSnapshot, AnalyzerSummary, RootCauseSummary
)
from schemas.analyzer_output import HealthStatus, Severity, AbnormalityType
from enums.root_cause_type import RootCauseType
from prompts.recommendation_prompt_builder import RecommendationPromptBuilder


def _make_input(**overrides) -> RecommendationInputSchema:
    defaults = dict(
        pod_name="api-server-xyz",
        namespace="production",
        timestamp=datetime.now(timezone.utc),
        metrics=MetricsSnapshot(
            cpu_usage=95.0, avg_cpu_5m=91.0, avg_cpu_15m=88.0,
            cpu_trend="INCREASING", cpu_limit=1000.0, cpu_request=500.0,
            restart_count=2, replica_count=1, throttling_percentage=18.5,
        ),
        analyzer_output=AnalyzerSummary(
            health_status=HealthStatus.CRITICAL, severity=Severity.CRITICAL,
            abnormality=AbnormalityType.SUSTAINED_HIGH_CPU,
            trend="INCREASING", confidence=88,
            reasoning=["CPU above 90% for 15m"], recommendations=["Scale up"],
        ),
        root_cause_output=RootCauseSummary(
            root_cause=RootCauseType.CPU_LIMIT_REACHED, confidence=90,
            evidence=["CPU at 95%, limit is 1000m"], reasoning=["Throttling detected"],
            source="GEMINI",
        ),
    )
    defaults.update(overrides)
    return RecommendationInputSchema(**defaults)


class TestRecommendationPromptBuilder:

    def test_build_returns_two_strings(self):
        builder = RecommendationPromptBuilder()
        system, user = builder.build(_make_input())
        assert isinstance(system, str) and len(system) > 0
        assert isinstance(user, str) and len(user) > 0

    def test_pod_name_injected(self):
        builder = RecommendationPromptBuilder()
        _, user = builder.build(_make_input())
        assert "api-server-xyz" in user

    def test_root_cause_injected(self):
        builder = RecommendationPromptBuilder()
        _, user = builder.build(_make_input())
        assert "CPU_LIMIT_REACHED" in user

    def test_cpu_usage_injected(self):
        builder = RecommendationPromptBuilder()
        _, user = builder.build(_make_input())
        assert "95.0" in user

    def test_system_prompt_has_allowed_list(self):
        builder = RecommendationPromptBuilder()
        system, _ = builder.build(_make_input())
        assert "SCALE_UP_REPLICAS" in system
        assert "ENABLE_HPA" in system

    def test_evidence_injected(self):
        builder = RecommendationPromptBuilder()
        _, user = builder.build(_make_input())
        assert "CPU at 95%" in user
