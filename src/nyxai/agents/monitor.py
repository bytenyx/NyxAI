"""Monitor Agent for NyxAI.

This module implements the Monitor Agent that continuously monitors
metrics and detects anomalies.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.agents.base import Agent, AgentConfig, AgentContext, AgentResult, AgentRole
from nyxai.detection.base import BaseDetector
from nyxai.detection.models.anomaly import Anomaly


class MonitorAgentConfig(AgentConfig):
    """Configuration for Monitor Agent.

    Attributes:
        detection_interval_seconds: Interval between detection runs.
        min_anomaly_score: Minimum score to report as anomaly.
        batch_size: Number of data points to process in batch.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "MonitorAgent"
        self.role = AgentRole.MONITOR
        self.description = "Monitors metrics and detects anomalies"
        self.detection_interval_seconds = 60.0
        self.min_anomaly_score = 0.7
        self.batch_size = 100


class MonitorAgent(Agent):
    """Agent responsible for monitoring and anomaly detection.

    This agent continuously monitors metrics using configured detectors
    and triggers anomaly detection workflows.

    Attributes:
        config: Monitor agent configuration.
        _detectors: List of anomaly detectors.
        _last_detection_time: Timestamp of last detection run.
    """

    def __init__(
        self,
        detectors: list[BaseDetector[Any]],
        config: MonitorAgentConfig | None = None,
    ) -> None:
        """Initialize the monitor agent.

        Args:
            detectors: List of anomaly detectors to use.
            config: Agent configuration. Uses defaults if None.
        """
        super().__init__(config or MonitorAgentConfig())
        self.monitor_config = config or MonitorAgentConfig()
        self._detectors = detectors
        self._last_detection_time: float = 0.0

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute monitoring and anomaly detection.

        Args:
            context: Execution context.

        Returns:
            Agent execution result.
        """
        start_time = time.time()
        self._set_status(self.get_status().RUNNING)

        try:
            # Check if we can execute
            if not self.can_execute(context):
                return AgentResult.failure_result(
                    error="Agent cannot execute with current context",
                    agent_name=self.get_name(),
                )

            # Get metrics data from context
            metrics_data = context.anomaly_data.get("metrics_data", [])
            service_id = context.anomaly_data.get("service_id", "unknown")

            if not metrics_data:
                return AgentResult.success_result(
                    data={"message": "No metrics data to process", "anomalies_detected": 0},
                    agent_name=self.get_name(),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Run detection with all enabled detectors
            all_anomalies: list[Anomaly] = []
            detection_results = []

            for detector in self._detectors:
                if not detector.is_enabled():
                    continue

                try:
                    anomalies = detector.detect(
                        metrics_data,
                        source_type="metric",
                    )

                    # Filter by minimum score
                    filtered_anomalies = [
                        a for a in anomalies
                        if a.score >= self.monitor_config.min_anomaly_score
                    ]

                    all_anomalies.extend(filtered_anomalies)
                    detection_results.append({
                        "detector": detector.__class__.__name__,
                        "anomalies_found": len(filtered_anomalies),
                    })

                except Exception as e:
                    detection_results.append({
                        "detector": detector.__class__.__name__,
                        "error": str(e),
                    })

            # Update context with detected anomalies
            if all_anomalies:
                context.update(
                    anomaly_data={
                        **context.anomaly_data,
                        "detected_anomalies": [a.to_dict() for a in all_anomalies],
                        "service_id": service_id,
                        "detection_timestamp": time.time(),
                    }
                )

            self._last_detection_time = time.time()
            self._set_status(self.get_status().SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            return AgentResult.success_result(
                data={
                    "anomalies_detected": len(all_anomalies),
                    "detection_results": detection_results,
                    "service_id": service_id,
                },
                agent_name=self.get_name(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(self.get_status().FAILED)
            return AgentResult.failure_result(
                error=f"Monitor agent failed: {str(e)}",
                agent_name=self.get_name(),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def add_detector(self, detector: BaseDetector[Any]) -> None:
        """Add a detector to the agent.

        Args:
            detector: Detector to add.
        """
        self._detectors.append(detector)

    def remove_detector(self, detector_class: str) -> bool:
        """Remove a detector by class name.

        Args:
            detector_class: Class name of detector to remove.

        Returns:
            True if removed, False if not found.
        """
        for i, detector in enumerate(self._detectors):
            if detector.__class__.__name__ == detector_class:
                self._detectors.pop(i)
                return True
        return False

    def get_detector_info(self) -> list[dict[str, Any]]:
        """Get information about configured detectors.

        Returns:
            List of detector information.
        """
        return [
            {
                "name": d.__class__.__name__,
                "enabled": d.is_enabled(),
            }
            for d in self._detectors
        ]

    def get_last_detection_time(self) -> float:
        """Get timestamp of last detection run.

        Returns:
            Timestamp in seconds since epoch.
        """
        return self._last_detection_time
