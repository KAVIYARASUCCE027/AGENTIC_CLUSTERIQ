import sys
from pathlib import Path

# Add project root to path so we can import modules
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
from pprint import pprint

from schemas.cpu_state import CPUState, InputState, ExecutionStatus
from graph.cpu_graph import build_cpu_graph

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_metric_collector")

def main():
    logger.info("Starting Metric Collector Node test...")
    
    # 1. Create Initial State
    initial_input = InputState(
        pod_name="prometheus-grafana-7f45d45-s5g9t",
        namespace="monitoring"
    )
    initial_state = CPUState(inputs=initial_input)
    
    # 2. Build and compile graph
    graph = build_cpu_graph()
    
    # 3. Execute graph
    logger.info("Executing graph with initial state...")
    try:
        # LangGraph invoke returns the final state (or a dictionary depending on version)
        result = graph.invoke(initial_state)
        
        # If it returns a dict, we might need to cast it or just print it.
        # StateGraph with Pydantic often returns a dict representing the state.
        if isinstance(result, dict):
            final_state = CPUState(**result)
        else:
            final_state = result
            
        logger.info("Graph execution completed.")
        
        # 4. Verify results
        print("\n" + "="*50)
        print("VERIFICATION RESULTS")
        print("="*50)
        
        # Ensure status is RUNNING
        status = final_state.metadata.status
        print(f"Status: {status.value} (Expected: RUNNING)")
        assert status == ExecutionStatus.RUNNING, "Status is not RUNNING"
        
        # Ensure metric_collector is in visited_nodes
        visited = final_state.metadata.visited_nodes
        print(f"Visited Nodes: {visited} (Expected to contain 'metric_collector')")
        assert "metric_collector" in visited, "'metric_collector' not in visited nodes"
        
        # Check metrics
        cpu_usage = final_state.metrics.cpu_usage
        replica_count = final_state.metrics.replica_count
        print(f"CPU Usage: {cpu_usage}")
        print(f"Replica Count: {replica_count}")
        
        if status == ExecutionStatus.FAILED:
            print(f"\nExecution FAILED with error: {final_state.metadata.error_message}")
            print("Note: This is expected if the Spring Boot service is not currently running locally.")
        else:
            assert cpu_usage > 0, f"CPU Usage is not > 0: {cpu_usage}"
            assert replica_count >= 1, f"Replica Count is not >= 1: {replica_count}"
            print("\nAll assertions PASSED!")
            
        print("\n" + "="*50)
        print("FINAL STATE DUMP")
        print("="*50)
        pprint(final_state.model_dump())
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
        
if __name__ == "__main__":
    main()
