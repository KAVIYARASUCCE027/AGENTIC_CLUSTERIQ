"""
CPU Metric Service Module — Phase 3.

Central orchestrator for the metric collection pipeline.  Coordinates
the Spring Boot client, validator, calculator, and cache to produce a
fully-populated ``MetricState`` that is written back into ``CPUState``.

Workflow:
    1. Check cache for existing metrics (short-circuit on hit).
    2. Call Spring Boot APIs via ``SpringBootClient``.
    3. Validate raw values via ``MetricValidator``.
    4. Derive secondary metrics via ``MetricCalculator``.
    5. Build a ``MetricState`` instance.
    6. Store result in cache for future requests.
    7. Return the enriched ``CPUState``.

Design Notes:
    • This service is the **only** module that directly mutates the
      ``metrics`` section of ``CPUState``.  All other modules interact
      through this single entry point.
    • Failures at any stage are caught, logged, and re-raised as the
      appropriate domain exception so the calling node can set the
      state to FAILED with a meaningful error message.
    • The service is injected with its dependencies via the constructor
      to support testing with mocks / stubs.
"""

from __future__ import annotations

import logging
from typing import Optional

from schemas.cpu_state import CPUState, CPUTrend, MetricState
from services.cache_service import CacheService, get_cache_service
from services.exception_handler import (
    AgentBaseException,
    MetricFetchException,
    MetricValidationException,
)
from services.metric_calculator import MetricCalculator
from services.metric_validator import MetricValidator
from services.springboot_client import SpringBootClient

logger = logging.getLogger(__name__)


class CPUMetricService:
    """
    Orchestrates CPU metric collection, validation, enrichment, and caching.

    Args:
        client: HTTP client for Spring Boot APIs.
                Defaults to a new ``SpringBootClient`` instance.
        cache: TTL cache for metric responses.
               Defaults to the singleton ``CacheService``.
    """

    def __init__(
        self,
        client: Optional[SpringBootClient] = None,
        cache: Optional[CacheService] = None,
    ) -> None:
        self._client = client or SpringBootClient()
        self._cache = cache or get_cache_service()
        self._validator = MetricValidator()
        self._calculator = MetricCalculator()

        logger.info("CPUMetricService initialised.")

    # -----------------------------------------------------------------
    # Public Entry Point
    # -----------------------------------------------------------------

    def collect_and_populate(self, state: CPUState) -> CPUState:
        """
        Collect, validate, enrich, and populate metrics into CPUState.

        This is the **single entry point** for the metric node.

        Args:
            state: Current ``CPUState`` with ``inputs`` already populated.

        Returns:
            A new ``CPUState`` with the ``metrics`` section fully populated.

        Raises:
            MetricFetchException: If metrics cannot be retrieved.
            MetricValidationException: If any metric value is invalid.
            AgentBaseException: For any other domain-specific failure.
        """
        pod_name = state.inputs.pod_name
        namespace = state.inputs.namespace

        logger.info(
            "CPUMetricService: Starting metric collection for "
            "pod '%s' in namespace '%s'.",
            pod_name,
            namespace,
        )

        # --- Step 1: Check cache ---
        cache_key = CacheService.build_pod_metric_key(
            namespace=namespace,
            pod_name=pod_name,
            metric_type="cpu_full",
        )
        cached_metrics: Optional[MetricState] = self._cache.get(cache_key)

        if cached_metrics is not None:
            logger.info(
                "CPUMetricService: Returning cached metrics for '%s/%s'.",
                namespace,
                pod_name,
            )
            return state.model_copy(update={"metrics": cached_metrics})

        # --- Step 2: Fetch raw metrics from Spring Boot ---
        logger.info("CPUMetricService: Fetching metrics from Spring Boot…")

        cpu_response = self._client.get_cpu_metrics(pod_name)
        restart_response = self._client.get_restart_count(pod_name)
        replica_response = self._client.get_replica_count(pod_name)
        details_response = self._client.get_pod_details(pod_name)

        logger.info(
            "CPUMetricService: All API responses received for '%s'.",
            pod_name,
        )

        # --- Step 3: Validate raw values ---
        logger.info("CPUMetricService: Validating metrics…")

        self._validator.validate_all(
            cpu_usage=cpu_response.cpu_usage,
            cpu_limit=cpu_response.cpu_limit,
            cpu_request=cpu_response.cpu_request,
            restart_count=restart_response.restart_count,
            replica_count=replica_response.replica_count,
            throttling_percentage=cpu_response.throttling_percentage,
        )

        # --- Step 4: Derive secondary metrics ---
        logger.info("CPUMetricService: Calculating derived metrics…")

        cpu_history = details_response.cpu_history
        averages = self._calculator.calculate_averages(cpu_history)
        trend = self._calculator.calculate_trend(cpu_history)
        throttling = self._calculator.calculate_throttling(
            cpu_usage=cpu_response.cpu_usage,
            cpu_limit=cpu_response.cpu_limit,
        )

        # --- Step 5: Build MetricState ---
        metric_state = MetricState(
            cpu_usage=cpu_response.cpu_usage,
            cpu_limit=cpu_response.cpu_limit,
            cpu_request=cpu_response.cpu_request,
            restart_count=restart_response.restart_count,
            replica_count=replica_response.replica_count,
            throttling_percentage=throttling,
            cpu_trend=trend,
            avg_cpu_last_5m=averages["avg_cpu_last_5m"],
            avg_cpu_last_15m=averages["avg_cpu_last_15m"],
            avg_cpu_last_1h=averages["avg_cpu_last_1h"],
        )

        logger.info(
            "CPUMetricService: MetricState built — "
            "cpu=%.1f%%, trend=%s, throttle=%.1f%%.",
            metric_state.cpu_usage,
            metric_state.cpu_trend.value,
            metric_state.throttling_percentage,
        )

        # --- Step 6: Cache the result ---
        self._cache.set(cache_key, metric_state)

        # --- Step 7: Return updated CPUState ---
        updated_state = state.model_copy(update={"metrics": metric_state})

        # Also enrich inputs if Spring Boot returned node/cluster info
        if details_response.node_name or details_response.cluster_name:
            updated_inputs = state.inputs.model_copy(
                update={
                    k: v
                    for k, v in {
                        "node_name": details_response.node_name,
                        "cluster_name": details_response.cluster_name,
                    }.items()
                    if v  # only overwrite if non-empty
                }
            )
            updated_state = updated_state.model_copy(
                update={"inputs": updated_inputs},
            )

        logger.info(
            "CPUMetricService: Metric collection complete for '%s/%s'.",
            namespace,
            pod_name,
        )
        return updated_state
