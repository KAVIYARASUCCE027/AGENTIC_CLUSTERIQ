"""
Services package for K8S Agentic AI Service.

Contains LLM integration, external data source services, and the
Phase 3 metric collection pipeline.

Phase 1:
    llm_service          — Google Gemini LLM singleton
    prometheus_service   — Mock Prometheus metrics (legacy)

Phase 3 — Metric Service Layer:
    exception_handler    — Custom domain exceptions
    retry_service        — Exponential backoff retry decorator
    cache_service        — Thread-safe in-memory TTL cache
    springboot_client    — Spring Boot REST HTTP client
    metric_validator     — Raw metric validation rules
    metric_calculator    — Derived metric computations
    cpu_metric_service   — Central metric orchestrator
"""
