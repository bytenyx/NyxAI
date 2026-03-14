"""Strategy manager for recovery actions.

This module provides the StrategyManager class that manages
recovery strategies and matches them to anomalies.
"""

from __future__ import annotations

import uuid
from typing import Any

from nyxai.recovery.strategies.base import RecoveryAction, RecoveryStrategy


class StrategyManager:
    """Manages recovery strategies and matches them to anomalies.

    This class maintains a registry of recovery strategies and provides
    methods to find appropriate strategies for given anomalies.

    Attributes:
        _strategies: List of registered strategies.
    """

    def __init__(self) -> None:
        """Initialize the strategy manager."""
        self._strategies: list[RecoveryStrategy] = []

    def register(self, strategy: RecoveryStrategy) -> None:
        """Register a recovery strategy.

        Args:
            strategy: Strategy to register.
        """
        self._strategies.append(strategy)
        # Sort by priority (descending)
        self._strategies.sort(key=lambda s: s.get_priority(), reverse=True)

    def unregister(self, strategy_name: str) -> bool:
        """Unregister a recovery strategy by name.

        Args:
            strategy_name: Name of the strategy to unregister.

        Returns:
            True if strategy was found and removed.
        """
        for i, strategy in enumerate(self._strategies):
            if strategy.get_name() == strategy_name:
                self._strategies.pop(i)
                return True
        return False

    def get_strategies(
        self,
        enabled_only: bool = True,
    ) -> list[RecoveryStrategy]:
        """Get all registered strategies.

        Args:
            enabled_only: If True, return only enabled strategies.

        Returns:
            List of strategies.
        """
        if enabled_only:
            return [s for s in self._strategies if s.is_enabled()]
        return self._strategies.copy()

    def find_strategies(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
    ) -> list[RecoveryStrategy]:
        """Find strategies that can handle the given anomaly.

        Args:
            anomaly_type: Type of anomaly detected.
            service_id: ID of the affected service.
            context: Additional context about the anomaly.

        Returns:
            List of applicable strategies, sorted by priority.
        """
        applicable = []
        for strategy in self._strategies:
            if strategy.is_enabled() and strategy.can_handle(
                anomaly_type, service_id, context
            ):
                applicable.append(strategy)

        # Sort by priority (already sorted, but ensure)
        applicable.sort(key=lambda s: s.get_priority(), reverse=True)
        return applicable

    def create_action(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
        strategy_name: str | None = None,
    ) -> RecoveryAction | None:
        """Create a recovery action for the anomaly.

        Args:
            anomaly_type: Type of anomaly detected.
            service_id: ID of the affected service.
            context: Additional context about the anomaly.
            strategy_name: If specified, use this specific strategy.

        Returns:
            Recovery action, or None if no strategy can handle it.
        """
        if strategy_name:
            # Find specific strategy
            for strategy in self._strategies:
                if strategy.get_name() == strategy_name and strategy.is_enabled():
                    if strategy.can_handle(anomaly_type, service_id, context):
                        action = strategy.create_action(
                            anomaly_type, service_id, context
                        )
                        if action:
                            return self._prepare_action(action)
            return None

        # Find best matching strategy
        strategies = self.find_strategies(anomaly_type, service_id, context)
        for strategy in strategies:
            action = strategy.create_action(anomaly_type, service_id, context)
            if action:
                return self._prepare_action(action)

        return None

    def create_actions(
        self,
        anomaly_type: str,
        service_id: str,
        context: dict[str, Any],
        max_actions: int = 3,
    ) -> list[RecoveryAction]:
        """Create multiple recovery actions for the anomaly.

        Args:
            anomaly_type: Type of anomaly detected.
            service_id: ID of the affected service.
            context: Additional context about the anomaly.
            max_actions: Maximum number of actions to create.

        Returns:
            List of recovery actions.
        """
        actions = []
        strategies = self.find_strategies(anomaly_type, service_id, context)

        for strategy in strategies[:max_actions]:
            action = strategy.create_action(anomaly_type, service_id, context)
            if action:
                actions.append(self._prepare_action(action))

        return actions

    def _prepare_action(self, action: RecoveryAction) -> RecoveryAction:
        """Prepare an action for execution.

        Args:
            action: Action to prepare.

        Returns:
            Prepared action.
        """
        # Ensure action has an ID
        if not action.id:
            action.id = str(uuid.uuid4())

        return action

    def clear(self) -> None:
        """Clear all registered strategies."""
        self._strategies.clear()

    def get_strategy_count(self) -> int:
        """Get the number of registered strategies.

        Returns:
            Number of strategies.
        """
        return len(self._strategies)

    def get_strategy_names(self) -> list[str]:
        """Get names of all registered strategies.

        Returns:
            List of strategy names.
        """
        return [s.get_name() for s in self._strategies]
