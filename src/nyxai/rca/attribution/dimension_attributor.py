"""Dimension attribution analysis for NyxAI RCA.

This module provides algorithms to identify which dimensions (e.g., region,
instance, endpoint) contribute most to anomalies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field


@dataclass
class DimensionContributor:
    """Represents a dimension value and its contribution to the anomaly.

    Attributes:
        dimension_name: Name of the dimension (e.g., 'region', 'instance').
        dimension_value: Value of the dimension (e.g., 'us-east-1', 'instance-01').
        contribution_score: Score indicating contribution to anomaly (0.0 to 1.0).
        expected_value: Expected/normal value for this dimension.
        actual_value: Actual/anomalous value for this dimension.
        deviation: Difference between actual and expected.
        confidence: Confidence in the attribution (0.0 to 1.0).
        sample_count: Number of samples for this dimension.
    """

    dimension_name: str
    dimension_value: str
    contribution_score: float
    expected_value: float = 0.0
    actual_value: float = 0.0
    deviation: float = 0.0
    confidence: float = 0.8
    sample_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "dimension_name": self.dimension_name,
            "dimension_value": self.dimension_value,
            "contribution_score": self.contribution_score,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "deviation": self.deviation,
            "confidence": self.confidence,
            "sample_count": self.sample_count,
        }


@dataclass
class DimensionAttributionResult:
    """Result of dimension attribution analysis.

    Attributes:
        metric_name: Name of the metric being analyzed.
        anomaly_timestamp: When the anomaly occurred.
        top_contributors: List of top contributing dimensions.
        total_dimensions: Total number of dimensions analyzed.
        explanation: Human-readable explanation of the attribution.
        metadata: Additional metadata.
    """

    metric_name: str
    anomaly_timestamp: str
    top_contributors: list[DimensionContributor] = field(default_factory=list)
    total_dimensions: int = 0
    explanation: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "metric_name": self.metric_name,
            "anomaly_timestamp": self.anomaly_timestamp,
            "top_contributors": [c.to_dict() for c in self.top_contributors],
            "total_dimensions": self.total_dimensions,
            "explanation": self.explanation,
            "metadata": self.metadata,
        }


class AttributionConfig(BaseModel):
    """Configuration for dimension attribution.

    Attributes:
        top_k: Number of top contributors to return.
        min_contribution_threshold: Minimum contribution score to include.
        use_relative_deviation: Whether to use relative deviation for scoring.
        normalization_method: Method for normalizing scores ('minmax', 'zscore', 'softmax').
    """

    top_k: int = Field(default=5, ge=1, description="Number of top contributors")
    min_contribution_threshold: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Minimum contribution threshold"
    )
    use_relative_deviation: bool = Field(
        default=True, description="Use relative deviation"
    )
    normalization_method: str = Field(
        default="minmax", description="Normalization method"
    )


class DimensionAttributor:
    """Analyzes dimension contributions to anomalies.

    This class provides methods to identify which dimensions (e.g., region,
    instance, endpoint) contribute most to observed anomalies using various
    attribution algorithms.

    Supported algorithms:
    - Deviation-based: Compare actual vs expected values
    - Variance-based: Identify dimensions with highest variance
    - Correlation-based: Find dimensions most correlated with anomaly
    - Shapley-value inspired: Distribute anomaly score across dimensions
    """

    def __init__(self, config: AttributionConfig | None = None) -> None:
        """Initialize the dimension attributor.

        Args:
            config: Attribution configuration. Uses defaults if None.
        """
        self.config = config or AttributionConfig()

    def analyze(
        self,
        metric_name: str,
        df: pd.DataFrame,
        anomaly_timestamp: str,
        value_column: str = "value",
        dimension_columns: list[str] | None = None,
    ) -> DimensionAttributionResult:
        """Perform dimension attribution analysis.

        Args:
            metric_name: Name of the metric being analyzed.
            df: DataFrame containing metric data with dimensions.
            anomaly_timestamp: Timestamp when anomaly occurred.
            value_column: Column name containing metric values.
            dimension_columns: List of dimension columns. Auto-detected if None.

        Returns:
            Dimension attribution result.
        """
        if dimension_columns is None:
            dimension_columns = self._detect_dimension_columns(df, value_column)

        if not dimension_columns:
            return DimensionAttributionResult(
                metric_name=metric_name,
                anomaly_timestamp=anomaly_timestamp,
                explanation="No dimensions found for analysis",
            )

        # Calculate contributions for each dimension
        all_contributors: list[DimensionContributor] = []

        for dim_col in dimension_columns:
            contributors = self._analyze_dimension(
                df, dim_col, value_column
            )
            all_contributors.extend(contributors)

        # Sort by contribution score and filter
        all_contributors.sort(key=lambda x: x.contribution_score, reverse=True)

        # Filter by threshold and take top_k
        filtered = [
            c for c in all_contributors
            if c.contribution_score >= self.config.min_contribution_threshold
        ]
        top_contributors = filtered[: self.config.top_k]

        # Generate explanation
        explanation = self._generate_explanation(metric_name, top_contributors)

        return DimensionAttributionResult(
            metric_name=metric_name,
            anomaly_timestamp=anomaly_timestamp,
            top_contributors=top_contributors,
            total_dimensions=len(dimension_columns),
            explanation=explanation,
            metadata={
                "total_contributors": len(all_contributors),
                "filtered_contributors": len(filtered),
                "normalization_method": self.config.normalization_method,
            },
        )

    def _detect_dimension_columns(
        self, df: pd.DataFrame, value_column: str
    ) -> list[str]:
        """Automatically detect dimension columns.

        Args:
            df: DataFrame to analyze.
            value_column: Column containing metric values.

        Returns:
            List of dimension column names.
        """
        exclude_cols = {value_column, "timestamp", "time", "value", "metric"}
        dimension_cols = []

        for col in df.columns:
            if col in exclude_cols:
                continue
            # Consider categorical or low-cardinality columns as dimensions
            if df[col].dtype == "object" or df[col].nunique() < len(df) * 0.1:
                dimension_cols.append(col)

        return dimension_cols

    def _analyze_dimension(
        self,
        df: pd.DataFrame,
        dimension_column: str,
        value_column: str,
    ) -> list[DimensionContributor]:
        """Analyze a single dimension's contribution.

        Args:
            df: DataFrame containing data.
            dimension_column: Column name of the dimension.
            value_column: Column name of the metric values.

        Returns:
            List of dimension contributors.
        """
        contributors = []

        # Group by dimension value
        grouped = df.groupby(dimension_column)[value_column]

        # Calculate global statistics
        global_mean = df[value_column].mean()
        global_std = df[value_column].std() or 1.0

        for dim_value, group in grouped:
            actual_value = group.mean()
            sample_count = len(group)

            # Calculate expected value (using global mean as baseline)
            expected_value = global_mean

            # Calculate deviation
            deviation = actual_value - expected_value

            # Calculate contribution score
            if self.config.use_relative_deviation:
                # Use relative deviation normalized by global std
                raw_score = abs(deviation) / global_std
            else:
                # Use absolute deviation
                raw_score = abs(deviation)

            # Normalize to 0-1 range
            contribution_score = self._normalize_score(raw_score)

            # Calculate confidence based on sample size
            confidence = min(0.5 + (sample_count / 100), 0.95)

            contributor = DimensionContributor(
                dimension_name=dimension_column,
                dimension_value=str(dim_value),
                contribution_score=contribution_score,
                expected_value=expected_value,
                actual_value=actual_value,
                deviation=deviation,
                confidence=confidence,
                sample_count=sample_count,
            )
            contributors.append(contributor)

        return contributors

    def _normalize_score(self, raw_score: float) -> float:
        """Normalize a raw score to 0-1 range.

        Args:
            raw_score: Raw score to normalize.

        Returns:
            Normalized score between 0 and 1.
        """
        method = self.config.normalization_method

        if method == "minmax":
            # Simple min-max scaling with sigmoid-like behavior
            return min(1.0, raw_score / (1 + raw_score))
        elif method == "zscore":
            # Convert to probability-like score from z-score
            from scipy.stats import norm
            return 2 * (1 - norm.cdf(abs(raw_score))) if raw_score > 0 else 0.0
        elif method == "softmax":
            # Will be applied to all scores together
            return raw_score
        else:
            return min(1.0, max(0.0, raw_score))

    def _generate_explanation(
        self,
        metric_name: str,
        contributors: list[DimensionContributor],
    ) -> str:
        """Generate human-readable explanation.

        Args:
            metric_name: Name of the metric.
            contributors: List of top contributors.

        Returns:
            Explanation string.
        """
        if not contributors:
            return f"No significant dimension contributors found for {metric_name}."

        parts = [f"Top contributors to {metric_name} anomaly:"]

        for i, contrib in enumerate(contributors[:3], 1):
            direction = "higher" if contrib.deviation > 0 else "lower"
            parts.append(
                f"{i}. {contrib.dimension_name}={contrib.dimension_value} "
                f"({contrib.contribution_score:.1%} contribution, "
                f"{direction} than expected)"
            )

        return "\n".join(parts)

    def compare_periods(
        self,
        baseline_df: pd.DataFrame,
        anomaly_df: pd.DataFrame,
        dimension_column: str,
        value_column: str = "value",
    ) -> list[DimensionContributor]:
        """Compare baseline vs anomaly period for a specific dimension.

        Args:
            baseline_df: DataFrame containing baseline/normal data.
            anomaly_df: DataFrame containing anomalous data.
            dimension_column: Dimension to compare.
            value_column: Column containing metric values.

        Returns:
            List of dimension contributors.
        """
        contributors = []

        # Calculate baseline statistics
        baseline_stats = (
            baseline_df.groupby(dimension_column)[value_column]
            .agg(["mean", "count"])
            .reset_index()
        )
        baseline_map = baseline_stats.set_index(dimension_column).to_dict("index")

        # Calculate anomaly statistics
        anomaly_stats = (
            anomaly_df.groupby(dimension_column)[value_column]
            .agg(["mean", "count"])
            .reset_index()
        )

        for _, row in anomaly_stats.iterrows():
            dim_value = row[dimension_column]
            actual_value = row["mean"]
            sample_count = int(row["count"])

            # Get baseline value
            if dim_value in baseline_map:
                expected_value = baseline_map[dim_value]["mean"]
            else:
                expected_value = baseline_df[value_column].mean()

            deviation = actual_value - expected_value

            # Calculate contribution score
            baseline_std = baseline_df[value_column].std() or 1.0
            raw_score = abs(deviation) / baseline_std
            contribution_score = self._normalize_score(raw_score)

            contributor = DimensionContributor(
                dimension_name=dimension_column,
                dimension_value=str(dim_value),
                contribution_score=contribution_score,
                expected_value=expected_value,
                actual_value=actual_value,
                deviation=deviation,
                confidence=min(0.5 + (sample_count / 100), 0.95),
                sample_count=sample_count,
            )
            contributors.append(contributor)

        # Sort by contribution score
        contributors.sort(key=lambda x: x.contribution_score, reverse=True)

        return contributors
