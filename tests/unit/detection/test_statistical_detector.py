"""Unit tests for statistical detectors."""

from __future__ import annotations

import numpy as np
import pytest

from nyxai.detection.engines.statistical_detector import (
    EWMADetector,
    EWMADetectorConfig,
    ThreeSigmaDetector,
    ThreeSigmaConfig,
)


class TestThreeSigmaDetector:
    """Tests for ThreeSigmaDetector."""

    def test_initialization_default_config(self):
        """Test detector initialization with default config."""
        detector = ThreeSigmaDetector()
        assert detector.config.sigma_multiplier == 3.0
        assert detector.config.min_anomaly_score == 0.5
        assert detector.config.sensitivity == 0.8

    def test_initialization_custom_config(self):
        """Test detector initialization with custom config."""
        config = ThreeSigmaConfig(sigma_multiplier=2.5, min_anomaly_score=0.6)
        detector = ThreeSigmaDetector(config)
        assert detector.config.sigma_multiplier == 2.5
        assert detector.config.min_anomaly_score == 0.6

    def test_fit_with_valid_data(self, sample_metric_data):
        """Test fitting with valid data."""
        detector = ThreeSigmaDetector()
        result = detector.fit(sample_metric_data)
        assert result is detector  # Returns self for chaining
        assert detector._mean is not None
        assert detector._std is not None

    def test_fit_with_insufficient_data(self):
        """Test fitting with insufficient data."""
        detector = ThreeSigmaDetector()
        with pytest.raises(ValueError, match="Data must have at least 2 points"):
            detector.fit(np.array([1.0]))

    def test_fit_with_constant_data(self):
        """Test fitting with constant data."""
        detector = ThreeSigmaDetector()
        constant_data = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        detector.fit(constant_data)
        # Should handle zero std gracefully
        assert detector._std == 0.0

    def test_detect_without_fit(self, sample_metric_data):
        """Test detection without fitting."""
        detector = ThreeSigmaDetector()
        with pytest.raises(ValueError, match="Detector must be fitted"):
            detector.detect(sample_metric_data)

    def test_detect_no_anomalies(self, sample_metric_data):
        """Test detection with no anomalies."""
        detector = ThreeSigmaDetector()
        detector.fit(sample_metric_data)
        anomalies = detector.detect(sample_metric_data)
        # Normal data should have few or no anomalies
        assert len(anomalies) == 0

    def test_detect_with_anomalies(self, sample_metric_data_with_anomaly):
        """Test detection with anomalies."""
        detector = ThreeSigmaDetector()
        detector.fit(sample_metric_data_with_anomaly)
        anomalies = detector.detect(sample_metric_data_with_anomaly)
        # Should detect the injected anomalies
        assert len(anomalies) > 0

    def test_detect_disabled_detector(self, sample_metric_data):
        """Test detection with disabled detector."""
        config = ThreeSigmaConfig(enabled=False)
        detector = ThreeSigmaDetector(config)
        detector.fit(sample_metric_data)
        anomalies = detector.detect(sample_metric_data)
        assert len(anomalies) == 0

    def test_is_enabled(self):
        """Test is_enabled method."""
        detector = ThreeSigmaDetector()
        assert detector.is_enabled() is True

        detector.config.enabled = False
        assert detector.is_enabled() is False


class TestEWMADetector:
    """Tests for EWMADetector."""

    def test_initialization_default_config(self):
        """Test detector initialization with default config."""
        detector = EWMADetector()
        assert detector.config.alpha == 0.3
        assert detector.config.sigma_multiplier == 3.0

    def test_initialization_custom_config(self):
        """Test detector initialization with custom config."""
        config = EWMADetectorConfig(alpha=0.5, sigma_multiplier=2.0)
        detector = EWMADetector(config)
        assert detector.config.alpha == 0.5
        assert detector.config.sigma_multiplier == 2.0

    def test_fit_with_valid_data(self, sample_metric_data):
        """Test fitting with valid data."""
        detector = EWMADetector()
        result = detector.fit(sample_metric_data)
        assert result is detector
        assert detector._ewma_mean is not None
        assert detector._ewma_std is not None

    def test_fit_with_insufficient_data(self):
        """Test fitting with insufficient data."""
        detector = EWMADetector()
        with pytest.raises(ValueError, match="Data must have at least 10 points"):
            detector.fit(np.array([1.0, 2.0, 3.0]))

    def test_detect_with_anomalies(self, sample_metric_data_with_anomaly):
        """Test detection with anomalies."""
        detector = EWMADetector()
        detector.fit(sample_metric_data_with_anomaly)
        anomalies = detector.detect(sample_metric_data_with_anomaly)
        assert len(anomalies) > 0

    def test_detect_with_timestamps(self, sample_metric_data_with_anomaly):
        """Test detection with timestamps."""
        import pandas as pd

        detector = EWMADetector()
        detector.fit(sample_metric_data_with_anomaly)
        timestamps = pd.date_range(
            start="2024-01-01", periods=len(sample_metric_data_with_anomaly), freq="1min"
        )
        anomalies = detector.detect(sample_metric_data_with_anomaly, timestamps=timestamps)

        for anomaly in anomalies:
            assert anomaly.timestamp is not None

    def test_alpha_validation(self):
        """Test alpha parameter validation."""
        with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
            EWMADetectorConfig(alpha=1.5)

        with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
            EWMADetectorConfig(alpha=-0.1)

    def test_validate_data_with_valid_input(self):
        """Test _validate_data with valid input."""
        detector = EWMADetector()
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = detector.validate_data(data)
        assert isinstance(result, np.ndarray)
        assert len(result) == 5

    def test_validate_data_with_nan(self):
        """Test _validate_data with NaN values."""
        detector = EWMADetector()
        data = np.array([1.0, np.nan, 3.0, np.nan, 5.0])
        result = detector.validate_data(data)
        assert len(result) == 3  # NaN values should be removed
