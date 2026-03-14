"""NyxAI Recovery Strategies module.

This module provides recovery strategy definitions and management.
"""

from nyxai.recovery.strategies.base import RecoveryAction, RecoveryStrategy
from nyxai.recovery.strategies.manager import StrategyManager
from nyxai.recovery.strategies.builtin import (
    RestartServiceStrategy,
    ScaleUpStrategy,
    ClearCacheStrategy,
    CircuitBreakerStrategy,
)

__all__ = [
    "RecoveryAction",
    "RecoveryStrategy",
    "StrategyManager",
    "RestartServiceStrategy",
    "ScaleUpStrategy",
    "ClearCacheStrategy",
    "CircuitBreakerStrategy",
]
