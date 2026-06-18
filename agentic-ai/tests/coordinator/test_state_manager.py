"""
Tests for StateManager.
"""
import pytest
from schemas.cpu_state import CPUState, InputState
from services.state_manager import StateManager

def _make_state():
    return CPUState(inputs=InputState(pod_name="api-pod", namespace="prod"))

class TestStateManager:
    def test_state_manager_initialization(self):
        state = _make_state()
        manager = StateManager(state)
        
        retrieved = manager.get_state()
        assert retrieved is not state  # Should be a deep copy
        assert retrieved.inputs.pod_name == "api-pod"

    def test_safe_update(self):
        state = _make_state()
        manager = StateManager(state)
        
        new_state = state.model_copy(update={"inputs": InputState(pod_name="changed", namespace="prod")})
        manager.update_state(new_state)
        
        assert manager.get_state().inputs.pod_name == "changed"

    def test_corruption_prevention(self):
        state = _make_state()
        manager = StateManager(state)
        
        # Corrupt execution ID
        new_metadata = state.metadata.model_copy(update={"execution_id": "malicious-id"})
        new_state = state.model_copy(update={"metadata": new_metadata})
        
        with pytest.raises(ValueError, match="State corruption detected"):
            manager.update_state(new_state)
