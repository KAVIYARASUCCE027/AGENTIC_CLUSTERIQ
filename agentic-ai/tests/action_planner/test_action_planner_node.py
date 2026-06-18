"""
Tests for action_planner_node.
Mocks GeminiActionPlannerService to avoid real API calls.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import AnalyzerOutputState, HealthStatus, Severity, AbnormalityType
from schemas.root_cause_output import RootCauseOutputState
from schemas.recommendation_output import RecommendationOutputState
from schemas.action_plan_output import ActionPlanOutputState, ActionStep
from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource
from enums.recommendation_type import RecommendationType
from enums.recommendation_source import RecommendationSource
from enums.action_type import ActionType
from enums.action_source import ActionSource
from enums.action_priority import ActionPriority
from enums.action_risk import ActionRisk
from nodes.cpu.action_planner_node import action_planner_node


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
        recommendation_output=RecommendationOutputState(
            recommendations=[RecommendationType.INCREASE_CPU_LIMIT],
            reasoning=["CPU at limit"],
            confidence=85,
            source=RecommendationSource.GEMINI,
        )
    )


def _gemini_output(confidence=85) -> ActionPlanOutputState:
    return ActionPlanOutputState(
        actions=[
            ActionStep(
                step=1,
                action="Patch CPU Limit",
                action_type=ActionType.PATCH_DEPLOYMENT,
                risk=ActionRisk.MEDIUM,
                estimated_duration="2m",
            )
        ],
        priority=ActionPriority.HIGH,
        risk=ActionRisk.MEDIUM,
        estimated_duration="2m",
        rollback_strategy="Revert patch",
        confidence=confidence,
        source=ActionSource.GEMINI,
        model_name="gemini-2.5-flash",
        execution_time_ms=300,
        timestamp=datetime.now(timezone.utc),
    )


class TestActionPlannerNode:

    def test_uses_gemini_when_high_confidence(self):
        with patch("nodes.cpu.action_planner_node.GeminiActionPlannerService") as MockGemini:
            mock_service = MagicMock()
            mock_service.plan_action.return_value = _gemini_output(confidence=85)
            MockGemini.return_value = mock_service

            result = action_planner_node(_make_state())
            assert result.action_plan_output.source == ActionSource.GEMINI
            assert len(result.action_plan_output.actions) == 1
            assert "action_planner" in result.metadata.visited_nodes

    def test_falls_back_when_gemini_low_confidence(self):
        with patch("nodes.cpu.action_planner_node.GeminiActionPlannerService") as MockGemini:
            mock_service = MagicMock()
            mock_service.plan_action.return_value = _gemini_output(confidence=30)
            MockGemini.return_value = mock_service

            result = action_planner_node(_make_state())
            assert result.action_plan_output.source == ActionSource.FALLBACK

    def test_falls_back_when_gemini_raises(self):
        with patch("nodes.cpu.action_planner_node.GeminiActionPlannerService") as MockGemini:
            MockGemini.side_effect = RuntimeError("No API key")

            result = action_planner_node(_make_state())
            assert result.action_plan_output.source == ActionSource.FALLBACK
            assert len(result.action_plan_output.actions) > 0

    def test_action_plan_output_populated(self):
        with patch("nodes.cpu.action_planner_node.GeminiActionPlannerService") as MockGemini:
            mock_service = MagicMock()
            mock_service.plan_action.return_value = _gemini_output(confidence=88)
            MockGemini.return_value = mock_service

            result = action_planner_node(_make_state())
            assert result.action_plan_output is not None
            assert result.action_plan_output.confidence > 0
            assert result.action_plan_output.rollback_strategy is not None
