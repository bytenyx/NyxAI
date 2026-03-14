"""Statistical anomaly detectors for NyxAI.

This module implements statistical-based anomaly detection algorithms:
- ThreeSigmaDetector: 3-sigma rule-based detection
- EWMADetector: Exponentially Weighted Moving Average detection
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import Field, field_validator

from nyxai.detection.base import BaseDetector, DetectionResult, DetectorConfig
from nyxai.detection.models.anomaly import Anomaly


class ThreeSigmaConfig(DetectorConfig):
    """Configuration for Three Sigma detector.

    Attributes:
        window_size: Size of the sliding window for statistics calculation.
        min_periods: Minimum number of observations required.
        use_median: Use median instead of mean for robust statistics.
        direction: Detection direction ('both', 'upper', 'lower').
    """

    window_size: int = Field(
        default=30,
        ge=3,
        description="Size of sliding window for statistics",
    )
    min_periods: int = Field(
        default=10,
        ge=3,
        description="Minimum observations required",
    )
    use_median: bool = Field(
        default=False,
        description="Use median instead of mean",
    )
    direction: str = Field(
        default="both",
        description="Detection direction: 'both', 'upper', 'lower'",
    )

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction parameter."""
        if v not in ("both", "upper", "lower"):
            raise ValueError("direction must be 'both', 'upper', or 'lower'")
        return v

    @field_validator("min_periods")
    @classmethod
    def validate_min_periods(cls, v: int, info: Any) -> int:
        """Validate min_periods is not larger than window_size."""
        if "window_size" in info.data and v > info.data["window_size"]:
            raise ValueError("min_periods cannot be larger than window_size")
        return v


class ThreeSigmaDetector(BaseDetector[ThreeSigmaConfig]):
    """Three-sigma rule based anomaly detector.

    This detector uses the 3-sigma rule (empirical rule) to identify anomalies.
    Data points that fall outside mean ± 3 * standard deviation are flagged.

    For robust detection, median absolute deviation (MAD) can be used instead
    of standard deviation.

    Attributes:
        config: ThreeSigmaConfig instance.
        _mean: Running mean values.
        _std: Running standard deviation values.
    """

    def __init__(self, config: ThreeSigmaConfig | None = None) -> None:
        """Initialize the Three Sigma detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or ThreeSigmaConfig())
        self._mean: np.ndarray | None = None
        self._std: np.ndarray | None = None

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> ThreeSigmaDetector:
        """Fit the detector to training data.

        For ThreeSigmaDetector, fitting calculates initial statistics
        but is not strictly required as statistics are computed online.

        Args:
            data: Training data.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.
        """
        _ = self.validate_data(data)
        # Statistics are computed during detection
        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using the 3-sigma rule.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - window_size: Override config window_size
                - direction: Override config direction

        Returns:
            List of detected anomalies.

        Raises:
            ValueError: If data is invalid or insufficient.
        """
        if not self.is_enabled():
            return []

        values = self.validate_data(data)
        n = len(values)

        if n < self.config.min_periods:
            raise ValueError(
                f"Data must have at least {self.config.min_periods} points, got {n}"
            )

        # Get parameters (allow kwargs override)
        window_size = kwargs.get("window_size", self.config.window_size)
        direction = kwargs.get("direction", self.config.direction)

        # Compute rolling statistics
        result = self._compute_anomalies(
            values, window_size, self.config.min_periods, direction
        )

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="three_sigma",
            timestamps=timestamps,
        )

    def _compute_anomalies(
        self,
        values: np.ndarray,
        window_size: int,
        min_periods: int,
        direction: str,
    ) -> DetectionResult:
        """Compute anomalies using 3-sigma rule.

        Args:
            values: Input values array.
            window_size: Rolling window size.
            min_periods: Minimum periods for valid calculation.
            direction: Detection direction.

        Returns:
            DetectionResult with anomaly information.
        """
        n = len(values)

        # Use pandas for efficient rolling calculations
        series = pd.Series(values)

        if self.config.use_median:
            # Use median and MAD for robust statistics
            center = series.rolling(window=window_size, min_periods=min_periods).median()
            mad = (
                series.rolling(window=window_size, min_periods=min_periods)
                .apply(lambda x: np.median(np.abs(x - np.median(x))), raw=True)
            )
            # Convert MAD to std equivalent (MAD * 1.4826 ≈ std for normal distribution)
            std = mad * 1.4826
        else:
            # Use mean and std
            center = series.rolling(window=window_size, min_periods=min_periods).mean()
            std = series.rolling(window=window_size, min_periods=min_periods).std()

        # Calculate z-scores
        z_scores = np.abs((values - center) / std)
        z_scores = np.nan_to_num(z_scores, nan=0.0, posinf=0.0, neginf=0.0)

        # Determine anomaly mask based on direction
        if direction == "upper":
            anomaly_mask = values > (center + 3 * std)
        elif direction == "lower":
            anomaly_mask = values < (center - 3 * std)
        else:  # both
            anomaly_mask = np.abs(values - center) > (3 * std)

        # Handle NaN values
        anomaly_mask = anomaly_mask & np.isfinite(z_scores)
        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate overall anomaly score and confidence
        if len(anomaly_indices) > 0:
            max_z_score = np.max(z_scores[anomaly_indices])
            # Convert z-score to normalized score (0-1)
            score = min(max_z_score / 5.0, 1.0)  # Cap at 5 sigma
            confidence = min(self.config.sensitivity * (1 + max_z_score / 10), 1.0)
        else:
            score = 0.0
            confidence = 1.0

        return DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=float(score),
            confidence=float(confidence),
            indices=anomaly_indices,
            metadata={
                "z_scores": z_scores[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "threshold": 3.0,
                "window_size": window_size,
                "direction": direction,
            },
        )

    def get_statistics(self) -> dict[str, np.ndarray | None]:
        """Get current statistics.

        Returns:
            Dictionary with mean and std arrays.
        """
        return {"mean": self._mean, "std": self._std}


