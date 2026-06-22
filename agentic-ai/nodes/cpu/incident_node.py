import logging
from schemas.cpu_state import CPUState
from services.global_bus import agent_registry

logger = logging.getLogger(__name__)

def incident_node(state: CPUState) -> CPUState:
    """
    LangGraph node for grouping correlated events into incidents.
    Delegates to the IncidentAgent.
    """
    agent = agent_registry.get_agent("IncidentAgent")
    
    state = state.mark_running(agent.name)
    try:
        state = agent.execute(state)
        agent_registry.update_health(agent.name, response_time_ms=10) # rough estimate
        state = state.mark_node_completed(agent.name)
    except Exception as e:
        logger.error(f"IncidentAgent failed: {e}", exc_info=True)
        agent_registry.update_health(agent.name, has_error=True)
        state = state.mark_failed(str(e))
        
    return state
