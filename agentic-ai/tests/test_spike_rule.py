import pytest
from schemas.cpu_state import CPUState, MetricState, InputState
from schemas.analyzer_output import AbnormalityType
from services.rules.spike_rule import SpikeRule

def test_spike_rule_detected():
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"), 
        metrics=MetricState(cpu_usage=95.0, avg_cpu_last_5m=40.0)
    )
    rule = SpikeRule()
    result = rule.evaluate(state)
    assert result.abnormality == AbnormalityType.CPU_SPIKE
    assert len(result.reasoning) > 0
    assert result.confidence_score > 0

def test_spike_rule_not_detected():
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"), 
        metrics=MetricState(cpu_usage=95.0, avg_cpu_last_5m=90.0)
    )
    rule = SpikeRule()
    result = rule.evaluate(state)
    assert result.abnormality is None
