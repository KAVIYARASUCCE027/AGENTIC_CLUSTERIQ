"""
Prometheus Metrics Registry — Phase 10.
"""
from prometheus_client import Counter, Histogram

# Latency histogram
agent_execution_seconds = Histogram(
    'agent_execution_seconds',
    'Time spent executing an agent',
    ['agent_name']
)

# Failure counter
agent_failures_total = Counter(
    'agent_failures_total',
    'Total number of agent execution failures',
    ['agent_name']
)

# Retry counter
agent_retry_total = Counter(
    'agent_retry_total',
    'Total number of agent retries',
    ['agent_name']
)

# Token usage counter
agent_tokens_total = Counter(
    'agent_tokens_total',
    'Total number of tokens consumed by the agent',
    ['agent_name']
)
