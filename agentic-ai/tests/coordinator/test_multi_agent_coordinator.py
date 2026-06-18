"""
Tests for MultiAgentCoordinator.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from schemas.cpu_state import CPUState, InputState
from services.multi_agent_coordinator import MultiAgentCoordinator

@pytest.fixture(autouse=True)
def setup_test_db():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)

def _make_state():
    return CPUState(inputs=InputState(pod_name="api-pod", namespace="prod"))

class TestMultiAgentCoordinator:
    
    @patch("services.multi_agent_coordinator.AgentRegistry")
    def test_execute_agent_success(self, MockRegistry):
        state = _make_state()
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.validate.return_value = True
        
        # Mutate state slightly
        mutated_state = state.model_copy(deep=True)
        mutated_state.inputs.pod_name = "mutated-pod"
        mock_agent.execute.return_value = mutated_state
        
        MockRegistry.return_value.get_agent.return_value = mock_agent
        
        coordinator = MultiAgentCoordinator()
        # Force re-inject the mocked registry because it's a singleton
        coordinator._registry = MockRegistry.return_value
        
        result_state = coordinator.execute_agent("test_agent", state)
        
        mock_agent.execute.assert_called_once_with(state)
        mock_agent.validate.assert_called_once_with(mutated_state)
        assert result_state.inputs.pod_name == "mutated-pod"

    @patch("services.multi_agent_coordinator.AgentRegistry")
    def test_execute_agent_failure_fallback(self, MockRegistry):
        state = _make_state()
        mock_agent = MagicMock()
        mock_agent.name = "test_agent"
        mock_agent.execute.side_effect = Exception("Agent crashed!")
        mock_agent.rollback.return_value = state # Mock successful rollback returning original state
        
        MockRegistry.return_value.get_agent.return_value = mock_agent
        
        coordinator = MultiAgentCoordinator()
        coordinator._registry = MockRegistry.return_value
        
        # Should not raise exception
        result_state = coordinator.execute_agent("test_agent", state)
        
        mock_agent.execute.assert_called_once()
        mock_agent.rollback.assert_called_once_with(state)
        # Should return the original state
        assert result_state.inputs.pod_name == "api-pod"
