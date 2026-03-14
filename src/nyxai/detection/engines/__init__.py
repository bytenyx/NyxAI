"""NyxAI Detection Engines.

This module contains various detection engine implementations.
"""

from nyxai.detection.engines.statistical_detector import EWMADetector, ThreeSigmaDetector

__all__ = [
    "ThreeSigmaDetector",
    "EWMADetector",
]
