"""Machine learning based anomaly detectors for NyxAI.

This module implements ML-based anomaly detection algorithms:
- IsolationForestDetector: Isolation Forest for anomaly detection
- LOFDetector: Local Outlier Factor for anomaly detection
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from pydantic import Field, field_validator
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

from nyxai.detection.base import BaseDetector, DetectionResult, DetectorConfig
from nyxai.detection.models.anomaly import Anomaly


class IsolationForestConfig(DetectorConfig):
    """Configuration for Isolation Forest detector.

    Attributes:
        n_estimators: Number of base estimators in the ensemble.
        contamination: Expected proportion of outliers in the data.
        max_samples: Number of samples to draw from X to train each base estimator.
        random_state: Random seed for reproducibility.
        max_features: Number of features to draw from X to train each base estimator.
        bootstrap: Whether to use bootstrap samples.
    """

    n_estimators: int = Field(
        default=100,
        ge=1,
        description="Number of base estimators",
    )
    contamination: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Expected proportion of outliers",
    )
    max_samples: int | str = Field(
        default="auto",
        description="Number of samples to draw for each estimator",
    )
    random_state: int | None = Field(
        default=42,
        description="Random seed for reproducibility",
    )
    max_features: int | float = Field(
        default=1.0,
        description="Number of features to draw for each estimator",
    )
    bootstrap: bool = Field(
        default=False,
        description="Whether to use bootstrap samples",
    )


class IsolationForestDetector(BaseDetector[IsolationForestConfig]):
    """Isolation Forest anomaly detector.

    Isolation Forest is an algorithm for anomaly detection that isolates
    anomalies instead of profiling normal data points. It works by randomly
    selecting a feature and then randomly selecting a split value between
    the maximum and minimum values of the selected feature.

    Anomalies are easier to isolate and therefore have shorter path lengths
    in the isolation trees.

    Attributes:
        config: IsolationForestConfig instance.
        _model: Fitted IsolationForest model.
        _scaler: StandardScaler for feature normalization.
    """

    def __init__(self, config: IsolationForestConfig | None = None) -> None:
        """Initialize the Isolation Forest detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or IsolationForestConfig())
        self._model: IsolationForest | None = None
        self._scaler: StandardScaler | None = None

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> IsolationForestDetector:
        """Fit the detector to training data.

        Args:
            data: Training data. Can be 1D or 2D.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If data is invalid.
        """
        values = self._prepare_data(data)

        # Initialize and fit scaler
        self._scaler = StandardScaler()
        values_scaled = self._scaler.fit_transform(values)

        # Initialize and fit Isolation Forest
        self._model = IsolationForest(
            n_estimators=self.config.n_estimators,
            contamination=self.config.contamination,
            max_samples=self.config.max_samples,
            random_state=self.config.random_state,
            max_features=self.config.max_features,
            bootstrap=self.config.bootstrap,
            n_jobs=-1,
        )
        self._model.fit(values_scaled)

        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using Isolation Forest.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - contamination: Override config contamination

        Returns:
            List of detected anomalies.

        Raises:
            ValueError: If model is not fitted or data is invalid.
        """
        if not self.is_enabled():
            return []

        if self._model is None or self._scaler is None:
            raise ValueError(
                "Detector must be fitted before detection. Call fit() first."
            )

        values = self._prepare_data(data)
        n_samples = len(values)

        if n_samples < 2:
            raise ValueError("Data must have at least 2 samples")

        # Scale the data
        values_scaled = self._scaler.transform(values)

        # Get anomaly scores and predictions
        # anomaly_score: negative values are more anomalous
        anomaly_scores = self._model.score_samples(values_scaled)
        predictions = self._model.predict(values_scaled)

        # Convert to 0-1 scale (higher is more anomalous)
        # anomaly_scores are negative, with more negative being more anomalous
        min_score = np.min(anomaly_scores)
        max_score = np.max(anomaly_scores)
        score_range = max_score - min_score

        if score_range > 0:
            normalized_scores = 1 - (anomaly_scores - min_score) / score_range
        else:
            normalized_scores = np.zeros_like(anomaly_scores)

        # Find anomalies (predictions == -1 are anomalies)
        anomaly_mask = predictions == -1
        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate overall score and confidence
        if len(anomaly_indices) > 0:
            max_anomaly_score = float(np.max(normalized_scores[anomaly_indices]))
            confidence = min(
                self.config.sensitivity * (1 + max_anomaly_score),
                1.0,
            )
        else:
            max_anomaly_score = 0.0
            confidence = 1.0

        result = DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=max_anomaly_score,
            confidence=confidence,
            indices=anomaly_indices,
            metadata={
                "anomaly_scores": anomaly_scores[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "normalized_scores": normalized_scores[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "n_estimators": self.config.n_estimators,
                "contamination": self.config.contamination,
            },
        )

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="isolation_forest",
            timestamps=timestamps,
        )

    def _prepare_data(
        self, data: np.ndarray | pd.Series | pd.DataFrame
    ) -> np.ndarray:
        """Prepare data for Isolation Forest.

        Args:
            data: Input data.

        Returns:
            2D numpy array suitable for sklearn.
        """
        if isinstance(data, pd.DataFrame):
            return data.to_numpy(dtype=np.float64)
        elif isinstance(data, pd.Series):
            return data.to_numpy(dtype=np.float64).reshape(-1, 1)
        elif isinstance(data, np.ndarray):
            if data.ndim == 1:
                return data.reshape(-1, 1).astype(np.float64)
            elif data.ndim == 2:
                return data.astype(np.float64)
            else:
                raise ValueError(f"Array must be 1D or 2D, got {data.ndim}D")
        else:
            raise ValueError(
                f"Data must be numpy array, pandas Series, or DataFrame, got {type(data)}"
            )

    def get_feature_importances(self) -> np.ndarray | None:
        """Get feature importances from the model.

        Returns:
            Feature importances if available, None otherwise.
        """
        if self._model is not None:
            # IsolationForest doesn't have feature_importances_,
            # but we can return the estimators for analysis
            return None
        return None


class LOFConfig(DetectorConfig):
    """Configuration for Local Outlier Factor detector.

    Attributes:
        n_neighbors: Number of neighbors to use.
        contamination: Expected proportion of outliers in the data.
        algorithm: Algorithm for computing nearest neighbors.
        leaf_size: Leaf size for BallTree or KDTree.
        metric: Distance metric to use.
        p: Parameter for Minkowski metric.
    """

    n_neighbors: int = Field(
        default=20,
        ge=1,
        description="Number of neighbors",
    )
    contamination: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Expected proportion of outliers",
    )
    algorithm: str = Field(
        default="auto",
        description="Algorithm for nearest neighbors",
    )
    leaf_size: int = Field(
        default=30,
        ge=1,
        description="Leaf size for tree-based algorithms",
    )
    metric: str = Field(
        default="minkowski",
        description="Distance metric",
    )
    p: int = Field(
        default=2,
        ge=1,
        description="Parameter for Minkowski metric",
    )

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, v: str) -> str:
        """Validate algorithm parameter."""
        valid_algorithms = ("auto", "ball_tree", "kd_tree", "brute")
        if v not in valid_algorithms:
            raise ValueError(f"algorithm must be one of {valid_algorithms}")
        return v


class LOFDetector(BaseDetector[LOFConfig]):
    """Local Outlier Factor anomaly detector.

    LOF is a density-based anomaly detection algorithm that computes the local
    density deviation of a given data point with respect to its neighbors.
    It considers samples that have a substantially lower density than their
    neighbors as outliers.

    Attributes:
        config: LOFConfig instance.
        _model: Fitted LOF model.
        _scaler: StandardScaler for feature normalization.
        _training_data: Training data for novelty detection.
    """

    def __init__(self, config: LOFConfig | None = None) -> None:
        """Initialize the LOF detector.

        Args:
            config: Configuration for the detector. Uses defaults if None.
        """
        super().__init__(config or LOFConfig())
        self._model: LocalOutlierFactor | None = None
        self._scaler: StandardScaler | None = None
        self._training_data: np.ndarray | None = None

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> LOFDetector:
        """Fit the detector to training data.

        For LOF, fitting stores the training data for novelty detection.

        Args:
            data: Training data.
            **kwargs: Additional parameters (ignored).

        Returns:
            Self for method chaining.

        Raises:
            ValueError: If data is invalid.
        """
        values = self._prepare_data(data)

        # Store training data for novelty detection
        self._training_data = values.copy()

        # Initialize and fit scaler
        self._scaler = StandardScaler()
        self._scaler.fit(values)

        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using Local Outlier Factor.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters:
                - contamination: Override config contamination
                - n_neighbors: Override config n_neighbors

        Returns:
            List of detected anomalies.

        Raises:
            ValueError: If model is not fitted or data is invalid.
        """
        if not self.is_enabled():
            return []

        if self._scaler is None or self._training_data is None:
            raise ValueError(
                "Detector must be fitted before detection. Call fit() first."
            )

        values = self._prepare_data(data)
        n_samples = len(values)

        if n_samples < 2:
            raise ValueError("Data must have at least 2 samples")

        # Get parameters (allow kwargs override)
        contamination = kwargs.get("contamination", self.config.contamination)
        n_neighbors = kwargs.get("n_neighbors", self.config.n_neighbors)

        # Combine training and test data for LOF
        # This allows LOF to work in novelty detection mode
        combined_data = np.vstack([self._training_data, values])

        # Scale combined data
        combined_scaled = self._scaler.transform(combined_data)

        # Fit LOF on combined data
        self._model = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=contamination,
            algorithm=self.config.algorithm,
            leaf_size=self.config.leaf_size,
            metric=self.config.metric,
            p=self.config.p,
            novelty=False,  # We use combined data approach
            n_jobs=-1,
        )

        # Fit and predict
        self._model.fit_predict(combined_scaled)
        lof_scores = -self._model.negative_outlier_factor_

        # Extract scores for test data only
        test_scores = lof_scores[len(self._training_data) :]
        test_predictions = self._model.fit_predict(combined_scaled)[
            len(self._training_data) :
        ]

        # Normalize scores to 0-1 range
        min_score = np.min(lof_scores)
        max_score = np.max(lof_scores)
        score_range = max_score - min_score

        if score_range > 0:
            normalized_scores = (test_scores - min_score) / score_range
        else:
            normalized_scores = np.zeros_like(test_scores)

        # Find anomalies (predictions == -1 are anomalies)
        anomaly_mask = test_predictions == -1
        anomaly_indices = np.where(anomaly_mask)[0]

        # Calculate overall score and confidence
        if len(anomaly_indices) > 0:
            max_anomaly_score = float(np.max(normalized_scores[anomaly_indices]))
            confidence = min(
                self.config.sensitivity * (1 + max_anomaly_score),
                1.0,
            )
        else:
            max_anomaly_score = 0.0
            confidence = 1.0

        result = DetectionResult(
            is_anomaly=len(anomaly_indices) > 0,
            score=max_anomaly_score,
            confidence=confidence,
            indices=anomaly_indices,
            metadata={
                "lof_scores": test_scores[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "normalized_scores": normalized_scores[anomaly_indices].tolist()
                if len(anomaly_indices) > 0
                else [],
                "n_neighbors": n_neighbors,
                "contamination": contamination,
            },
        )

        # Create anomaly objects
        return self._create_anomalies(
            result=result,
            source_type=kwargs.get("source_type", "metric"),
            detection_method="lof",
            timestamps=timestamps,
        )

    def _prepare_data(
        self, data: np.ndarray | pd.Series | pd.DataFrame
    ) -> np.ndarray:
        """Prepare data for LOF.

        Args:
            data: Input data.

        Returns:
            2D numpy array suitable for sklearn.
        """
        if isinstance(data, pd.DataFrame):
            return data.to_numpy(dtype=np.float64)
        elif isinstance(data, pd.Series):
            return data.to_numpy(dtype=np.float64).reshape(-1, 1)
        elif isinstance(data, np.ndarray):
            if data.ndim == 1:
                return data.reshape(-1, 1).astype(np.float64)
            elif data.ndim == 2:
                return data.astype(np.float64)
            else:
                raise ValueError(f"Array must be 1D or 2D, got {data.ndim}D")
        else:
            raise ValueError(
                f"Data must be numpy array, pandas Series, or DataFrame, got {type(data)}"
            )
