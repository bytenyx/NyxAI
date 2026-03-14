"""NyxAI Detection Module.

This module provides anomaly detection capabilities including statistical
detectors, ML-based detectors, and rule-based detectors.
"""

from nyxai.detection.base import BaseDetector, DetectionResult, DetectorConfig
from nyxai.detection.engines.statistical_detector import (
    EWMAConfig,
    EWMADetector,
    ThreeSigmaConfig,
    ThreeSigmaDetector,
)
from nyxai.detection.models.anomaly import Anomaly, AnomalySeverity, AnomalyStatus

__all__ = [
    "BaseDetector",
    "DetectorConfig",
    "DetectionResult",
    "Anomaly",
    "AnomalySeverity",
    "AnomalyStatus",
    "ThreeSigmaDetector",
    "ThreeSigmaConfig",
    "EWMADetector",
    "EWMAConfig",
]
