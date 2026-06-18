"""
Tests for recommendation_node.
Mocks GeminiRecommendationService to avoid real API calls.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import AnalyzerOutputState, HealthStatus, Severity, AbnormalityType
from schemas.root_cause_output import RootCauseOutputState, CandidateCause
from schemas.recommendation_output import RecommendationOutputState, CandidateRecommendation
from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource
from enums.recommendation_type import RecommendationType
from enums.recommendation_source import RecommendationSource
from enums.confidence_level import ConfidenceLevel
from nodes.cpu.recommendation_node import recommendation_node


def _make_state() -> CPUState:
    return CPUState(
        inputs=InputState(pod_name="api-pod", namespace="prod"),
        metrics=MetricState(cpu_usage=93.0, avg_cpu_last_5m=90.0, restart_count=1, replica_count=1),
        analyzer_output=AnalyzerOutputState(
            health_status=HealthStatus.CRITICAL,
            severity=Severity.CRITICAL,
            abnormality=AbnormalityType.SUSTAINED_HIGH_CPU,
            reasoning=["CPU above 90%"],
            confidence=88,
        ),
        root_cause_output=RootCauseOutputState(
            root_cause=RootCauseType.CPU_LIMIT_REACHED,
            confidence=90,
            evidence=["CPU at 93%"],
            reasoning=["Approaching configured limit"],
            source=RootCauseSource.GEMINI,
        ),
    )


def _gemini_output(confidence=85) -> RecommendationOutputState:
    return RecommendationOutputState(
        recommendations=[RecommendationType.INCREASE_CPU_LIMIT, RecommendationType.ENABLE_HPA],
        reasoning=["CPU at limit, need to increase allowance."],
        confidence=confidence,
        confidence_level=ConfidenceLevel.HIGH,
        source=RecommendationSource.GEMINI,
        model_name="gemini-2.5-flash",
        execution_time_ms=300,
        timestamp=datetime.now(timezone.utc),
    )


class TestRecommendationNode:

    def test_uses_gemini_when_high_confidence(self):
        with patch("nodes.cpu.recommendation_node.GeminiRecommendationService") as MockGemini:
            mock_service = MagicMock()
            mock_service.recommend.return_value = _gemini_output(confidence=85)
            MockGemini.return_value = mock_service

            result = recommendation_node(_make_state())
            assert result.recommendation_output.source == RecommendationSource.GEMINI
            assert RecommendationType.INCREASE_CPU_LIMIT in result.recommendation_output.recommendations
            assert "recommendation" in result.metadata.visited_nodes

    def test_falls_back_when_gemini_low_confidence(self):
        with patch("nodes.cpu.recommendation_node.GeminiRecommendationService") as MockGemini:
            mock_service = MagicMock()
            mock_service.recommend.return_value = _gemini_output(confidence=30)
            MockGemini.return_value = mock_service

            result = recommendation_node(_make_state())
            assert result.recommendation_output.source == RecommendationSource.FALLBACK

    def test_falls_back_when_gemini_raises(self):
        with patch("nodes.cpu.recommendation_node.GeminiRecommendationService") as MockGemini:
            MockGemini.side_effect = RuntimeError("No API key")

            result = recommendation_node(_make_state())
            assert result.recommendation_output.source == RecommendationSource.FALLBACK
            assert len(result.recommendation_output.recommendations) > 0

    def test_recommendation_output_populated(self):
        with patch("nodes.cpu.recommendation_node.GeminiRecommendationService") as MockGemini:
            mock_service = MagicMock()
            mock_service.recommend.return_value = _gemini_output(confidence=88)
            MockGemini.return_value = mock_service

            result = recommendation_node(_make_state())
            assert result.recommendation_output is not None
            assert result.recommendation_output.confidence > 0
            assert len(result.recommendation_output.reasoning) > 0
