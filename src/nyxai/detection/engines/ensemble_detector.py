"""Ensemble anomaly detectors for NyxAI.

This module implements ensemble methods that combine multiple detectors:
- VotingEnsemble: Majority voting across multiple detectors
- WeightedEnsemble: Weighted combination of detector scores
- StackingEnsemble: Meta-learner based ensemble
"""

from __future__ import annotations

from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from pydantic import Field, field_validator

from nyxai.detection.base import BaseDetector, DetectionResult, DetectorConfig
from nyxai.detection.models.anomaly import Anomaly


class EnsembleStrategy(str, Enum):
    """Ensemble combination strategies."""

    VOTING = "voting"
    WEIGHTED = "weighted"
    UNION = "union"
    INTERSECTION = "intersection"


class EnsembleConfig(DetectorConfig):
    """Configuration for Ensemble detector.

    Attributes:
        strategy: Ensemble combination strategy.
        weights: Weights for each detector (for weighted strategy).
        min_detectors: Minimum number of detectors that must flag anomaly.
        score_aggregation: How to aggregate scores ('mean', 'max', 'min').
    """

    strategy: EnsembleStrategy = Field(
        default=EnsembleStrategy.VOTING,
        description="Ensemble combination strategy",
    )
    weights: list[float] | None = Field(
        default=None,
        description="Weights for each detector (for weighted strategy)",
    )
    min_detectors: int = Field(
        default=2,
        ge=1,
        description="Minimum detectors that must flag anomaly",
    )
    score_aggregation: str = Field(
        default="mean",
        description="Score aggregation method: 'mean', 'max', 'min'",
    )

    @field_validator("score_aggregation")
    @classmethod
    def validate_aggregation(cls, v: str) -> str:
        """Validate aggregation method."""
        if v not in ("mean", "max", "min"):
            raise ValueError("score_aggregation must be 'mean', 'max', or 'min'")
        return v


