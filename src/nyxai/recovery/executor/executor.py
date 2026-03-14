"""Action executor for recovery strategies.

This module provides the execution engine for recovery actions,
including dry-run mode, rollback support, and execution tracking.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, Field

from nyxai.recovery.strategies.base import ActionStatus, RecoveryAction


class ExecutionStatus(str, Enum):
    """Status of action execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionBackend(Protocol):
    """Protocol for execution backends."""

    async def execute(self, action: RecoveryAction) -> dict[str, Any]:
        """Execute an action.

        Args:
            action: Recovery action to execute.

        Returns:
            Execution result.
        """
        ...

    async def rollback(self, action: RecoveryAction) -> dict[str, Any]:
        """Rollback an action.

        Args:
            action: Recovery action to rollback.

        Returns:
            Rollback result.
        """
        ...


@dataclass
class ExecutionResult:
    """Result of action execution.

    Attributes:
        action_id: ID of the executed action.
        status: Execution status.
        success: Whether execution was successful.
        output: Execution output.
        error: Error message if failed.
        execution_time_ms: Execution time in milliseconds.
        started_at: Start timestamp.
        completed_at: Completion timestamp.
        rollback_result: Rollback result if applicable.
        metadata: Additional metadata.
    """

    action_id: str
    status: ExecutionStatus
    success: bool = False
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    execution_time_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    rollback_result: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "action_id": self.action_id,
            "status": self.status.value,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "rollback_result": self.rollback_result,
            "metadata": self.metadata,
        }


class ExecutorConfig(BaseModel):
    """Configuration for Action Executor.

    Attributes:
        dry_run: Whether to simulate execution without actual changes.
        enable_rollback: Whether to enable rollback on failure.
        default_timeout_seconds: Default execution timeout.
        max_concurrent_executions: Maximum concurrent executions.
        retry_attempts: Number of retry attempts on failure.
        retry_delay_seconds: Delay between retries.
    """

    dry_run: bool = Field(default=False, description="Dry run mode")
    enable_rollback: bool = Field(default=True, description="Enable rollback")
    default_timeout_seconds: float = Field(
        default=300.0, ge=1.0, description="Default timeout"
    )
    max_concurrent_executions: int = Field(
        default=5, ge=1, description="Max concurrent executions"
    )
    retry_attempts: int = Field(default=3, ge=0, description="Retry attempts")
    retry_delay_seconds: float = Field(
        default=5.0, ge=0.0, description="Retry delay"
    )


