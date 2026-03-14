"""Monitoring skills for MonitorAgent.

This module provides skills for the Monitor Agent to perform
metrics collection and anomaly detection tasks.
"""

from __future__ import annotations

from nyxai.skills.builtin.monitoring.metric_collection import MetricCollectionSkill
from nyxai.skills.builtin.monitoring.anomaly_detection import AnomalyDetectionSkill

__all__ = [
    "MetricCollectionSkill",
    "AnomalyDetectionSkill",
]