class EnsembleDetector(BaseDetector[EnsembleConfig]):
    """Ensemble anomaly detector that combines multiple detectors.

    This detector aggregates results from multiple base detectors using
    various strategies:
    - VOTING: Anomaly if majority of detectors agree
    - WEIGHTED: Weighted combination of detector scores
    - UNION: Anomaly if any detector flags it
    - INTERSECTION: Anomaly only if all detectors flag it

    Attributes:
        config: EnsembleConfig instance.
        _detectors: List of base detectors.
    """

    def __init__(
        self,
        detectors: list[BaseDetector[Any]],
        config: EnsembleConfig | None = None,
    ) -> None:
        """Initialize the Ensemble detector.

        Args:
            detectors: List of base detectors to ensemble.
            config: Configuration for the detector. Uses defaults if None.

        Raises:
            ValueError: If detectors list is empty.
        """
        super().__init__(config or EnsembleConfig())

        if not detectors:
            raise ValueError("At least one detector is required for ensemble")

        self._detectors: list[BaseDetector[Any]] = detectors

        # Validate weights if provided
        if self.config.weights is not None:
            if len(self.config.weights) != len(detectors):
                raise ValueError(
                    f"Number of weights ({len(self.config.weights)}) must match "
                    f"number of detectors ({len(detectors)})"
                )
            if not all(w >= 0 for w in self.config.weights):
                raise ValueError("All weights must be non-negative")
            if sum(self.config.weights) == 0:
                raise ValueError("Sum of weights must be greater than 0")

    def fit(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        **kwargs: Any,
    ) -> EnsembleDetector:
        """Fit all base detectors to training data.

        Args:
            data: Training data.
            **kwargs: Additional parameters passed to each detector.

        Returns:
            Self for method chaining.
        """
        for detector in self._detectors:
            if hasattr(detector, "fit"):
                detector.fit(data, **kwargs)

        return self

    def detect(
        self,
        data: np.ndarray | pd.Series | pd.DataFrame,
        timestamps: pd.DatetimeIndex | None = None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Detect anomalies using ensemble of detectors.

        Args:
            data: Input data to analyze.
            timestamps: Optional timestamps for data points.
            **kwargs: Additional parameters passed to each detector.

        Returns:
            List of detected anomalies.
        """
        if not self.is_enabled():
            return []

        # Collect results from all detectors
        all_results: list[list[Anomaly]] = []
        for detector in self._detectors:
            if detector.is_enabled():
                try:
                    results = detector.detect(data, timestamps, **kwargs)
                    all_results.append(results)
                except Exception:
                    # Skip detectors that fail
                    all_results.append([])
            else:
                all_results.append([])

        # Combine results based on strategy
        if self.config.strategy == EnsembleStrategy.VOTING:
            return self._voting_ensemble(all_results, timestamps, **kwargs)
        elif self.config.strategy == EnsembleStrategy.WEIGHTED:
            return self._weighted_ensemble(all_results, timestamps, **kwargs)
        elif self.config.strategy == EnsembleStrategy.UNION:
            return self._union_ensemble(all_results, timestamps, **kwargs)
        elif self.config.strategy == EnsembleStrategy.INTERSECTION:
            return self._intersection_ensemble(all_results, timestamps, **kwargs)
        else:
            return self._voting_ensemble(all_results, timestamps, **kwargs)

    def _voting_ensemble(
        self,
        all_results: list[list[Anomaly]],
        timestamps: pd.DatetimeIndex | None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Combine results using majority voting.

        Args:
            all_results: Results from each detector.
            timestamps: Optional timestamps.
            **kwargs: Additional parameters.

        Returns:
            Combined list of anomalies.
        """
        # Build anomaly index sets for each detector
        anomaly_sets: list[set[int]] = []
        detector_scores: dict[int, list[tuple[float, float]]] = {}

        for detector_idx, anomalies in enumerate(all_results):
            indices = set()
            for anomaly in anomalies:
                if anomaly.metadata and "index" in anomaly.metadata:
                    idx = anomaly.metadata["index"]
                    indices.add(idx)
                    if idx not in detector_scores:
                        detector_scores[idx] = []
                    detector_scores[idx].append(
                        (anomaly.score, anomaly.confidence)
                    )
            anomaly_sets.append(indices)

        # Find indices that meet voting criteria
        n_detectors = len([s for s in anomaly_sets if s])  # Non-empty sets
        if n_detectors == 0:
            return []

        # Count votes for each index
        all_indices: set[int] = set()
        for s in anomaly_sets:
            all_indices.update(s)

        voted_indices = []
        for idx in all_indices:
            votes = sum(1 for s in anomaly_sets if idx in s)
            if votes >= min(self.config.min_detectors, n_detectors):
                voted_indices.append(idx)

        if not voted_indices:
            return []

        # Create ensemble anomalies
        anomalies = []
        for idx in sorted(voted_indices):
            scores_and_conf = detector_scores.get(idx, [(0.5, 0.5)])
            scores = [s for s, _ in scores_and_conf]
            confidences = [c for _, c in scores_and_conf]

            # Aggregate scores
            if self.config.score_aggregation == "mean":
                agg_score = float(np.mean(scores))
                agg_confidence = float(np.mean(confidences))
            elif self.config.score_aggregation == "max":
                agg_score = float(np.max(scores))
                agg_confidence = float(np.max(confidences))
            else:  # min
                agg_score = float(np.min(scores))
                agg_confidence = float(np.min(confidences))

            timestamp = timestamps[idx] if timestamps is not None else None

            anomaly = Anomaly.create(
                title=f"Ensemble anomaly at index {idx}",
                description=f"Anomaly detected by ensemble voting "
                f"({len(scores)} detectors)",
                severity=Anomaly.from_score(agg_score),
                source_type=kwargs.get("source_type", "metric"),
                detection_method="ensemble_voting",
                score=agg_score,
                confidence=agg_confidence,
                timestamp=timestamp,
                metadata={
                    "index": idx,
                    "detector_count": len(scores),
                    "individual_scores": scores,
                },
            )
            anomalies.append(anomaly)

        return anomalies

    def _weighted_ensemble(
        self,
        all_results: list[list[Anomaly]],
        timestamps: pd.DatetimeIndex | None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Combine results using weighted scores.

        Args:
            all_results: Results from each detector.
            timestamps: Optional timestamps.
            **kwargs: Additional parameters.

        Returns:
            Combined list of anomalies.
        """
        # Use equal weights if not provided
        weights = self.config.weights or [1.0] * len(all_results)
        weight_sum = sum(weights)
        normalized_weights = [w / weight_sum for w in weights]

        # Collect all unique indices and their weighted scores
        index_scores: dict[int, float] = {}
        index_confidences: dict[int, float] = {}
        index_detectors: dict[int, list[int]] = {}

        for detector_idx, (anomalies, weight) in enumerate(
            zip(all_results, normalized_weights)
        ):
            for anomaly in anomalies:
                if anomaly.metadata and "index" in anomaly.metadata:
                    idx = anomaly.metadata["index"]

                    if idx not in index_scores:
                        index_scores[idx] = 0.0
                        index_confidences[idx] = 0.0
                        index_detectors[idx] = []

                    index_scores[idx] += anomaly.score * weight
                    index_confidences[idx] += anomaly.confidence * weight
                    index_detectors[idx].append(detector_idx)

        # Filter by threshold
        threshold = self.config.min_anomaly_score
        selected_indices = [
            idx for idx, score in index_scores.items() if score >= threshold
        ]

        if not selected_indices:
            return []

        # Create ensemble anomalies
        anomalies = []
        for idx in sorted(selected_indices):
            timestamp = timestamps[idx] if timestamps is not None else None

            anomaly = Anomaly.create(
                title=f"Weighted ensemble anomaly at index {idx}",
                description=f"Anomaly detected by weighted ensemble",
                severity=Anomaly.from_score(index_scores[idx]),
                source_type=kwargs.get("source_type", "metric"),
                detection_method="ensemble_weighted",
                score=index_scores[idx],
                confidence=index_confidences[idx],
                timestamp=timestamp,
                metadata={
                    "index": idx,
                    "detectors": index_detectors[idx],
                    "weights": [normalized_weights[d] for d in index_detectors[idx]],
                },
            )
            anomalies.append(anomaly)

        return anomalies

    def _union_ensemble(
        self,
        all_results: list[list[Anomaly]],
        timestamps: pd.DatetimeIndex | None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Combine results using union (any detector flags anomaly).

        Args:
            all_results: Results from each detector.
            timestamps: Optional timestamps.
            **kwargs: Additional parameters.

        Returns:
            Combined list of anomalies.
        """
        # Collect all unique anomalies by index
        index_anomalies: dict[int, Anomaly] = {}

        for anomalies in all_results:
            for anomaly in anomalies:
                if anomaly.metadata and "index" in anomaly.metadata:
                    idx = anomaly.metadata["index"]
                    if idx not in index_anomalies:
                        index_anomalies[idx] = anomaly
                    else:
                        # Keep the one with higher score
                        if anomaly.score > index_anomalies[idx].score:
                            index_anomalies[idx] = anomaly

        return list(index_anomalies.values())

    def _intersection_ensemble(
        self,
        all_results: list[list[Anomaly]],
        timestamps: pd.DatetimeIndex | None,
        **kwargs: Any,
    ) -> list[Anomaly]:
        """Combine results using intersection (all detectors must flag).

        Args:
            all_results: Results from each detector.
            timestamps: Optional timestamps.
            **kwargs: Additional parameters.

        Returns:
            Combined list of anomalies.
        """
        # Build anomaly index sets
        anomaly_sets: list[set[int]] = []
        detector_scores: dict[int, list[tuple[float, float]]] = {}

        for detector_idx, anomalies in enumerate(all_results):
            indices = set()
            for anomaly in anomalies:
                if anomaly.metadata and "index" in anomaly.metadata:
                    idx = anomaly.metadata["index"]
                    indices.add(idx)
                    if idx not in detector_scores:
                        detector_scores[idx] = []
                    detector_scores[idx].append(
                        (anomaly.score, anomaly.confidence)
                    )
            anomaly_sets.append(indices)

        # Find intersection
        if not anomaly_sets:
            return []

        intersection = anomaly_sets[0].copy()
        for s in anomaly_sets[1:]:
            intersection &= s

        # Create anomalies from intersection
        anomalies = []
        for idx in sorted(intersection):
            scores_and_conf = detector_scores.get(idx, [(0.5, 0.5)])
            scores = [s for s, _ in scores_and_conf]
            confidences = [c for _, c in scores_and_conf]

            timestamp = timestamps[idx] if timestamps is not None else None

            anomaly = Anomaly.create(
                title=f"Intersection ensemble anomaly at index {idx}",
                description=f"Anomaly detected by all detectors",
                severity=Anomaly.from_score(float(np.mean(scores))),
                source_type=kwargs.get("source_type", "metric"),
                detection_method="ensemble_intersection",
                score=float(np.mean(scores)),
                confidence=float(np.mean(confidences)),
                timestamp=timestamp,
                metadata={
                    "index": idx,
                    "detector_count": len(scores),
                    "individual_scores": scores,
                },
            )
            anomalies.append(anomaly)

        return anomalies

    def get_detector_info(self) -> list[dict[str, Any]]:
        """Get information about base detectors.

        Returns:
            List of detector information dictionaries.
        """
        return [
            {
                "name": type(d).__name__,
                "enabled": d.is_enabled(),
            }
            for d in self._detectors
        ]
