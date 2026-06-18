"""
CPU Agent Graph Module.
Defines the LangGraph pipeline for the CPU Analysis Agent.
"""
import logging
from langgraph.graph import StateGraph, START, END

from schemas.cpu_state import CPUState
from nodes.cpu.metric_collector_node import metric_collector
from nodes.cpu.analyzer_node import analyzer_node
from nodes.cpu.root_cause_node import root_cause_node
from nodes.cpu.recommendation_node import recommendation_node
from nodes.cpu.action_planner_node import action_planner_node
from nodes.cpu.memory_node import memory_node

logger = logging.getLogger(__name__)

def build_cpu_graph() -> StateGraph:
    """
    Builds and compiles the CPU Analysis LangGraph.
    
    Returns:
        A compiled StateGraph ready for execution.
    """
    logger.info("Building CPU Agent LangGraph...")
    
    # 1. Initialize StateGraph with CPUState
    graph_builder = StateGraph(CPUState)
    
    # 2. Add nodes
    graph_builder.add_node("metric_collector", metric_collector)
    graph_builder.add_node("analyzer", analyzer_node)
    graph_builder.add_node("root_cause", root_cause_node)
    graph_builder.add_node("recommendation", recommendation_node)
    graph_builder.add_node("action_planner", action_planner_node)
    graph_builder.add_node("memory", memory_node)
    
    # 3. Define the edges (workflow)
    graph_builder.add_edge(START, "metric_collector")
    graph_builder.add_edge("metric_collector", "analyzer")
    graph_builder.add_edge("analyzer", "root_cause")
    graph_builder.add_edge("root_cause", "recommendation")
    graph_builder.add_edge("recommendation", "action_planner")
    graph_builder.add_edge("action_planner", "memory")
    graph_builder.add_edge("memory", END)
    
    # 4. Compile graph
    compiled_graph = graph_builder.compile()
    logger.info("CPU Agent LangGraph compiled successfully.")
    
    return compiled_graph
