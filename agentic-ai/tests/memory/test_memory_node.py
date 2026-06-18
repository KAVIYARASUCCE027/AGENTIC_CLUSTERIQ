"""
Tests for Memory Node.
Ensures graph node properly falls back when the DB fails.
"""
import pytest
from unittest.mock import patch, MagicMock

from config.settings import get_settings
from schemas.cpu_state import CPUState, InputState, MetricState
from schemas.analyzer_output import AnalyzerOutputState, HealthStatus, Severity, AbnormalityType
from schemas.root_cause_output import RootCauseOutputState
from schemas.recommendation_output import RecommendationOutputState
from schemas.action_plan_output import ActionPlanOutputState
from enums.root_cause_type import RootCauseType
from enums.memory_source import MemorySource
from nodes.cpu.memory_node import memory_node


import os

@pytest.fixture(autouse=True)
def setup_test_db():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)


def _make_state() -> CPUState:
    return CPUState(
        inputs=InputState(pod_name="api-pod", namespace="prod"),
        metrics=MetricState(cpu_usage=90.0, avg_cpu_last_5m=85.0),
        analyzer_output=AnalyzerOutputState(
            health_status=HealthStatus.CRITICAL,
            severity=Severity.HIGH,
            abnormality=AbnormalityType.SUSTAINED_HIGH_CPU,
        ),
        root_cause_output=RootCauseOutputState(
            root_cause=RootCauseType.CPU_LIMIT_REACHED,
        ),
        recommendation_output=RecommendationOutputState(),
        action_plan_output=ActionPlanOutputState()
    )


class TestMemoryNode:

    @patch("nodes.cpu.memory_node.MemoryService")
    def test_memory_node_success(self, MockService):
        mock_svc = MockService.return_value
        mock_svc.retrieve_context.return_value = MagicMock(source=MemorySource.MONGODB, incident_count=2)
        mock_svc.save_incident.return_value = "incident-123"

        state = _make_state()
        result = memory_node(state)
        
        assert "memory" in result.metadata.visited_nodes
        assert result.memory_output.source == MemorySource.MONGODB
        assert result.memory_output.incident_count == 2

    @patch("nodes.cpu.memory_node.MemoryService")
    def test_memory_node_fallback_on_db_failure(self, MockService):
        mock_svc = MockService.return_value
        mock_svc.retrieve_context.side_effect = Exception("DB Connection refused")
        mock_svc.save_incident.side_effect = Exception("DB Connection refused")

        state = _make_state()
        result = memory_node(state)
        
        # Pipeline should NOT fail. It should degrade gracefully.
        assert result.metadata.status.value != "FAILED"
        assert result.memory_output.source == MemorySource.FALLBACK
        assert "memory" in result.metadata.visited_nodes
