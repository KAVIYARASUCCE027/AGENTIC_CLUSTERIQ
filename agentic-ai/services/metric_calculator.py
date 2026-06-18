"""
Metric Calculator Module — Phase 3.

Derives secondary metrics from raw and historical CPU data:
    • Rolling averages (5 min, 15 min, 1 hour)
    • CPU trend direction (Increasing / Stable / Decreasing)
    • Throttling percentage

All methods are pure functions — they take data in, return results,
and produce no side-effects.  This makes them trivially unit-testable.

Design Notes:
    • ``calculate_trend`` uses a simple slope heuristic: if the short
      window average exceeds the long window by more than a configurable
      threshold, the trend is INCREASING, and vice versa.
    • ``calculate_averages`` operates on a generic list of floats so the
      same function works with any time-series data.
    • When insufficient data is available, methods return safe defaults
      rather than raising — the caller can check for zeroes.
"""

from __future__ import annotations

import logging
from typing import Sequence

from schemas.cpu_state import CPUTrend
from services.exception_handler import CalculatorException

logger = logging.getLogger(__name__)

# Number of expected data points per time window.
# Assuming ~1 sample / minute from the Spring Boot backend.
_POINTS_5M: int = 5
_POINTS_15M: int = 15
_POINTS_1H: int = 60

# Trend detection threshold (percentage-point difference)
_TREND_THRESHOLD: float = 5.0


class MetricCalculator:
    """
    Stateless calculator for derived CPU metrics.

    All methods are ``@staticmethod`` — no instance state is held.
    """

    # -----------------------------------------------------------------
    # Rolling Averages
    # -----------------------------------------------------------------

    @staticmethod
    def calculate_average(data_points: Sequence[float], window: int) -> float:
        """
        Calculate the arithmetic mean of the most recent ``window`` values.

        If fewer than ``window`` data points are available, the average
        is computed over whatever is present.  An empty sequence returns
        ``0.0``.

        Args:
            data_points: Time-series values (newest first).
            window: Number of most-recent points to include.

        Returns:
            The arithmetic mean, rounded to two decimal places.
        """
        if not data_points:
            logger.debug("No data points provided — returning 0.0.")
            return 0.0

        subset = list(data_points[:window])
        avg = round(sum(subset) / len(subset), 2)

        logger.debug(
            "Calculated average over %d/%d points: %.2f.",
            len(subset),
            window,
            avg,
        )
        return avg

    @classmethod
    def calculate_averages(
        cls,
        cpu_history: Sequence[float],
    ) -> dict[str, float]:
        """
        Compute the 5-min, 15-min, and 1-hour rolling averages.

        Args:
            cpu_history: Historical CPU usage values (newest first).

        Returns:
            Dictionary with keys ``avg_cpu_last_5m``, ``avg_cpu_last_15m``,
            and ``avg_cpu_last_1h``.
        """
        try:
            averages = {
                "avg_cpu_last_5m": cls.calculate_average(cpu_history, _POINTS_5M),
                "avg_cpu_last_15m": cls.calculate_average(cpu_history, _POINTS_15M),
                "avg_cpu_last_1h": cls.calculate_average(cpu_history, _POINTS_1H),
            }

            logger.info(
                "Rolling averages computed: 5m=%.2f%%, 15m=%.2f%%, 1h=%.2f%%.",
                averages["avg_cpu_last_5m"],
                averages["avg_cpu_last_15m"],
                averages["avg_cpu_last_1h"],
            )
            return averages

        except Exception as exc:
            raise CalculatorException(
                f"Failed to calculate rolling averages: {exc}",
            ) from exc

    # -----------------------------------------------------------------
    # Trend Detection
    # -----------------------------------------------------------------

    @classmethod
    def calculate_trend(
        cls,
        cpu_history: Sequence[float],
        threshold: float = _TREND_THRESHOLD,
    ) -> CPUTrend:
        """
        Determine the CPU usage trend direction.

        Compares the short-window (5 min) average against the long-window
        (1 hour) average.  If the short window exceeds the long window by
        more than ``threshold`` percentage points, the trend is
        ``INCREASING``; if it is lower by more than ``threshold``, the
        trend is ``DECREASING``; otherwise ``STABLE``.

        Args:
            cpu_history: Historical CPU usage values (newest first).
            threshold: Minimum difference (pp) to classify as non-stable.

        Returns:
            The detected ``CPUTrend`` enum member.
        """
        try:
            if len(cpu_history) < 2:
                logger.info(
                    "Insufficient data for trend detection (%d points) "
                    "— defaulting to STABLE.",
                    len(cpu_history),
                )
                return CPUTrend.STABLE

            avg_short = cls.calculate_average(cpu_history, _POINTS_5M)
            avg_long = cls.calculate_average(cpu_history, _POINTS_1H)

            diff = avg_short - avg_long

            if diff > threshold:
                trend = CPUTrend.INCREASING
            elif diff < -threshold:
                trend = CPUTrend.DECREASING
            else:
                trend = CPUTrend.STABLE

            logger.info(
                "Trend detected: %s (short=%.2f%%, long=%.2f%%, diff=%.2f pp).",
                trend.value,
                avg_short,
                avg_long,
                diff,
            )
            return trend

        except Exception as exc:
            raise CalculatorException(
                f"Failed to calculate CPU trend: {exc}",
            ) from exc

    # -----------------------------------------------------------------
    # Throttling
    # -----------------------------------------------------------------

    @staticmethod
    def calculate_throttling(
        cpu_usage: float,
        cpu_limit: float,
    ) -> float:
        """
        Estimate the CPU throttling percentage.

        Uses a simplified model: if usage exceeds the limit, the excess
        fraction is treated as throttled cycles.  When the limit is zero
        (unlimited), throttling is 0 %.

        Args:
            cpu_usage: Current CPU usage percentage.
            cpu_limit: CPU limit assigned to the pod.

        Returns:
            Throttling percentage, clamped to [0.0, 100.0].
        """
        try:
            if cpu_limit <= 0.0:
                logger.debug("CPU limit is 0 (unlimited) — throttling = 0%%.")
                return 0.0

            if cpu_usage <= cpu_limit:
                logger.debug(
                    "CPU usage (%.2f) ≤ limit (%.2f) — throttling = 0%%.",
                    cpu_usage,
                    cpu_limit,
                )
                return 0.0

            throttle = min(
                ((cpu_usage - cpu_limit) / cpu_limit) * 100.0,
                100.0,
            )
            throttle = round(throttle, 2)

            logger.info(
                "Throttling estimated: %.2f%% (usage=%.2f, limit=%.2f).",
                throttle,
                cpu_usage,
                cpu_limit,
            )
            return throttle

        except Exception as exc:
            raise CalculatorException(
                f"Failed to calculate throttling: {exc}",
            ) from exc
