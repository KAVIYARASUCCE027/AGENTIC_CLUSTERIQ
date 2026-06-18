# Recommendation Agent — Phase 7

## Purpose

The Recommendation Agent is the third AI-powered agent in the CPU Analysis pipeline. It receives the structured health assessment (Phase 5) and root cause analysis (Phase 6) and determines **what the SRE team should do next**. It uses `gemini-2.5-flash` for intelligent prioritization and falls back to deterministic rules when the AI result is unreliable.

---

## Architecture

```
CPUState (metrics + analyzer_output + root_cause_output)
         ↓
recommendation_node  →  RecommendationInputSchema
         ↓
RecommendationPromptBuilder  (injects all context)
         ↓
GeminiRecommendationService  (services/ai/)
         ↓ [if failed or confidence < 60]
FallbackRecommendationService  (keyed on RootCauseType)
         ↓
RecommendationResponseValidator  (validates JSON)
         ↓
RecommendationOutputState  →  CPUState.recommendation_output
```

---

## Input Schema (`RecommendationInputSchema`)

| Field | Source |
|---|---|
| `pod_name` | `state.inputs.pod_name` |
| `namespace` | `state.inputs.namespace` |
| `metrics.*` | `state.metrics` (CPU, restarts, replicas, limits) |
| `analyzer_output.*` | `state.analyzer_output` (health_status, severity, trend) |
| `root_cause_output.*` | `state.root_cause_output` (root_cause, confidence, evidence) |

---

## Output Schema (`RecommendationOutputState`)

```json
{
  "recommendations": ["INCREASE_CPU_LIMIT", "ENABLE_HPA"],
  "reasoning": [
    "CPU usage at 95% has hit the configured limit of 1000m.",
    "HPA will automatically scale replicas during future spikes."
  ],
  "confidence": 88,
  "confidence_level": "HIGH",
  "possible_recommendations": [
    {"recommendation": "SCALE_UP_REPLICAS", "confidence": 70, "priority": "MEDIUM", "description": "Temporary relief"},
    {"recommendation": "REVIEW_DEPLOYMENT", "confidence": 60, "priority": "LOW", "description": "Review resource config"}
  ],
  "source": "GEMINI",
  "model_name": "gemini-2.5-flash",
  "execution_time_ms": 310,
  "token_usage": 503,
  "timestamp": "2026-06-18T05:57:00Z"
}
```

---

## Recommendation Types (Enums)

| Value | Trigger |
|---|---|
| `SCALE_UP_REPLICAS` | High CPU + low replica count |
| `ENABLE_HPA` | Any spike or sustained high CPU |
| `INCREASE_CPU_LIMIT` | CPU at configured limit |
| `INCREASE_CPU_REQUEST` | Sustained CPU, misaligned request |
| `INVESTIGATE_APPLICATION` | Application bug or restart loop |
| `CHECK_NODE_UTILIZATION` | Node resource contention |
| `RESTART_POD` | Pod in crash loop |
| `REVIEW_DEPLOYMENT` | Resource config needs audit |
| `MONITOR_CLOSELY` | Ambiguous or uncertain situation |
| `NO_ACTION_REQUIRED` | Metrics normal or recovering |

---

## Gemini Configuration

| Parameter | Value |
|---|---|
| Model | `gemini-2.5-flash` |
| Temperature | `0.2` (slightly creative for context-aware reasoning) |
| Top-P | `0.8` |
| Top-K | `20` |
| Max Output Tokens | `700` |
| Retries | `2` (with structured logging per attempt) |

---

## Fallback Rules (by Root Cause)

| Root Cause | Primary Recommendations | Confidence |
|---|---|---|
| `CPU_LIMIT_REACHED` | `INCREASE_CPU_LIMIT`, `ENABLE_HPA` | 88 |
| `INSUFFICIENT_REPLICAS` | `SCALE_UP_REPLICAS`, `ENABLE_HPA` | 85 |
| `POD_RESTARTING` | `INVESTIGATE_APPLICATION`, `RESTART_POD` | 82 |
| `WORKLOAD_SPIKE` | `ENABLE_HPA`, `SCALE_UP_REPLICAS` | 83 |
| `RESOURCE_REQUEST_TOO_LOW` | `INCREASE_CPU_REQUEST`, `REVIEW_DEPLOYMENT` | 78 |
| `NODE_RESOURCE_CONTENTION` | `CHECK_NODE_UTILIZATION`, `REVIEW_DEPLOYMENT` | 75 |
| `APPLICATION_BUG` | `INVESTIGATE_APPLICATION`, `MONITOR_CLOSELY` | 72 |
| `UNKNOWN` | `MONITOR_CLOSELY`, `REVIEW_DEPLOYMENT` | 40 |

---

## Error Handling & Fallback

1. **Gemini fails** → `FallbackRecommendationService` runs rule-based recommendations.
2. **Invalid JSON** → `RecommendationResponseValidator` repairs or substitutes fallback.
3. **Confidence < 60** → Fallback is compared; highest confidence wins.
4. **Invalid enum values** → Invalid recommendations are filtered; falls back to `MONITOR_CLOSELY`.

The `source` field (`GEMINI` | `FALLBACK`) provides full transparency.

---

## File Structure

```
enums/
    recommendation_type.py       # 10 recommendation actions
    recommendation_source.py     # GEMINI | FALLBACK
    confidence_level.py          # VERY_HIGH | HIGH | MEDIUM | LOW

prompts/
    recommendation_system_prompt.txt
    recommendation_template.txt
    recommendation_prompt_builder.py

schemas/
    recommendation_input.py
    recommendation_output.py     # With CandidateRecommendation + metadata

services/
    ai/
        gemini_recommendation_service.py
    fallback_recommendation_service.py
    recommendation_response_validator.py

nodes/cpu/
    recommendation_node.py

utils/
    recommendation_logger.py

tests/recommendation/
    test_prompt_builder.py
    test_response_validator.py
    test_fallback_service.py
    test_recommendation_node.py
```

---

## Testing Strategy

All 28 tests run without a real Gemini API call:
```bash
python -m pytest tests/recommendation/ -v
```

---

## Known Limitations

1. **Priority ordering**: Gemini may not always order recommendations by priority; the fallback always does.
2. **Token usage**: Only available when Gemini returns `usage_metadata`.

---

## Future Enhancements

| Phase | Enhancement |
|---|---|
| Phase 8 | Pass `possible_recommendations` to Action Planner |
| Phase 9 | Store recommendations in MongoDB for trend analysis |
| Phase 10 | Multi-agent voting on recommendations |