class ActionExecutor:
    """Executes recovery actions.

    This class provides the execution engine for recovery actions,
    with support for dry-run mode, rollback, and execution tracking.

    Attributes:
        config: Executor configuration.
        _backends: Mapping of action types to backends.
        _execution_history: History of executed actions.
        _semaphore: Semaphore for limiting concurrent executions.
    """

    def __init__(self, config: ExecutorConfig | None = None) -> None:
        """Initialize the action executor.

        Args:
            config: Executor configuration. Uses defaults if None.
        """
        self.config = config or ExecutorConfig()
        self._backends: dict[str, ExecutionBackend] = {}
        self._execution_history: list[ExecutionResult] = []
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_executions)

    def register_backend(
        self, action_type: str, backend: ExecutionBackend
    ) -> None:
        """Register an execution backend for an action type.

        Args:
            action_type: Action type to handle.
            backend: Backend implementation.
        """
        self._backends[action_type] = backend

    def unregister_backend(self, action_type: str) -> bool:
        """Unregister an execution backend.

        Args:
            action_type: Action type to unregister.

        Returns:
            True if unregistered, False if not found.
        """
        if action_type in self._backends:
            del self._backends[action_type]
            return True
        return False

    async def execute(
        self,
        action: RecoveryAction,
        timeout: float | None = None,
        dry_run: bool | None = None,
    ) -> ExecutionResult:
        """Execute a recovery action.

        Args:
            action: Recovery action to execute.
            timeout: Execution timeout. Uses config default if None.
            dry_run: Whether to simulate. Uses config default if None.

        Returns:
            Execution result.
        """
        timeout = timeout or self.config.default_timeout_seconds
        dry_run = dry_run if dry_run is not None else self.config.dry_run

        action.mark_executing()

        async with self._semaphore:
            started_at = datetime.utcnow()

            try:
                # Check if backend exists
                backend = self._backends.get(action.action_type.value)
                if not backend:
                    result = ExecutionResult(
                        action_id=action.id,
                        status=ExecutionStatus.FAILED,
                        success=False,
                        error=f"No backend registered for action type: {action.action_type.value}",
                        started_at=started_at,
                        completed_at=datetime.utcnow(),
                    )
                    action.mark_failed(result.error)
                    self._execution_history.append(result)
                    return result

                # Execute with retries
                for attempt in range(self.config.retry_attempts + 1):
                    try:
                        if dry_run:
                            output = await self._simulate_execution(action, backend)
                        else:
                            output = await asyncio.wait_for(
                                backend.execute(action),
                                timeout=timeout,
                            )

                        completed_at = datetime.utcnow()
                        execution_time_ms = (
                            completed_at - started_at
                        ).total_seconds() * 1000

                        result = ExecutionResult(
                            action_id=action.id,
                            status=ExecutionStatus.SUCCESS,
                            success=True,
                            output=output,
                            execution_time_ms=execution_time_ms,
                            started_at=started_at,
                            completed_at=completed_at,
                            metadata={
                                "dry_run": dry_run,
                                "attempt": attempt + 1,
                            },
                        )

                        action.mark_success(output)
                        self._execution_history.append(result)
                        return result

                    except asyncio.TimeoutError:
                        if attempt < self.config.retry_attempts:
                            await asyncio.sleep(self.config.retry_delay_seconds)
                            continue

                        completed_at = datetime.utcnow()
                        execution_time_ms = (
                            completed_at - started_at
                        ).total_seconds() * 1000

                        result = ExecutionResult(
                            action_id=action.id,
                            status=ExecutionStatus.TIMEOUT,
                            success=False,
                            error=f"Execution timed out after {timeout}s",
                            execution_time_ms=execution_time_ms,
                            started_at=started_at,
                            completed_at=completed_at,
                        )

                        action.mark_failed(result.error)
                        self._execution_history.append(result)
                        return result

                    except Exception as e:
                        if attempt < self.config.retry_attempts:
                            await asyncio.sleep(self.config.retry_delay_seconds)
                            continue

                        raise

            except Exception as e:
                completed_at = datetime.utcnow()
                execution_time_ms = (
                    completed_at - started_at
                ).total_seconds() * 1000

                result = ExecutionResult(
                    action_id=action.id,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error=str(e),
                    execution_time_ms=execution_time_ms,
                    started_at=started_at,
                    completed_at=completed_at,
                )

                action.mark_failed(result.error)
                self._execution_history.append(result)

                # Attempt rollback if enabled
                if self.config.enable_rollback and not dry_run:
                    rollback_result = await self._rollback_action(action)
                    result.rollback_result = rollback_result
                    result.status = ExecutionStatus.ROLLED_BACK

                return result

    async def execute_batch(
        self,
        actions: list[RecoveryAction],
        sequential: bool = False,
    ) -> list[ExecutionResult]:
        """Execute multiple actions.

        Args:
            actions: List of actions to execute.
            sequential: Whether to execute sequentially or in parallel.

        Returns:
            List of execution results.
        """
        if sequential:
            results = []
            for action in actions:
                result = await self.execute(action)
                results.append(result)
                # Stop on failure
                if not result.success:
                    break
            return results
        else:
            tasks = [self.execute(action) for action in actions]
            return await asyncio.gather(*tasks)

    async def rollback(self, action: RecoveryAction) -> ExecutionResult:
        """Rollback a previously executed action.

        Args:
            action: Action to rollback.

        Returns:
            Rollback execution result.
        """
        started_at = datetime.utcnow()

        try:
            backend = self._backends.get(action.action_type.value)
            if not backend:
                return ExecutionResult(
                    action_id=action.id,
                    status=ExecutionStatus.FAILED,
                    success=False,
                    error=f"No backend registered for action type: {action.action_type.value}",
                    started_at=started_at,
                    completed_at=datetime.utcnow(),
                )

            output = await backend.rollback(action)

            completed_at = datetime.utcnow()
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000

            action.mark_rolled_back()

            return ExecutionResult(
                action_id=action.id,
                status=ExecutionStatus.ROLLED_BACK,
                success=True,
                output=output,
                execution_time_ms=execution_time_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

        except Exception as e:
            completed_at = datetime.utcnow()
            execution_time_ms = (completed_at - started_at).total_seconds() * 1000

            return ExecutionResult(
                action_id=action.id,
                status=ExecutionStatus.FAILED,
                success=False,
                error=f"Rollback failed: {str(e)}",
                execution_time_ms=execution_time_ms,
                started_at=started_at,
                completed_at=completed_at,
            )

    async def _rollback_action(self, action: RecoveryAction) -> dict[str, Any]:
        """Internal method to rollback an action.

        Args:
            action: Action to rollback.

        Returns:
            Rollback result.
        """
        try:
            backend = self._backends.get(action.action_type.value)
            if backend:
                return await backend.rollback(action)
            return {"error": "No backend available for rollback"}
        except Exception as e:
            return {"error": str(e)}

    async def _simulate_execution(
        self,
        action: RecoveryAction,
        backend: ExecutionBackend,
    ) -> dict[str, Any]:
        """Simulate action execution (dry run).

        Args:
            action: Action to simulate.
            backend: Backend that would execute the action.

        Returns:
            Simulated execution output.
        """
        return {
            "simulated": True,
            "action_type": action.action_type.value,
            "target": action.target,
            "parameters": action.parameters,
            "message": "Action would be executed in non-dry-run mode",
        }

    def get_execution_history(
        self,
        action_id: str | None = None,
        limit: int | None = None,
    ) -> list[ExecutionResult]:
        """Get execution history.

        Args:
            action_id: Filter by action ID. Returns all if None.
            limit: Maximum number of results to return.

        Returns:
            List of execution results.
        """
        results = self._execution_history

        if action_id:
            results = [r for r in results if r.action_id == action_id]

        # Sort by started_at descending
        results = sorted(results, key=lambda r: r.started_at, reverse=True)

        if limit:
            results = results[:limit]

        return results

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()

    def get_statistics(self) -> dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dictionary with statistics.
        """
        total = len(self._execution_history)
        if total == 0:
            return {
                "total_executions": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "average_execution_time_ms": 0.0,
            }

        successful = sum(1 for r in self._execution_history if r.success)
        failed = total - successful

        avg_time = sum(r.execution_time_ms for r in self._execution_history) / total

        return {
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total,
            "average_execution_time_ms": avg_time,
        }
