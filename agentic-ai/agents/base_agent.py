"""
Base Agent Interface — Phase 10.
"""
from abc import ABC, abstractmethod
from schemas.cpu_state import CPUState

class BaseAgent(ABC):
    """
    Interface for all AI Agents in the Multi-Agent Coordinator architecture.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique name of the agent."""
        pass

    @abstractmethod
    def execute(self, state: CPUState) -> CPUState:
        """
        Execute the agent's core logic.
        Must return a mutated or new CPUState.
        """
        pass

    def validate(self, state: CPUState) -> bool:
        """
        Validate whether the output state is well-formed.
        Defaults to returning True. Can be overridden.
        """
        return True

    def rollback(self, state: CPUState) -> CPUState:
        """
        Optional rollback logic if the agent fails or its changes
        need to be undone to maintain consistency.
        Defaults to returning the original state unchanged.
        """
        return state
