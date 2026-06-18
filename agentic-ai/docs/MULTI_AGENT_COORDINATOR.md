# Multi-Agent Coordinator — Phase 10

## Architecture Overview

The Multi-Agent Coordinator acts as the central brain of the Kubernetes AIOps platform. It is responsible for orchestrating the execution of all specialized AI agents while enforcing state management, failure recovery, and observability policies.

Crucially, **the LangGraph workflow engine remains intact**. The nodes (`analyzer_node`, `root_cause_node`, `recommendation_node`, `action_planner_node`, `memory_node`) are preserved to maintain full workflow visibility, LangSmith tracing, and debugging capabilities. However, these nodes have been refactored into **thin wrappers** that delegate execution to the `MultiAgentCoordinator`.

```text
LangGraph

START
↓
metric_collector
↓
analyzer_node        → MultiAgentCoordinator.execute_agent("analyzer", state)
↓
root_cause_node      → MultiAgentCoordinator.execute_agent("root_cause", state)
↓
recommendation_node  → MultiAgentCoordinator.execute_agent("recommendation", state)
↓
action_planner_node  → MultiAgentCoordinator.execute_agent("action_planner", state)
↓
memory_node          → MultiAgentCoordinator.execute_agent("memory", state)
↓
END
```

---

## Core Components

### 1. Agents Layer (`agents/`)
Each service is wrapped in an implementation of `BaseAgent`. The `BaseAgent` enforces a strict interface:
- `name()`: Identifier.
- `execute(state)`: Core execution logic mutating the `CPUState`.
- `validate(state)`: Validation checks.
- `rollback(state)`: Recovery mechanisms if execution fails.

### 2. Agent Registry (`services/agent_registry.py`)
Dynamically registers and provisions instances of all `BaseAgent` implementations.

### 3. State Manager (`services/state_manager.py`)
Responsible for deep-copying and safely merging `CPUState`. It ensures that execution identifiers remain consistent and prevents state corruption during parallel execution or graph transitions.

### 4. Multi-Agent Coordinator (`services/multi_agent_coordinator.py`)
The orchestrator. When a LangGraph node calls `coordinator.execute_agent()`, the coordinator:
1. Records the start time and sets the agent status to `RUNNING`.
2. Looks up the agent from the `AgentRegistry`.
3. Invokes `agent.execute()`.
4. Handles any exceptions. If a failure occurs, it triggers `agent.rollback()`, logs the failure, increments Prometheus error metrics, and gracefully returns the original state (preventing the pipeline from crashing).
5. Emits latency and token-usage metrics to Prometheus.

---

## Observability & Prometheus Metrics

The coordinator exposes key metrics to allow monitoring the platform via Grafana.

- `agent_execution_seconds`: Histogram measuring agent latency.
- `agent_failures_total`: Counter tracking execution failures per agent.
- `agent_retry_total`: Counter tracking retries.
- `agent_tokens_total`: Counter tracking token consumption for Gemini interactions.

---

## Execution Policies & Future Extensions

Currently, the coordinator executes in **SEQUENTIAL** mode, driven by the LangGraph edges.

In future phases, the coordinator's architecture supports:
1. **PARALLEL** execution (e.g., fetching Root Cause and Memory context simultaneously).
2. **CONDITIONAL** execution (e.g., executing the Action Planner only if Severity > WARNING).
3. **Autonomous Remediation** via an Execution Agent.
4. **Human Approval Workflows** for high-risk actions.
