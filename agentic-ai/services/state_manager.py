"""
State Manager — Phase 10.
"""
import logging
from schemas.cpu_state import CPUState

logger = logging.getLogger(__name__)

class StateManager:
    """
    Maintains CPUState and ensures safe, immutable transitions.
    """
    def __init__(self, initial_state: CPUState):
        # We store a copy to prevent accidental mutations by reference
        self._current_state = initial_state.model_copy(deep=True)

    def get_state(self) -> CPUState:
        """Retrieve the current state safely."""
        return self._current_state.model_copy(deep=True)

    def update_state(self, new_state: CPUState) -> None:
        """
        Safely transition to a new state.
        Validates the new state before accepting the mutation.
        """
        # A deeper validation layer could be added here, e.g., checking if 
        # execution_id drifted, etc.
        if new_state.metadata.execution_id != self._current_state.metadata.execution_id:
            raise ValueError("State corruption detected: execution_id mismatch during state merge.")
            
        self._current_state = new_state.model_copy(deep=True)
        logger.debug(f"State safely updated. Current node: {self._current_state.metadata.current_node}")

    def merge_output(self, node_name: str, output_state: CPUState) -> None:
        """
        Syntactic sugar to mark node completed while updating state.
        """
        final_state = output_state.mark_node_completed(node_name)
        self.update_state(final_state)
