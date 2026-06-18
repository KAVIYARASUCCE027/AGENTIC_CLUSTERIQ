"""
CPU Prompt Templates Module.

Contains reusable prompt strings for CPU-related LLM interactions
including analysis and recommendation generation.
"""

# --- CPU Analysis Prompt ---
CPU_ANALYSIS_PROMPT: str = """You are a Kubernetes infrastructure expert specializing in CPU resource analysis.

Analyze the following CPU metrics for a Kubernetes pod and provide a detailed assessment.

**Pod Information:**
- Namespace: {namespace}
- Pod Name: {pod_name}

**CPU Metrics:**
- Current CPU Usage: {cpu_usage_cores} cores
- CPU Limit: {cpu_limit_cores} cores
- CPU Usage Percentage: {cpu_usage_percent}%
- Timestamp: {timestamp}

**Instructions:**
1. Assess whether the CPU usage is normal, elevated, or critical.
2. Identify any potential issues or risks.
3. Provide a clear, concise summary of the CPU health status.

Respond with a structured analysis including:
- **Status**: (Normal / Warning / Critical)
- **Summary**: A brief one-line summary.
- **Details**: A detailed explanation of the assessment.
"""

# --- High CPU Recommendation Prompt ---
HIGH_CPU_RECOMMENDATION_PROMPT: str = """You are a Kubernetes operations expert.

The following pod is experiencing HIGH CPU usage and requires immediate attention.

**Pod Information:**
- Namespace: {namespace}
- Pod Name: {pod_name}

**CPU Metrics:**
- Current CPU Usage: {cpu_usage_cores} cores
- CPU Limit: {cpu_limit_cores} cores
- CPU Usage Percentage: {cpu_usage_percent}%

**Analysis Result:**
{analysis_result}

**Instructions:**
Provide actionable recommendations to resolve the high CPU usage. Include:
1. Immediate actions to mitigate the issue.
2. Short-term fixes (e.g., resource limit adjustments, HPA configuration).
3. Long-term solutions (e.g., code optimization, architectural changes).
4. Specific kubectl commands or YAML snippets where applicable.

Be precise, actionable, and production-oriented.
"""

# --- Normal CPU Recommendation Prompt ---
NORMAL_CPU_RECOMMENDATION_PROMPT: str = """You are a Kubernetes operations expert.

The following pod has NORMAL CPU usage levels.

**Pod Information:**
- Namespace: {namespace}
- Pod Name: {pod_name}

**CPU Metrics:**
- Current CPU Usage: {cpu_usage_cores} cores
- CPU Limit: {cpu_limit_cores} cores
- CPU Usage Percentage: {cpu_usage_percent}%

**Analysis Result:**
{analysis_result}

**Instructions:**
Provide optimization recommendations for maintaining healthy CPU usage. Include:
1. Whether current resource limits are appropriately sized.
2. Suggestions for resource optimization (right-sizing).
3. Monitoring best practices to maintain this healthy state.
4. Any preventive measures to avoid future CPU issues.

Be concise and actionable.
"""
