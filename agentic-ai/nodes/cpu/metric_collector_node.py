import logging
import time

from schemas.cpu_state import CPUState
from services.cpu_metric_service import CPUMetricService
from services.exception_handler import AgentBaseException

logger = logging.getLogger(__name__)

def metric_collector(state: CPUState) -> CPUState:
    """
    LangGraph Node: Metric Collector.
    
    Responsible for fetching real metrics and populating CPUState.
    It delegates the complex collection and validation logic to the CPUMetricService.
    
    Args:
        state: The current execution state.
        
    Returns:
        The updated CPUState with populated metrics.
    """
    start_time = time.time()
    node_name = "metric_collector"
    
    # 1. Update metadata to RUNNING
    state = state.mark_running(node_name)
    
    pod_name = state.inputs.pod_name
    namespace = state.inputs.namespace
    execution_id = state.metadata.execution_id

    logger.info(
        "[%s] Node started: %s for pod %s/%s", 
        execution_id, node_name, namespace, pod_name
    )
    
    metric_service = CPUMetricService()
    
    try:
        # 2. Call CPUMetricService to do the heavy lifting
        updated_state = metric_service.collect_and_populate(state)
        
        # 3. Mark node completed
        final_state = updated_state.mark_node_completed(node_name)
        
        execution_time = time.time() - start_time
        logger.info(
            "[%s] Node completed successfully: %s in %.2fs | cpu_usage: %.2f%%, trend: %s",
            execution_id,
            node_name,
            execution_time,
            final_state.metrics.cpu_usage,
            final_state.metrics.cpu_trend.value
        )
        return final_state

    except AgentBaseException as e:
        # Expected domain exceptions
        execution_time = time.time() - start_time
        logger.error(
            "[%s] Node failed: %s in %.2fs | Error: %s",
            execution_id,
            node_name,
            execution_time,
            str(e)
        )
        return state.mark_failed(str(e))
        
    except Exception as e:
        # Unexpected exceptions
        execution_time = time.time() - start_time
        logger.error(
            "[%s] Node encountered unexpected failure: %s in %.2fs | Error: %s",
            execution_id,
            node_name,
            execution_time,
            str(e),
            exc_info=True
        )
        return state.mark_failed(f"Unexpected error in metric collection: {str(e)}")