class EWMAConfig(DetectorConfig):
    """Configuration for EWMA detector.

    Attributes:
        span: Span for EWMA calculation (center of mass = (span-1)/2).
        threshold_std: Number of standard deviations for threshold.
        min_periods: Minimum observations required.
        direction: Detection direction ('both', 'upper', 'lower').
    """

    span: int = Field(
        default=20,
        ge=2,
        description="Span for EWMA calculation",
    )
    threshold_std: float = Field(
        default=3.0,
        ge=1.0,
        description="Number of standard deviations for threshold",
    )
    min_periods: int = Field(
        default=10,
        ge=2,
        description="Minimum observations required",
    )
    direction: str = Field(
        default="both",
        description="Detection direction: 'both', 'upper', 'lower'",
    )

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction parameter."""
        if v not in ("both", "upper", "lower"):
            raise ValueError("direction must be 'both', 'upper', or 'lower'")
        return v


class EWMADetector(BaseDetector[EWMAConfig]):
    """Exponentially Weighted Moving Average anomaly detector.

    This detector uses EWMA to smooth the time series and detect deviations
    from the expected value. It's particularly effective for detecting
    gradual changes and trends in data.

    The detection is based on the deviation from the EWMA value, normalized
    by the standard deviation of the residuals.

    Attributes:
        config: EWMAConfig instance.
        _ewma: Last computed EWMA values.
        _residual_std: Standard deviation of residuals.
    """

    def __init__(self, config: EWMAConfig | None = None) -> None:
        """Initialize the EWMA detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or EWMAConfig())
        self._ewma: np.ndarray | None = None
        self._residual_std: float | None = None

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> EWMADetector:
        """Fit the detector to training data.

        Calculates the baseline EWMA and residual statistics.

        Args:
            data: Training data.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.
        """
        values = self.validate_data(data)
        series = pd.Series(values)

        # Calculate EWMA
        self._ewma = (
            series.ewm(span=self.config.span, min_periods=self.config.min_periods)
            .mean()
            .to_numpy()
        )

        # Calculate residual standard deviation
        residuals = values - self._ewma
        self._residual_std = float(np.nanstd(residuals))

        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using EWMA deviation.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - span: Override config span
                - threshold_std: Override config threshold_std
                - direction: Override config direction

        Returns:
            List of detected anomalies.

        Raises:
            ValueError: If data is invalid or insufficient.
        """
        if not self.is_enabled():
            return []

        values = self.validate_data(data)
        n = len(values)

        if n < self.config.min_periods:
            raise ValueError(
                f"Data must have at least {self.config.min_periods} points, got {n}"
            )

        # Get parameters (allow kwargs override)
        span = kwargs.get("span", self.config.span)
        threshold_std = kwargs.get("threshold_std", self.config.threshold_std)
        direction = kwargs.get("direction", self.config.direction)

        # Compute EWMA
        series = pd.Series(values)
        ewma = series.ewm(span=span, min_periods=self.config.min_periods).mean()

        # Calculate residuals and their statistics
        residuals = values - ewma.to_numpy()

        # Use fitted residual std if available, otherwise calculate from data
        if self._residual_std is not None:
            residual_std = self._residual_std
        else:
            residual_std = float(np.nanstd(residuals))

        if residual_std == 0:
            residual_std = 1e-10  # Avoid division by zero

        # Normalize residuals
        normalized_residuals = residuals / residual_std
        normalized_residuals = np.nan_to_num(
            normalized_residuals, nan=0.0, posinf=0.0, neginf=0.0
        )

        # Determine anomaly mask based on direction
        if direction == "upper":
            anomaly_mask = normalized_residuals > threshold_std
        elif direction == "lower":
            anomaly_mask = normalized_residuals < -threshold_std
        else:  # both
            anomaly_mask = np.abs(normalized_residuals) > threshold_std

        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate overall anomaly score and confidence
        if len(anomaly_indices) > 0:
            max_deviation = np.max(np.abs(normalized_residuals[anomaly_indices]))
            # Convert deviation to normalized score (0-1)
            score = min(max_deviation / (threshold_std * 2), 1.0)
            confidence = min(self.config.sensitivity * (1 + max_deviation / 10), 1.0)
        else:
            score = 0.0
            confidence = 1.0

        result = DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=float(score),
            confidence=float(confidence),
            indices=anomaly_indices,
            metadata={
                "residuals": residuals[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "normalized_residuals": normalized_residuals[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "threshold_std": threshold_std,
                "span": span,
                "direction": direction,
            },
        )

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="ewma",
            timestamps=timestamps,
        )

    def get_baseline(self) -> np.ndarray | None:
        """Get the fitted EWMA baseline.

        Returns:
            EWMA values if fitted, None otherwise.
        """
        return self._ewma

    def get_residual_std(self) -> float | None:
        """Get the residual standard deviation.

        Returns:
            Residual std if fitted, None otherwise.
        """
        return self._residual_std
