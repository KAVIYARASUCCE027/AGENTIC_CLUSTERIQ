"""
Tests for RootCausePromptBuilder.
Validates metric injection and prompt loading without calling Gemini.
"""
import pytest
from schemas.root_cause_input import (
    RootCauseInputSchema, CPUMetricsInput, RestartMetricsInput, ReplicaMetricsInput
)
from schemas.analyzer_output import Severity, AbnormalityType
from prompts.root_cause_prompt_builder import RootCausePromptBuilder


def _make_input(**kwargs) -> RootCauseInputSchema:
    defaults = dict(
        pod_name="nginx-abc",
        namespace="production",
        severity=Severity.CRITICAL,
        abnormality=AbnormalityType.CPU_SPIKE,
        analyzer_reasoning=["CPU is above 90%", "Trend is INCREASING"],
        cpu_metrics=CPUMetricsInput(
            current_cpu_usage=95.0,
            avg_cpu_5m=40.0,
            avg_cpu_15m=38.0,
            cpu_trend="INCREASING",
            throttling_percentage=12.5,
            cpu_limit=1000.0,
            cpu_request=500.0,
        ),
        restart_metrics=RestartMetricsInput(restart_count=2),
        replica_metrics=ReplicaMetricsInput(current_replicas=1),
    )
    defaults.update(kwargs)
    return RootCauseInputSchema(**defaults)


class TestRootCausePromptBuilder:

    def test_build_returns_two_strings(self):
        builder = RootCausePromptBuilder()
        inp = _make_input()
        system, user = builder.build(inp)
        assert isinstance(system, str)
        assert isinstance(user, str)
        assert len(system) > 0
        assert len(user) > 0

    def test_pod_name_injected(self):
        builder = RootCausePromptBuilder()
        inp = _make_input(pod_name="my-test-pod")
        _, user = builder.build(inp)
        assert "my-test-pod" in user

    def test_cpu_usage_injected(self):
        builder = RootCausePromptBuilder()
        inp = _make_input()
        _, user = builder.build(inp)
        assert "95.0" in user

    def test_reasoning_injected(self):
        builder = RootCausePromptBuilder()
        inp = _make_input()
        _, user = builder.build(inp)
        assert "CPU is above 90%" in user

    def test_system_prompt_contains_json_instruction(self):
        builder = RootCausePromptBuilder()
        inp = _make_input()
        system, _ = builder.build(inp)
        assert "JSON" in system
