"""
Tests for root_cause_node.
Mocks GeminiRootCauseService to avoid real API calls.
Validates fallback activation, state transitions, and output population.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import AnalyzerOutputState, HealthStatus, Severity, AbnormalityType
from schemas.root_cause_output import RootCauseOutputState, CandidateCause
from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource
from nodes.cpu.root_cause_node import root_cause_node


def _make_state(cpu=95.0, avg5=40.0, restarts=0, replicas=1) -> CPUState:
    return CPUState(
        inputs=InputState(pod_name="test-pod", namespace="test-ns"),
        metrics=MetricState(
            cpu_usage=cpu,
            avg_cpu_last_5m=avg5,
            avg_cpu_last_15m=avg5 - 5,
            restart_count=restarts,
            replica_count=replicas,
        ),
        analyzer_output=AnalyzerOutputState(
            health_status=HealthStatus.CRITICAL,
            severity=Severity.CRITICAL,
            abnormality=AbnormalityType.CPU_SPIKE,
            reasoning=["CPU is above 90%"],
            confidence=80,
        ),
    )


def _gemini_output(confidence=90, root_cause=RootCauseType.WORKLOAD_SPIKE) -> RootCauseOutputState:
    return RootCauseOutputState(
        root_cause=root_cause,
        confidence=confidence,
        evidence=["CPU is 95%, 5m avg is 40%"],
        reasoning=["Sudden spike with low baseline"],
        possible_causes=[CandidateCause(cause=RootCauseType.APPLICATION_BUG, confidence=40)],
        source=RootCauseSource.GEMINI,
        model_name="gemini-2.5-flash",
        execution_time_ms=250,
        timestamp=datetime.now(timezone.utc),
    )


class TestRootCauseNode:

    def test_uses_gemini_when_high_confidence(self):
        """When Gemini returns high confidence, it should be used."""
        with patch("nodes.cpu.root_cause_node.GeminiRootCauseService") as MockGemini:
            mock_service = MagicMock()
            mock_service.analyze.return_value = _gemini_output(confidence=90)
            MockGemini.return_value = mock_service

            state = _make_state()
            result = root_cause_node(state)

            assert result.root_cause_output.source == RootCauseSource.GEMINI
            assert result.root_cause_output.root_cause == RootCauseType.WORKLOAD_SPIKE
            assert "root_cause" in result.metadata.visited_nodes

    def test_falls_back_when_gemini_low_confidence(self):
        """When Gemini returns confidence < 60, fallback should be used."""
        with patch("nodes.cpu.root_cause_node.GeminiRootCauseService") as MockGemini:
            mock_service = MagicMock()
            mock_service.analyze.return_value = _gemini_output(confidence=30, root_cause=RootCauseType.UNKNOWN)
            MockGemini.return_value = mock_service

            state = _make_state(cpu=95.0, avg5=40.0)
            result = root_cause_node(state)

            assert result.root_cause_output.source == RootCauseSource.FALLBACK

    def test_falls_back_when_gemini_raises(self):
        """When Gemini raises an exception, fallback should run."""
        with patch("nodes.cpu.root_cause_node.GeminiRootCauseService") as MockGemini:
            MockGemini.side_effect = RuntimeError("API key not set")

            state = _make_state(cpu=95.0, avg5=40.0)
            result = root_cause_node(state)

            assert result.root_cause_output.source == RootCauseSource.FALLBACK
            assert result.root_cause_output.root_cause == RootCauseType.WORKLOAD_SPIKE

    def test_state_has_root_cause_output(self):
        """root_cause_output should be populated after node execution."""
        with patch("nodes.cpu.root_cause_node.GeminiRootCauseService") as MockGemini:
            mock_service = MagicMock()
            mock_service.analyze.return_value = _gemini_output(confidence=85)
            MockGemini.return_value = mock_service

            state = _make_state()
            result = root_cause_node(state)

            assert result.root_cause_output is not None
            assert result.root_cause_output.confidence > 0
            assert len(result.root_cause_output.evidence) > 0
