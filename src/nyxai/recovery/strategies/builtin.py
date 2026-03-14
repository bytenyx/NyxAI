"""Built-in recovery strategies.

This module provides common recovery strategy implementations.
"""

from __future__ import annotations

import uuid
from typing import Any

from nyxai.recovery.strategies.base import (
    ActionType,
    RecoveryAction,
    RecoveryStrategy,
    RiskLevel,
    StrategyConfig,
)


class RestartServiceConfig(StrategyConfig):
    """Configuration for restart service strategy."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "RestartServiceStrategy"
        self.description = "Restart the affected service"
        self.priority = 80


class RestartServiceStrategy(RecoveryStrategy):
    """Strategy to restart a service.

    This strategy is suitable for:
    - Memory leaks
    - Deadlocks
    - Resource exhaustion
    - Unknown/unclassified errors
    """

    def __init__(self, config: RestartServiceConfig | None = None) -> None:
        super().__init__(config or RestartServiceConfig())

    def can_handle(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> bool:
        """Check if this strategy can handle the anomaly.

        Can handle memory, deadlock, and unknown errors.
        """
        handleable_types = {
            "memory_leak",
            "deadlock",
            "resource_exhaustion",
            "high_memory_usage",
            "unhealthy",
            "unknown",
        }
        return anomaly_type.lower() in handleable_types

    def create_action(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> RecoveryAction | None:
        """Create a restart action."""
        return RecoveryAction(
            id=str(uuid.uuid4()),
            action_type=ActionType.RESTART,
            target=service_id,
            parameters={
                "graceful": True,
                "timeout": 30,
                "reason": anomaly_type,
            },
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=60.0,
            requires_approval=False,
            metadata={
                "strategy": self.get_name(),
                "anomaly_type": anomaly_type,
            },
        )


class ScaleUpConfig(StrategyConfig):
    """Configuration for scale up strategy."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "ScaleUpStrategy"
        self.description = "Scale up the service to handle load"
        self.priority = 70
        self.scale_factor = 2


class ScaleUpStrategy(RecoveryStrategy):
    """Strategy to scale up a service.

    This strategy is suitable for:
    - High CPU usage
    - High latency
    - High request rate
    - Resource saturation
    """

    def __init__(self, config: ScaleUpConfig | None = None) -> None:
        self.scale_config = config or ScaleUpConfig()
        super().__init__(self.scale_config)

    def can_handle(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> bool:
        """Check if this strategy can handle the anomaly.

        Can handle high load and resource saturation.
        """
        handleable_types = {
            "high_cpu",
            "high_latency",
            "high_request_rate",
            "resource_saturation",
            "cpu_throttling",
            "load_spike",
        }
        return anomaly_type.lower() in handleable_types

    def create_action(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> RecoveryAction | None:
        """Create a scale up action."""
        current_replicas = context.get("current_replicas", 1)
        scale_factor = getattr(self.scale_config, "scale_factor", 2)
        new_replicas = current_replicas * scale_factor

        return RecoveryAction(
            id=str(uuid.uuid4()),
            action_type=ActionType.SCALE,
            target=service_id,
            parameters={
                "current_replicas": current_replicas,
                "target_replicas": new_replicas,
                "scale_factor": scale_factor,
                "reason": anomaly_type,
            },
            risk_level=RiskLevel.LOW,
            estimated_duration=120.0,
            requires_approval=False,
            metadata={
                "strategy": self.get_name(),
                "anomaly_type": anomaly_type,
            },
        )


class ClearCacheConfig(StrategyConfig):
    """Configuration for clear cache strategy."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "ClearCacheStrategy"
        self.description = "Clear service cache"
        self.priority = 60


class ClearCacheStrategy(RecoveryStrategy):
    """Strategy to clear service cache.

    This strategy is suitable for:
    - Cache inconsistency
    - Stale cache data
    - Cache memory issues
    """

    def __init__(self, config: ClearCacheConfig | None = None) -> None:
        super().__init__(config or ClearCacheConfig())

    def can_handle(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> bool:
        """Check if this strategy can handle the anomaly.

        Can handle cache-related issues.
        """
        handleable_types = {
            "cache_inconsistency",
            "stale_cache",
            "cache_memory_issue",
            "cache_corruption",
        }
        return anomaly_type.lower() in handleable_types

    def create_action(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> RecoveryAction | None:
        """Create a clear cache action."""
        cache_type = context.get("cache_type", "redis")

        return RecoveryAction(
            id=str(uuid.uuid4()),
            action_type=ActionType.CLEAR_CACHE,
            target=service_id,
            parameters={
                "cache_type": cache_type,
                "pattern": "*",  # Clear all by default
                "reason": anomaly_type,
            },
            risk_level=RiskLevel.LOW,
            estimated_duration=10.0,
            requires_approval=False,
            metadata={
                "strategy": self.get_name(),
                "anomaly_type": anomaly_type,
            },
        )


class CircuitBreakerConfig(StrategyConfig):
    """Configuration for circuit breaker strategy."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "CircuitBreakerStrategy"
        self.description = "Enable circuit breaker for failing dependencies"
        self.priority = 75


class CircuitBreakerStrategy(RecoveryStrategy):
    """Strategy to enable circuit breaker.

    This strategy is suitable for:
    - Cascading failures
    - Dependency failures
    - Timeout storms
    """

    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        super().__init__(config or CircuitBreakerConfig())

    def can_handle(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> bool:
        """Check if this strategy can handle the anomaly.

        Can handle cascading and dependency failures.
        """
        handleable_types = {
            "cascading_failure",
            "dependency_failure",
            "timeout_storm",
            "retry_storm",
            "circuit_open",
        }
        return anomaly_type.lower() in handleable_types

    def create_action(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> RecoveryAction | None:
        """Create a circuit breaker action."""
        dependency = context.get("failed_dependency", "unknown")

        return RecoveryAction(
            id=str(uuid.uuid4()),
            action_type=ActionType.CIRCUIT_BREAKER,
            target=service_id,
            parameters={
                "dependency": dependency,
                "threshold": 5,
                "timeout": 30,
                "half_open_requests": 3,
                "reason": anomaly_type,
            },
            risk_level=RiskLevel.MEDIUM,
            estimated_duration=30.0,
            requires_approval=True,  # Requires approval as it affects traffic
            metadata={
                "strategy": self.get_name(),
                "anomaly_type": anomaly_type,
            },
        )
