# Memory Layer — Phase 9

## Purpose

The Memory Layer transforms the CPU Agent from a stateless pipeline into a learning AIOps platform. It persists the output of every pipeline phase (Metrics, Analyzer, Root Cause, Recommendation, Action Plan) into a structured historical incident record.

When a new incident occurs, the Memory Agent queries this layer to find similar historical events, extract recurring patterns, and generate contextual intelligence. This context is then injected into `CPUState.memory_output` so downstream agents (Phase 10 Multi-Agent Coordinator) can make informed decisions based on past successes or failures.

---

## Architecture

The Memory Layer acts as the final node in the current pipeline:
```text
Analyzer → Root Cause → Recommendation → Action Planner → Memory Node → END
```

### Components
1. **Memory Node**: LangGraph orchestrator.
2. **Memory Service**: Business logic mapping `CPUState` ↔ `IncidentRecord`, and computing similarity.
3. **Memory/Incident Repositories**: Data access layer executing PyMongo aggregate pipelines.
4. **MongoDB**: The physical storage layer (`cpu_incidents` collection).

---

## Database Configuration

We use **MongoDB Atlas** for production persistence, and `mongomock` for testing.

### Collections
- `cpu_incidents`: Stores full `IncidentRecord` documents.
- `memory_metadata`: Stores configuration, TTL rules, and system-level metadata.

### Index Strategy (`database/indexes.py`)
To ensure low-latency lookups (<100ms), the following indexes are maintained:
1. `{"pod_name": 1, "namespace": 1}` — Fast pod filtering.
2. `{"timestamp": -1}` — Fast time-series sorting.
3. `{"root_cause.root_cause": 1}` — Pattern extraction.
4. `{"analyzer.severity": 1}` — Similarity weighting.

---

## Similarity Engine

In the absence of a vector database (coming in Phase 10), similarity is computed deterministically via a weighted MongoDB `$addFields` pipeline:
- **Pod Match**: +0.4
- **Root Cause Match**: +0.4
- **Severity Match**: +0.2

*Threshold*: Incidents scoring `≥ 0.4` within the last 90 days are considered similar.

---

## Retention Policy

- **Hot Data (Read/Write)**: Incidents are actively queried for similarity for **90 days**.
- **Archive Data (Read-Only)**: Incidents older than 90 days are flagged as `ARCHIVED` (or naturally age out) and retained for up to **365 days** for long-term auditing and compliance.

---

## Fallback Strategy

If the MongoDB connection drops, times out, or fails authentication, the **Memory Node will not crash the pipeline**.

1. It catches the `PyMongoError`.
2. It logs a `[FALLBACK]` warning using the `MemoryLogger`.
3. It sets `MemoryOutputState.source = MemorySource.FALLBACK`.
4. It allows the LangGraph state to advance to `END` gracefully.

---

## File Structure

```
enums/
    memory_source.py
    incident_status.py

schemas/
    memory/incident_record.py
    memory_output.py

database/
    mongo_client.py
    collections.py
    indexes.py

repositories/
    incident_repository.py
    memory_repository.py

services/
    memory_service.py

nodes/cpu/
    memory_node.py

utils/
    memory_logger.py
```
