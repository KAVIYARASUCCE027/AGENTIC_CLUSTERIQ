# Root Cause Agent — Phase 6

## Purpose

The Root Cause Agent is the first AI-powered agent in the Kubernetes CPU analysis pipeline. It receives the structured health assessment from the Phase 5 Analyzer Node and determines **why** the CPU incident occurred, using `gemini-2.5-flash` backed by a deterministic fallback for production reliability.

---

## Architecture

```
CPUState (analyzer_output + metrics)
         ↓
root_cause_node  →  RootCauseInputSchema
         ↓
RootCausePromptBuilder  (loads prompts/*.txt, injects metrics)
         ↓
GeminiRootCauseService  (services/ai/)
         ↓ [if failed or confidence < 60]
FallbackRootCauseService  (deterministic rules)
         ↓
RootCauseResponseValidator  (validates JSON, repairs malformed responses)
         ↓
RootCauseOutputState  →  CPUState.root_cause_output
```

---

## Inputs

`RootCauseInputSchema` is built by `root_cause_node` from `CPUState`:

| Field | Source |
|---|---|
| `pod_name` | `state.inputs.pod_name` |
| `namespace` | `state.inputs.namespace` |
| `severity` | `state.analyzer_output.severity` |
| `abnormality` | `state.analyzer_output.abnormality` |
| `analyzer_reasoning` | `state.analyzer_output.reasoning` |
| `cpu_metrics.current_cpu_usage` | `state.metrics.cpu_usage` |
| `cpu_metrics.avg_cpu_5m` | `state.metrics.avg_cpu_last_5m` |
| `cpu_metrics.avg_cpu_15m` | `state.metrics.avg_cpu_last_15m` |
| `cpu_metrics.cpu_trend` | `state.metrics.cpu_trend` |
| `cpu_metrics.cpu_limit` | `state.metrics.cpu_limit` |
| `restart_metrics.restart_count` | `state.metrics.restart_count` |
| `replica_metrics.current_replicas` | `state.metrics.replica_count` |

---

## Outputs

`RootCauseOutputState` is stored in `CPUState.root_cause_output`:

```json
{
  "root_cause": "WORKLOAD_SPIKE",
  "confidence": 92,
  "evidence": [
    "Current CPU is 95%, but 5m average is only 40%"
  ],
  "reasoning": [
    "Large gap between current and 5m average indicates a sudden spike",
    "Restart count is low, ruling out crash loops"
  ],
  "possible_causes": [
    {"cause": "APPLICATION_BUG", "confidence": 40},
    {"cause": "INSUFFICIENT_REPLICAS", "confidence": 30}
  ],
  "source": "GEMINI",
  "model_name": "gemini-2.5-flash",
  "execution_time_ms": 320,
  "token_usage": 487,
  "timestamp": "2026-06-18T05:45:00Z"
}
```

---

## Root Cause Types (Enums)

| Value | Meaning |
|---|---|
| `CPU_LIMIT_REACHED` | Pod CPU usage at/near configured limit |
| `INSUFFICIENT_REPLICAS` | Load too high for current replica count |
| `POD_RESTARTING` | Crash loop / OOMKill / liveness failure |
| `NODE_RESOURCE_CONTENTION` | Noisy neighbor on the same node |
| `WORKLOAD_SPIKE` | Sudden traffic burst or cron job |
| `RESOURCE_REQUEST_TOO_LOW` | Sustained high CPU across all time windows |
| `APPLICATION_BUG` | Code-level performance issue |
| `UNKNOWN` | Insufficient data to determine cause |

---

## Gemini Configuration

| Parameter | Value |
|---|---|
| Model | `gemini-2.5-flash` |
| Temperature | `0.1` (near-deterministic) |
| Top-P | `0.8` |
| Top-K | `20` |
| Max Output Tokens | `500` |
| Retries | `2` (with logging per attempt) |

---

## Error Handling & Fallback

The agent is designed to **never fail silently**:

1. **Gemini API down** → `FallbackRootCauseService` runs deterministic rules.
2. **Invalid JSON from Gemini** → `RootCauseResponseValidator` repairs or substitutes safe fallback.
3. **Low confidence (`< 60`)** → `FallbackRootCauseService` is compared; highest confidence wins.
4. **Root cause = UNKNOWN** → Fallback is always attempted.

The `source` field in `RootCauseOutputState` (`GEMINI` | `FALLBACK`) provides full transparency on which path was taken.

---

## File Structure

```
enums/
    root_cause_type.py          # RootCauseType enum (8 values)
    root_cause_source.py        # RootCauseSource enum (GEMINI | FALLBACK)

prompts/
    root_cause_system_prompt.txt    # Senior SRE system instruction
    root_cause_template.txt         # User-turn metric injection template
    root_cause_prompt_builder.py    # Loads files, injects values

schemas/
    root_cause_input.py         # Input contract (Pydantic)
    root_cause_output.py        # Output contract with LLM metadata

services/
    ai/
        gemini_root_cause_service.py    # Gemini call with retries
    fallback_root_cause_service.py      # Deterministic fallback rules
    root_cause_response_validator.py    # JSON validation and repair

nodes/cpu/
    root_cause_node.py          # Thin LangGraph node

utils/
    root_cause_logger.py        # Structured logging for each stage

tests/root_cause/
    test_prompt_builder.py
    test_response_validator.py
    test_fallback_service.py
    test_root_cause_node.py
```

---

## Testing Strategy

All tests run **without a real Gemini API call**:
- `GeminiRootCauseService` is mocked via `unittest.mock.patch`.
- `FallbackRootCauseService` is tested directly (pure rules, no external deps).
- `RootCauseResponseValidator` is tested against edge cases (empty, malformed, invalid enum).
- `RootCausePromptBuilder` is tested for correct metric injection.

Run all tests:
```bash
python -m pytest tests/root_cause/ -v
```

---

## Known Limitations

1. **Node CPU metrics**: `NodeContentionRule` requires node-level CPU data not yet available in `CPUState`. Currently returns `UNKNOWN` for this path.
2. **Token usage**: Token count depends on Gemini API returning `usage_metadata`. It is `None` when unavailable.
3. **Rate limits**: Gemini API rate limits may cause all retries to fail. The fallback guarantees a result in this case.

---

## Future Enhancements

| Phase | Enhancement |
|---|---|
| Phase 7 | Pass `root_cause_output.possible_causes` to Recommendation Agent |
| Phase 9 | Store `root_cause_output` in MongoDB `cpu_incidents` collection |
| Phase 9 | Use `root_cause` history for similarity search in Memory Agent |
| Future | Support multiple LLM providers (GPT-4o, Claude) via abstraction layer |
