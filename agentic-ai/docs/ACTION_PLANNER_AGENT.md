# Action Planner Agent — Phase 8

## Purpose

The Action Planner Agent is the fourth node in the AI pipeline. It takes the output from the Analyzer, Root Cause, and Recommendation agents and transforms it into a concrete, step-by-step **executable runbook**.

It acts as an automated SRE, producing actionable steps with evaluated risks, estimated durations, and safe rollback strategies. The agent uses `gemini-2.5-flash` with a strict deterministic fallback mechanism.

---

## Architecture

```
CPUState (metrics + analyzer + root_cause + recommendation)
         ↓
action_planner_node  →  ActionPlanInputSchema
         ↓
ActionPlannerPromptBuilder  (injects context into templates)
         ↓
GeminiActionPlannerService  (services/ai/)
         ↓ [if failed or confidence < 60]
FallbackActionPlannerService  (maps RecommendationType to action plan)
         ↓
ActionPlanResponseValidator  (enforces JSON integrity and enums)
         ↓
ActionPlanOutputState  →  CPUState.action_plan_output
```

---

## Inputs (`ActionPlanInputSchema`)

| Field | Source |
|---|---|
| `pod_name` / `namespace` | `state.inputs` |
| `metrics.*` | `state.metrics` |
| `analyzer_output.*` | `state.analyzer_output` |
| `root_cause_output.*` | `state.root_cause_output` |
| `recommendation_output.*` | `state.recommendation_output` |

---

## Outputs (`ActionPlanOutputState`)

```json
{
  "actions": [
    {
      "step": 1,
      "action": "Identify the deployment managing pod 'api-pod' in namespace 'prod'.",
      "action_type": "KUBECTL_COMMAND",
      "risk": "LOW",
      "estimated_duration": "1 minute"
    },
    {
      "step": 2,
      "action": "Patch the deployment to increase the CPU limit by 20%.",
      "action_type": "PATCH_DEPLOYMENT",
      "risk": "MEDIUM",
      "estimated_duration": "2 minutes"
    }
  ],
  "priority": "HIGH",
  "risk": "MEDIUM",
  "estimated_duration": "3 minutes",
  "rollback_strategy": "Revert the deployment CPU limit to its previous value using kubectl rollback.",
  "confidence": 85,
  "source": "FALLBACK",
  "model_name": "fallback",
  "execution_time_ms": 1,
  "token_usage": null,
  "timestamp": "2026-06-18T06:10:00Z"
}
```

---

## Enums

### `ActionType`
Defines the executable nature of the step:
- `KUBECTL_COMMAND`
- `PATCH_DEPLOYMENT`
- `HELM_UPGRADE`
- `MANUAL_INVESTIGATION`
- `CREATE_TICKET`
- `NO_ACTION`

### `ActionPriority` / `ActionRisk`
- `HIGH`
- `MEDIUM`
- `LOW`

### `ActionSource`
- `GEMINI`
- `FALLBACK`

---

## Gemini Configuration

| Parameter | Value |
|---|---|
| Model | `gemini-2.5-flash` |
| Temperature | `0.1` (Highly deterministic, minimal creativity) |
| Top-P | `0.8` |
| Top-K | `20` |
| Max Output Tokens | `1000` |
| Retries | `2` (with structured logging) |

---

## Fallback Action Planner

The `FallbackActionPlannerService` ensures the system never fails silently. It triggers when:
1. Gemini API is unreachable or fails all retries.
2. Gemini returns an invalid JSON that cannot be repaired.
3. Gemini returns a plan with `confidence < 60`.

**Fallback Logic:**
The fallback service picks the **highest-priority recommendation** from `recommendation_output` (index 0) and maps it deterministically to an `ActionPlanOutputState`.

*Example: If the primary recommendation is `SCALE_UP_REPLICAS`, the fallback produces a 1-step plan with a `KUBECTL_COMMAND` action type and a rollback strategy to scale back down.*

---

## File Structure

```
enums/
    action_type.py
    action_priority.py
    action_risk.py
    action_source.py

prompts/
    action_planner_system_prompt.txt
    action_planner_template.txt
    action_planner_prompt_builder.py

schemas/
    action_plan_input.py
    action_plan_output.py

services/
    ai/gemini_action_planner_service.py
    fallback_action_planner_service.py
    action_plan_response_validator.py

nodes/cpu/
    action_planner_node.py

utils/
    action_planner_logger.py

tests/action_planner/
    test_prompt_builder.py
    test_response_validator.py
    test_fallback_service.py
    test_action_planner_node.py
```

---

## Testing Strategy

Run the test suite (no real Gemini API calls required):
```bash
python -m pytest tests/action_planner/ -v
```

Tests validate prompt injection, JSON validator edge cases (missing fields, trailing commas, invalid enums), fallback deterministic logic, and node state management.

---

## Known Limitations

- Gemini token usage metadata is only available if `usage_metadata` is populated in the API response.
- Rollback strategies are descriptive strings; future enhancements could parse these into discrete `ActionStep` arrays.

---

## Future Enhancements

| Phase | Enhancement |
|---|---|
| Phase 9 | Store the generated action plan in MongoDB (Memory Layer) alongside the incident. |
| Future | Auto-remediation: allow the agent to execute `LOW` risk action plans automatically without human intervention. |
