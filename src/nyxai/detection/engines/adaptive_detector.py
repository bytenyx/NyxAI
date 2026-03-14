"""Adaptive threshold anomaly detectors for NyxAI.

This module implements adaptive threshold algorithms that can adjust
their detection thresholds based on data characteristics:
- AdaptiveThresholdDetector: Dynamic threshold based on data statistics
- QuantileDetector: Quantile-based adaptive detection
- SeasonalAdaptiveDetector: Seasonal pattern aware adaptive detection
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import Field, field_validator
from scipy import stats

from nyxai.detection.base import BaseDetector, DetectionResult, DetectorConfig
from nyxai.detection.models.anomaly import Anomaly


class AdaptiveThresholdConfig(DetectorConfig):
    """Configuration for Adaptive Threshold detector.

    Attributes:
        window_size: Size of the sliding window for statistics calculation.
        min_periods: Minimum number of observations required.
        adaptation_rate: Rate at which threshold adapts (0.0 to 1.0).
        base_threshold: Base multiplier for standard deviation.
        min_threshold: Minimum threshold value.
        max_threshold: Maximum threshold value.
        use_percentile: Use percentile-based threshold instead of std.
        percentile: Percentile to use for threshold (if use_percentile).
    """

    window_size: int = Field(
        default=50,
        ge=10,
        description="Size of sliding window for statistics",
    )
    min_periods: int = Field(
        default=20,
        ge=10,
        description="Minimum observations required",
    )
    adaptation_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Rate at which threshold adapts",
    )
    base_threshold: float = Field(
        default=3.0,
        ge=1.0,
        description="Base multiplier for standard deviation",
    )
    min_threshold: float = Field(
        default=1.5,
        ge=0.5,
        description="Minimum threshold value",
    )
    max_threshold: float = Field(
        default=5.0,
        ge=2.0,
        description="Maximum threshold value",
    )
    use_percentile: bool = Field(
        default=False,
        description="Use percentile-based threshold",
    )
    percentile: float = Field(
        default=95.0,
        ge=50.0,
        le=99.9,
        description="Percentile for threshold",
    )

    @field_validator("min_periods")
    @classmethod
    def validate_min_periods(cls, v: int, info: Any) -> int:
        """Validate min_periods is not larger than window_size."""
        if "window_size" in info.data and v > info.data["window_size"]:
            raise ValueError("min_periods cannot be larger than window_size")
        return v


class AdaptiveThresholdDetector(BaseDetector[AdaptiveThresholdConfig]):
    """Adaptive threshold anomaly detector.

    This detector dynamically adjusts its threshold based on the data's
    statistical properties. It uses a sliding window to compute statistics
    and adapts the threshold based on data volatility and historical patterns.

    The adaptation mechanism considers:
    - Data volatility (standard deviation)
    - Recent anomaly rate
    - Trend direction

    Attributes:
        config: AdaptiveThresholdConfig instance.
        _threshold_history: History of adaptive thresholds.
        _current_threshold: Current adaptive threshold.
    """

    def __init__(self, config: AdaptiveThresholdConfig | None = None) -> None:
        """Initialize the Adaptive Threshold detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or AdaptiveThresholdConfig())
        self._threshold_history: list[float] = []
        self._current_threshold: float = self.config.base_threshold

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> AdaptiveThresholdDetector:
        """Fit the detector to training data.

        Args:
            data: Training data.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.
        """
        values = self.validate_data(data)

        # Calculate initial threshold based on training data
        if self.config.use_percentile:
            self._current_threshold = np.percentile(
                np.abs(values - np.median(values)),
                self.config.percentile,
            )
        else:
            std = np.std(values)
            self._current_threshold = self.config.base_threshold * std

        # Clamp threshold
        self._current_threshold = np.clip(
            self._current_threshold,
            self.config.min_threshold,
            self.config.max_threshold,
        )

        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using adaptive threshold.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - adaptation_rate: Override config adaptation_rate

        Returns:
            List of detected anomalies.
        """
        if not self.is_enabled():
            return []

        values = self.validate_data(data)
        n = len(values)

        if n < self.config.min_periods:
            raise ValueError(
                f"Data must have at least {self.config.min_periods} points, got {n}"
            )

        adaptation_rate = kwargs.get("adaptation_rate", self.config.adaptation_rate)

        # Compute adaptive thresholds and detect anomalies
        result = self._compute_adaptive_anomalies(values, adaptation_rate)

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="adaptive_threshold",
            timestamps=timestamps,
        )

    def _compute_adaptive_anomalies(
        self,
        values: np.ndarray,
        adaptation_rate: float,
    ) -> DetectionResult:
        """Compute anomalies using adaptive threshold.

        Args:
            values: Input values array.
            adaptation_rate: Rate at which threshold adapts.

        Returns:
            DetectionResult with anomaly information.
        """
        n = len(values)
        window_size = self.config.window_size
        min_periods = self.config.min_periods

        series = pd.Series(values)

        # Compute rolling statistics
        rolling_mean = series.rolling(
            window=window_size, min_periods=min_periods
        ).mean()
        rolling_std = series.rolling(
            window=window_size, min_periods=min_periods
        ).std()

        # Initialize arrays
        thresholds = np.zeros(n)
        anomaly_mask = np.zeros(n, dtype=bool)

        # Track recent anomaly rate for adaptation
        recent_anomaly_count = 0
        recent_window_size = min(window_size // 4, 20)

        for i in range(n):
            if i < min_periods:
                # Use global statistics for initial points
                center = np.mean(values[: min(i + 1, min_periods)])
                std = np.std(values[: min(i + 1, min_periods)]) or 1.0
            else:
                center = rolling_mean.iloc[i]
                std = rolling_std.iloc[i] or 1.0

            # Calculate adaptive threshold
            if self.config.use_percentile:
                # Use percentile-based threshold
                window_data = values[max(0, i - window_size + 1) : i + 1]
                threshold = np.percentile(
                    np.abs(window_data - np.median(window_data)),
                    self.config.percentile,
                )
            else:
                # Use standard deviation based threshold
                volatility_factor = 1.0 + (std / np.mean(rolling_std.dropna()) - 1.0) * 0.5
                threshold = self._current_threshold * volatility_factor * std

            # Clamp threshold
            threshold = np.clip(
                threshold,
                self.config.min_threshold * std,
                self.config.max_threshold * std,
            )

            # Adapt threshold based on recent anomaly rate
            if recent_anomaly_count > recent_window_size * 0.2:  # > 20% anomalies
                # Too many anomalies, increase threshold
                threshold *= 1 + adaptation_rate
            elif recent_anomaly_count < recent_window_size * 0.05:  # < 5% anomalies
                # Too few anomalies, decrease threshold
                threshold *= 1 - adaptation_rate * 0.5

            thresholds[i] = threshold

            # Check for anomaly
            if i >= min_periods and np.isfinite(center) and np.isfinite(threshold):
                deviation = abs(values[i] - center)
                is_anomaly = deviation > threshold
                anomaly_mask[i] = is_anomaly

                # Update recent anomaly count
                if is_anomaly:
                    recent_anomaly_count += 1
                if i >= recent_window_size:
                    if anomaly_mask[i - recent_window_size]:
                        recent_anomaly_count -= 1

        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate scores
        if len(anomaly_indices) > 0:
            deviations = np.abs(values[anomaly_indices] - rolling_mean.iloc[anomaly_indices])
            scores = np.minimum(deviations / thresholds[anomaly_indices], 1.0)
            max_score = float(np.max(scores))
            confidence = min(self.config.sensitivity * (1 + max_score), 1.0)
        else:
            max_score = 0.0
            confidence = 1.0

        return DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=max_score,
            confidence=confidence,
            indices=anomaly_indices,
            metadata={
                "thresholds": thresholds[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "current_threshold": self._current_threshold,
                "adaptation_rate": adaptation_rate,
                "window_size": window_size,
            },
        )

    def get_threshold_history(self) -> list[float]:
        """Get the history of adaptive thresholds.

        Returns:
            List of threshold values over time.
        """
        return self._threshold_history.copy()


class QuantileConfig(DetectorConfig):
    """Configuration for Quantile-based detector.

    Attributes:
        window_size: Size of the sliding window.
        lower_percentile: Lower percentile bound.
        upper_percentile: Upper percentile bound.
        min_periods: Minimum observations required.
    """

    window_size: int = Field(
        default=100,
        ge=20,
        description="Size of sliding window",
    )
    lower_percentile: float = Field(
        default=5.0,
        ge=0.0,
        le=50.0,
        description="Lower percentile bound",
    )
    upper_percentile: float = Field(
        default=95.0,
        ge=50.0,
        le=100.0,
        description="Upper percentile bound",
    )
    min_periods: int = Field(
        default=30,
        ge=10,
        description="Minimum observations required",
    )

    @field_validator("upper_percentile")
    @classmethod
    def validate_percentiles(cls, v: float, info: Any) -> float:
        """Validate that upper_percentile > lower_percentile."""
        if "lower_percentile" in info.data and v <= info.data["lower_percentile"]:
            raise ValueError("upper_percentile must be greater than lower_percentile")
        return v


class QuantileDetector(BaseDetector[QuantileConfig]):
    """Quantile-based adaptive anomaly detector.

    This detector uses rolling percentiles to define dynamic bounds.
    Data points outside the specified percentile range are flagged as anomalies.

    Attributes:
        config: QuantileConfig instance.
    """

    def __init__(self, config: QuantileConfig | None = None) -> None:
        """Initialize the Quantile detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or QuantileConfig())

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> QuantileDetector:
        """Fit the detector to training data.

        For QuantileDetector, fitting is not strictly required as
        percentiles are computed online.

        Args:
            data: Training data.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.
        """
        _ = self.validate_data(data)
        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using quantile-based bounds.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - lower_percentile: Override config lower_percentile
                - upper_percentile: Override config upper_percentile

        Returns:
            List of detected anomalies.
        """
        if not self.is_enabled():
            return []

        values = self.validate_data(data)
        n = len(values)

        if n < self.config.min_periods:
            raise ValueError(
                f"Data must have at least {self.config.min_periods} points, got {n}"
            )

        lower_p = kwargs.get("lower_percentile", self.config.lower_percentile)
        upper_p = kwargs.get("upper_percentile", self.config.upper_percentile)

        # Compute quantile-based anomalies
        result = self._compute_quantile_anomalies(values, lower_p, upper_p)

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="quantile",
            timestamps=timestamps,
        )

    def _compute_quantile_anomalies(
        self,
        values: np.ndarray,
        lower_p: float,
        upper_p: float,
    ) -> DetectionResult:
        """Compute anomalies using quantile bounds.

        Args:
            values: Input values array.
            lower_p: Lower percentile bound.
            upper_p: Upper percentile bound.

        Returns:
            DetectionResult with anomaly information.
        """
        n = len(values)
        window_size = self.config.window_size
        min_periods = self.config.min_periods

        lower_bounds = np.zeros(n)
        upper_bounds = np.zeros(n)
        anomaly_mask = np.zeros(n, dtype=bool)

        for i in range(n):
            if i < min_periods - 1:
                # Not enough data yet
                continue

            # Get window data
            start_idx = max(0, i - window_size + 1)
            window_data = values[start_idx : i + 1]

            # Calculate percentiles
            lower_bounds[i] = np.percentile(window_data, lower_p)
            upper_bounds[i] = np.percentile(window_data, upper_p)

            # Check if current value is outside bounds
            if values[i] < lower_bounds[i] or values[i] > upper_bounds[i]:
                anomaly_mask[i] = True

        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate scores
        if len(anomaly_indices) > 0:
            scores = []
            for idx in anomaly_indices:
                if values[idx] < lower_bounds[idx]:
                    # Below lower bound
                    range_size = lower_bounds[idx] - np.min(values)
                    if range_size > 0:
                        score = min(
                            (lower_bounds[idx] - values[idx]) / range_size, 1.0
                        )
                    else:
                        score = 1.0
                else:
                    # Above upper bound
                    range_size = np.max(values) - upper_bounds[idx]
                    if range_size > 0:
                        score = min(
                            (values[idx] - upper_bounds[idx]) / range_size, 1.0
                        )
                    else:
                        score = 1.0
                scores.append(score)

            max_score = float(np.max(scores))
            confidence = min(self.config.sensitivity * (1 + max_score * 0.5), 1.0)
        else:
            max_score = 0.0
            confidence = 1.0

        return DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=max_score,
            confidence=confidence,
            indices=anomaly_indices,
            metadata={
                "lower_bounds": lower_bounds[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "upper_bounds": upper_bounds[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "lower_percentile": lower_p,
                "upper_percentile": upper_p,
                "window_size": window_size,
            },
        )


class SeasonalAdaptiveConfig(AdaptiveThresholdConfig):
    """Configuration for Seasonal Adaptive detector.

    Attributes:
        season_length: Length of seasonal pattern.
        seasonal_strength: Weight given to seasonal component (0.0 to 1.0).
    """

    season_length: int = Field(
        default=24,
        ge=2,
        description="Length of seasonal pattern",
    )
    seasonal_strength: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for seasonal component",
    )


class SeasonalAdaptiveDetector(BaseDetector[SeasonalAdaptiveConfig]):
    """Seasonal pattern aware adaptive anomaly detector.

    This detector extends the adaptive threshold approach by considering
    seasonal patterns in the data. It decomposes the time series into
    trend, seasonal, and residual components for more accurate detection.

    Attributes:
        config: SeasonalAdaptiveConfig instance.
        _seasonal_pattern: Learned seasonal pattern.
    """

    def __init__(self, config: SeasonalAdaptiveConfig | None = None) -> None:
        """Initialize the Seasonal Adaptive detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or SeasonalAdaptiveConfig())
        self._seasonal_pattern: np.ndarray | None = None

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> SeasonalAdaptiveDetector:
        """Fit the detector to training data and extract seasonal pattern.

        Args:
            data: Training data.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.
        """
        values = self.validate_data(data)
        n = len(values)

        if n < self.config.season_length * 2:
            raise ValueError(
                f"Data must have at least {self.config.season_length * 2} points "
                f"to detect seasonality, got {n}"
            )

        # Extract seasonal pattern using moving averages
        self._seasonal_pattern = self._extract_seasonal_pattern(values)

        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using seasonal adaptive threshold.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - seasonal_strength: Override config seasonal_strength

        Returns:
            List of detected anomalies.
        """
        if not self.is_enabled():
            return []

        values = self.validate_data(data)
        n = len(values)

        if n < self.config.min_periods:
            raise ValueError(
                f"Data must have at least {self.config.min_periods} points, got {n}"
            )

        seasonal_strength = kwargs.get(
            "seasonal_strength", self.config.seasonal_strength
        )

        # Compute seasonal adaptive anomalies
        result = self._compute_seasonal_anomalies(values, seasonal_strength)

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="seasonal_adaptive",
            timestamps=timestamps,
        )

    def _extract_seasonal_pattern(self, values: np.ndarray) -> np.ndarray:
        """Extract seasonal pattern from data.

        Args:
            values: Input time series.

        Returns:
            Seasonal pattern array.
        """
        season_length = self.config.season_length
        n = len(values)

        # Calculate seasonal subseries means
        seasonal_pattern = np.zeros(season_length)
        counts = np.zeros(season_length)

        for i in range(n):
            season_idx = i % season_length
            seasonal_pattern[season_idx] += values[i]
            counts[season_idx] += 1

        # Average each season position
        seasonal_pattern = np.divide(
            seasonal_pattern,
            counts,
            out=np.zeros_like(seasonal_pattern),
            where=counts != 0,
        )

        # Center the pattern
        seasonal_pattern -= np.mean(seasonal_pattern)

        return seasonal_pattern

    def _compute_seasonal_anomalies(
        self,
        values: np.ndarray,
        seasonal_strength: float,
    ) -> DetectionResult:
        """Compute anomalies using seasonal adaptive threshold.

        Args:
            values: Input values array.
            seasonal_strength: Weight for seasonal component.

        Returns:
            DetectionResult with anomaly information.
        """
        n = len(values)
        window_size = self.config.window_size
        min_periods = self.config.min_periods
        season_length = self.config.season_length

        series = pd.Series(values)

        # Compute trend using rolling mean
        trend = series.rolling(window=window_size, min_periods=min_periods).mean()

        # Compute seasonal component
        seasonal_component = np.zeros(n)
        if self._seasonal_pattern is not None:
            for i in range(n):
                season_idx = i % season_length
                seasonal_component[i] = self._seasonal_pattern[season_idx]

        # Compute expected values (trend + seasonal)
        expected = trend.to_numpy() + seasonal_strength * seasonal_component

        # Compute residuals
        residuals = values - expected

        # Compute rolling statistics of residuals
        residual_series = pd.Series(residuals)
        rolling_std = residual_series.rolling(
            window=window_size, min_periods=min_periods
        ).std()

        # Detect anomalies
        anomaly_mask = np.zeros(n, dtype=bool)
        thresholds = np.zeros(n)

        for i in range(min_periods, n):
            if not np.isfinite(rolling_std.iloc[i]):
                continue

            std = rolling_std.iloc[i] or 1.0
            threshold = self.config.base_threshold * std

            # Clamp threshold
            threshold = np.clip(
                threshold,
                self.config.min_threshold * std,
                self.config.max_threshold * std,
            )

            thresholds[i] = threshold

            if abs(residuals[i]) > threshold:
                anomaly_mask[i] = True

        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate scores
        if len(anomaly_indices) > 0:
            scores = np.abs(residuals[anomaly_indices]) / thresholds[anomaly_indices]
            scores = np.minimum(scores, 1.0)
            max_score = float(np.max(scores))
            confidence = min(self.config.sensitivity * (1 + max_score), 1.0)
        else:
            max_score = 0.0
            confidence = 1.0

        return DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=max_score,
            confidence=confidence,
            indices=anomaly_indices,
            metadata={
                "residuals": residuals[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "thresholds": thresholds[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "seasonal_strength": seasonal_strength,
                "season_length": season_length,
            },
        )

    def get_seasonal_pattern(self) -> np.ndarray | None:
        """Get the learned seasonal pattern.

        Returns:
            Seasonal pattern if fitted, None otherwise.
        """
        return self._seasonal_pattern.copy() if self._seasonal_pattern is not None else None
