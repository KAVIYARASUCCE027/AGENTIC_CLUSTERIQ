"""
Metric Validator Module — Phase 3.

Validates raw metric values received from the Spring Boot backend
before they enter the CPUState.  Acts as a quality gate between
the transport layer and the business layer.

Validation Rules:
    cpu_usage           →  0.0 ≤ value ≤ 100.0
    cpu_limit           →  value ≥ 0.0
    cpu_request         →  value ≥ 0.0
    restart_count       →  value ≥ 0
    replica_count       →  value ≥ 1
    throttling_pct      →  0.0 ≤ value ≤ 100.0

Design Notes:
    • Each check is an independent static method so it can be unit-tested
      in isolation and composed freely by the caller.
    • ``validate_all()`` runs every check and raises on the **first**
      failure to fail fast with a clear message.
    • All failures raise ``MetricValidationException`` with the field
      name, the offending value, and a human-readable reason.
"""

from __future__ import annotations

import logging

from services.exception_handler import MetricValidationException

logger = logging.getLogger(__name__)


class MetricValidator:
    """
    Stateless validator for CPU metric values.

    All methods are ``@staticmethod`` — instantiate the class for
    namespacing only; no internal state is held.
    """

    # -----------------------------------------------------------------
    # Individual Field Validators
    # -----------------------------------------------------------------

    @staticmethod
    def validate_cpu_usage(value: float) -> float:
        """
        Validate that CPU usage is within [0, 100].

        Args:
            value: CPU usage percentage.

        Returns:
            The validated value (pass-through on success).

        Raises:
            MetricValidationException: If the value is out of range.
        """
        if not (0.0 <= value <= 100.0):
            raise MetricValidationException(
                field="cpu_usage",
                value=value,
                reason="CPU usage must be between 0.0 and 100.0 (inclusive).",
            )
        logger.debug("Validated cpu_usage = %.2f%%.", value)
        return value

    @staticmethod
    def validate_cpu_limit(value: float) -> float:
        """
        Validate that CPU limit is non-negative.

        Args:
            value: CPU limit in millicores or percentage.

        Returns:
            The validated value.

        Raises:
            MetricValidationException: If the value is negative.
        """
        if value < 0.0:
            raise MetricValidationException(
                field="cpu_limit",
                value=value,
                reason="CPU limit cannot be negative.",
            )
        logger.debug("Validated cpu_limit = %.2f.", value)
        return value

    @staticmethod
    def validate_cpu_request(value: float) -> float:
        """
        Validate that CPU request is non-negative.

        Args:
            value: CPU request in millicores or percentage.

        Returns:
            The validated value.

        Raises:
            MetricValidationException: If the value is negative.
        """
        if value < 0.0:
            raise MetricValidationException(
                field="cpu_request",
                value=value,
                reason="CPU request cannot be negative.",
            )
        logger.debug("Validated cpu_request = %.2f.", value)
        return value

    @staticmethod
    def validate_restart_count(value: int) -> int:
        """
        Validate that restart count is non-negative.

        Args:
            value: Container restart count.

        Returns:
            The validated value.

        Raises:
            MetricValidationException: If the value is negative.
        """
        if value < 0:
            raise MetricValidationException(
                field="restart_count",
                value=value,
                reason="Restart count cannot be negative.",
            )
        logger.debug("Validated restart_count = %d.", value)
        return value

    @staticmethod
    def validate_replica_count(value: int) -> int:
        """
        Validate that replica count is at least 1.

        A running pod must belong to at least one replica.

        Args:
            value: Number of running replicas.

        Returns:
            The validated value.

        Raises:
            MetricValidationException: If the value is less than 1.
        """
        if value < 1:
            raise MetricValidationException(
                field="replica_count",
                value=value,
                reason="Replica count must be at least 1.",
            )
        logger.debug("Validated replica_count = %d.", value)
        return value

    @staticmethod
    def validate_throttling_percentage(value: float) -> float:
        """
        Validate that throttling percentage is within [0, 100].

        Args:
            value: Throttling percentage.

        Returns:
            The validated value.

        Raises:
            MetricValidationException: If the value is out of range.
        """
        if not (0.0 <= value <= 100.0):
            raise MetricValidationException(
                field="throttling_percentage",
                value=value,
                reason="Throttling percentage must be between 0.0 and 100.0.",
            )
        logger.debug("Validated throttling_percentage = %.2f%%.", value)
        return value

    # -----------------------------------------------------------------
    # Aggregate Validator
    # -----------------------------------------------------------------

    @classmethod
    def validate_all(
        cls,
        cpu_usage: float,
        cpu_limit: float,
        cpu_request: float,
        restart_count: int,
        replica_count: int,
        throttling_percentage: float = 0.0,
    ) -> None:
        """
        Run all metric validations in sequence.

        Raises on the **first** validation failure (fail-fast).

        Args:
            cpu_usage: CPU usage percentage.
            cpu_limit: CPU limit value.
            cpu_request: CPU request value.
            restart_count: Container restart count.
            replica_count: Replica count.
            throttling_percentage: CPU throttling percentage.

        Raises:
            MetricValidationException: On the first invalid value.
        """
        logger.info("Running full metric validation suite…")

        cls.validate_cpu_usage(cpu_usage)
        cls.validate_cpu_limit(cpu_limit)
        cls.validate_cpu_request(cpu_request)
        cls.validate_restart_count(restart_count)
        cls.validate_replica_count(replica_count)
        cls.validate_throttling_percentage(throttling_percentage)

        logger.info(
            "All metrics validated successfully: "
            "cpu=%.1f%%, limit=%.1f, request=%.1f, "
            "restarts=%d, replicas=%d, throttling=%.1f%%.",
            cpu_usage,
            cpu_limit,
            cpu_request,
            restart_count,
            replica_count,
            throttling_percentage,
        )
