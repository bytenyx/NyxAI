"""Base detector classes for NyxAI anomaly detection.

This module defines the abstract base classes and configuration models
for all anomaly detectors in the system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from nyxai.detection.models.anomaly import Anomaly


class DetectorConfig(BaseModel):
    """Base configuration for all detectors.

    Attributes:
        name: Human-readable name for the detector.
        description: Optional description of the detector.
        enabled: Whether the detector is enabled.
        sensitivity: Detection sensitivity threshold (0.0 to 1.0).
        min_anomaly_score: Minimum score to consider as anomaly.
    """

    name: str = Field(default="BaseDetector", description="Detector name")
    description: str | None = Field(default=None, description="Detector description")
    enabled: bool = Field(default=True, description="Whether detector is enabled")
    sensitivity: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Detection sensitivity (0.0 to 1.0)",
    )
    min_anomaly_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum anomaly score threshold",
    )

    class Config:
        """Pydantic configuration."""

        frozen = True


T = TypeVar("T", bound=DetectorConfig)


@dataclass
class DetectionResult:
    """Result of anomaly detection.

    Attributes:
        is_anomaly: Whether an anomaly was detected.
        score: Anomaly score (0.0 to 1.0, higher means more anomalous).
        confidence: Confidence in the detection (0.0 to 1.0).
        indices: Indices of anomalous data points.
        metadata: Additional detection metadata.
    """

    is_anomaly: bool
    score: float
    confidence: float
    indices: np.ndarray
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate result fields."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


class BaseDetector(ABC, Generic[T]):
    """Abstract base class for all anomaly detectors.

    All anomaly detectors must inherit from this class and implement
the detect() method.

    Type Parameters:
        T: The configuration type for this detector.

    Attributes:
        config: Detector configuration.
    """

    def __init__(self, config: T) -> None:
        """Initialize the detector with configuration.

        Args:
            config: Detector configuration.
        """
        self.config = config

    @abstractmethod
    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies in the provided data.

        Args:
            data: Input data to analyze. Can be numpy array, pandas Series,
                or DataFrame.
            timestamps: Optional timestamps corresponding to data points.
            **kwargs: Additional detector-specific parameters.

        Returns:
            List of detected anomalies.

        Raises:
            ValueError: If data format is invalid.
            RuntimeError: If detection fails.
        """
        ...

    @abstractmethod
    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> "BaseDetector[T]":
        """Fit the detector to training data.

        Args:
            data: Training data for the detector.
            **kwargs: Additional fitting parameters.

        Returns:
            Self for method chaining.
        """
        ...

    def validate_data(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
    ) -> np.ndarray:
        """Validate and convert input data to numpy array.

        Args:
            data: Input data to validate.

        Returns:
            Validated numpy array.

        Raises:
            ValueError: If data is invalid.
        """
        if isinstance(data, pd.DataFrame):
            if data.shape[1] != 1:
                raise ValueError(
                    f"DataFrame must have exactly 1 column, got {data.shape[1]}"
                )
            return data.iloc[:, 0].to_numpy(dtype=np.float64)
        elif isinstance(data, pd.Series):
            return data.to_numpy(dtype=np.float64)
        elif isinstance(data, np.ndarray):
            if data.ndim == 1:
                return data.astype(np.float64)
            elif data.ndim == 2 and data.shape[1] == 1:
                return data.flatten().astype(np.float64)
            else:
                raise ValueError(
                    f"Array must be 1D or 2D with shape (n, 1), got shape {data.shape}"
                )
        else:
            raise ValueError(
                f"Data must be numpy array, pandas Series, or DataFrame, got {type(data)}"
            )

    def _create_anomalies(
        self,
        result: DetectionResult,
        source_type: str,
        detection_method: str,
        timestamps: pd.DatetimeIndex | None = None,
    ) -> list[Anomaly]:
        """Create Anomaly objects from detection result.

        Args:
            result: Detection result containing anomaly indices.
            source_type: Type of data source (e.g., 'metric', 'log').
            detection_method: Method used for detection.
            timestamps: Optional timestamps for anomaly points.

        Returns:
            List of Anomaly objects.
        """
        anomalies: list[Anomaly] = []

        if not result.is_anomaly or len(result.indices) == 0:
            return anomalies

        for idx in result.indices:
            idx_int = int(idx)
            timestamp = timestamps[idx_int] if timestamps is not None else None

            anomaly = Anomaly.create(
                title=f"Anomaly detected at index {idx_int}",
                description=f"Anomaly detected using {detection_method}",
                severity=Anomaly.from_score(result.score),
                source_type=source_type,
                detection_method=detection_method,
                score=result.score,
                confidence=result.confidence,
                timestamp=timestamp,
                metadata={
                    "index": idx_int,
                    **(result.metadata or {}),
                },
            )
            anomalies.append(anomaly)

        return anomalies

    def is_enabled(self) -> bool:
        """Check if the detector is enabled.

        Returns:
            True if detector is enabled, False otherwise.
        """
        return self.config.enabled
