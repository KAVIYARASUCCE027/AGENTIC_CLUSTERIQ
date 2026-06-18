import pytest
from schemas.cpu_state import CPUState, MetricState, InputState
from services.rules.replica_rule import ReplicaRule

def test_replica_rule():
    state = CPUState(
        inputs=InputState(pod_name="test", namespace="test"), 
        metrics=MetricState(cpu_usage=90.0, replica_count=1)
    )
    rule = ReplicaRule()
    result = rule.evaluate(state)
    assert result.root_cause == "INSUFFICIENT_REPLICAS"
