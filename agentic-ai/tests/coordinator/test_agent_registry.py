"""
Tests for AgentRegistry.
"""
import pytest
import os
from services.agent_registry import AgentRegistry
from agents.analyzer_agent import AnalyzerAgent

@pytest.fixture(autouse=True)
def setup_test_db():
    os.environ["TESTING"] = "true"
    yield
    os.environ.pop("TESTING", None)

class TestAgentRegistry:
    def test_registry_initialization(self):
        registry = AgentRegistry()
        agents = registry.list_agents()
        assert "analyzer" in agents
        assert "root_cause" in agents
        assert "recommendation" in agents
        assert "action_planner" in agents
        assert "memory" in agents

    def test_get_agent(self):
        registry = AgentRegistry()
        agent = registry.get_agent("analyzer")
        assert isinstance(agent, AnalyzerAgent)
        assert agent.name == "analyzer"

    def test_get_missing_agent(self):
        registry = AgentRegistry()
        with pytest.raises(ValueError):
            registry.get_agent("non_existent_agent")
