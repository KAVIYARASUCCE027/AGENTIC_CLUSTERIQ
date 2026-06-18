"""
Tests for FallbackRootCauseService.
No Gemini API calls — purely deterministic rule validation.
"""
import pytest
from schemas.root_cause_input import (
    RootCauseInputSchema, CPUMetricsInput, RestartMetricsInput, ReplicaMetricsInput
)
from schemas.analyzer_output import Severity, AbnormalityType
from enums.root_cause_type import RootCauseType
from enums.root_cause_source import RootCauseSource
from services.fallback_root_cause_service import FallbackRootCauseService


def _make_input(cpu=40.0, avg5=38.0, avg15=36.0, restarts=0, replicas=3, limit=0.0) -> RootCauseInputSchema:
    return RootCauseInputSchema(
        pod_name="test-pod",
        namespace="test-ns",
        severity=Severity.LOW,
        abnormality=AbnormalityType.NONE,
        analyzer_reasoning=[],
        cpu_metrics=CPUMetricsInput(
            current_cpu_usage=cpu, avg_cpu_5m=avg5, avg_cpu_15m=avg15,
            cpu_trend="STABLE", throttling_percentage=0.0,
            cpu_limit=limit, cpu_request=200.0,
        ),
        restart_metrics=RestartMetricsInput(restart_count=restarts),
        replica_metrics=ReplicaMetricsInput(current_replicas=replicas),
    )


@pytest.fixture
def service():
    return FallbackRootCauseService()


class TestFallbackRootCauseService:

    def test_source_is_always_fallback(self, service):
        result = service.analyze(_make_input())
        assert result.source == RootCauseSource.FALLBACK

    def test_detects_workload_spike(self, service):
        inp = _make_input(cpu=95.0, avg5=40.0)
        result = service.analyze(inp)
        assert result.root_cause == RootCauseType.WORKLOAD_SPIKE
        assert result.confidence >= 80

    def test_detects_cpu_limit_reached(self, service):
        inp = _make_input(cpu=95.0, avg5=91.0, limit=1000.0)
        result = service.analyze(inp)
        assert result.root_cause == RootCauseType.CPU_LIMIT_REACHED

    def test_detects_pod_restarting(self, service):
        inp = _make_input(cpu=85.0, avg5=82.0, restarts=5)
        result = service.analyze(inp)
        assert result.root_cause == RootCauseType.POD_RESTARTING
        assert result.confidence >= 75

    def test_detects_insufficient_replicas(self, service):
        inp = _make_input(cpu=90.0, avg5=88.0, restarts=1, replicas=1)
        result = service.analyze(inp)
        assert result.root_cause == RootCauseType.INSUFFICIENT_REPLICAS

    def test_unknown_for_normal_metrics(self, service):
        inp = _make_input(cpu=40.0, avg5=38.0, restarts=0, replicas=3)
        result = service.analyze(inp)
        assert result.root_cause == RootCauseType.UNKNOWN

    def test_evidence_is_non_empty(self, service):
        inp = _make_input(cpu=95.0, avg5=40.0)
        result = service.analyze(inp)
        assert len(result.evidence) > 0

    def test_possible_causes_populated(self, service):
        inp = _make_input(cpu=95.0, avg5=40.0)
        result = service.analyze(inp)
        assert len(result.possible_causes) > 0
