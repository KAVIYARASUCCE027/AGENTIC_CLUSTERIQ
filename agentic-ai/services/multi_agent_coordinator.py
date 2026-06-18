"""
Multi-Agent Coordinator — Phase 10.
"""
import time
import logging
from typing import List, Optional

from schemas.cpu_state import CPUState
from schemas.coordinator.agent_execution_state import AgentExecutionState, AgentStatus
from services.agent_registry import AgentRegistry
from utils.metrics import (
    agent_execution_seconds,
    agent_failures_total,
    agent_retry_total,
    agent_tokens_total
)
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MultiAgentCoordinator:
    """
    Central orchestration layer.
    Executes agents while enforcing shared state management, metric tracking,
    and failure recovery.
    """
    
    # Singleton pattern so we don't recreate the registry constantly
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MultiAgentCoordinator, cls).__new__(cls)
            cls._instance._registry = AgentRegistry()
        return cls._instance

    def execute_agent(self, agent_name: str, state: CPUState) -> CPUState:
        """
        Executes a specific agent by name, tracking all metrics and handling failures.
        Called by the thin LangGraph nodes.
        """
        exec_state = AgentExecutionState(agent_name=agent_name, status=AgentStatus.RUNNING)
        exec_state.start_time = datetime.now(timezone.utc)
        
        start_t = time.perf_counter()
        
        try:
            agent = self._registry.get_agent(agent_name)
            
            # Execute
            logger.info(f"Coordinator invoking agent: {agent_name}")
            new_state = agent.execute(state)
            
            # Validate
            if not agent.validate(new_state):
                raise ValueError(f"Agent {agent_name} failed validation.")
            
            exec_state.status = AgentStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {str(e)}", exc_info=True)
            agent_failures_total.labels(agent_name=agent_name).inc()
            
            exec_state.status = AgentStatus.FAILED
            exec_state.error_message = str(e)
            
            # Fallback/Rollback mechanism: If an agent fails, we don't crash the graph.
            # We return the original state (effectively skipping the agent's mutation).
            try:
                agent = self._registry.get_agent(agent_name)
                new_state = agent.rollback(state)
            except Exception as rollback_e:
                logger.error(f"Rollback failed for {agent_name}: {rollback_e}")
                new_state = state # strict fallback
            
        finally:
            end_t = time.perf_counter()
            duration_s = end_t - start_t
            exec_state.end_time = datetime.now(timezone.utc)
            exec_state.duration_ms = int(duration_s * 1000)
            
            # Record prometheus metrics
            agent_execution_seconds.labels(agent_name=agent_name).observe(duration_s)
            
            # Extract token usage from new state (if applicable - rough estimate or tracking)
            # Future enhancement: dynamically extract token_usage from the state metadata if present
            # agent_tokens_total.labels(agent_name=agent_name).inc(...)
            
            # For now, we print it to logger for visibility
            logger.info(f"Coordinator finished {agent_name} | status={exec_state.status.value} | time={exec_state.duration_ms}ms")
            
        return new_state

