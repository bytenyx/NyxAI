"""Execute Agent for NyxAI.

This module implements the Execute Agent that executes recovery actions.
"""

from __future__ import annotations

import time
from typing import Any

from nyxai.agents.base import Agent, AgentConfig, AgentResult
from nyxai.types import AgentContext, AgentRole
from nyxai.recovery.executor.executor import ActionExecutor, ExecutionResult
from nyxai.recovery.strategies.base import RecoveryAction


class ExecuteAgentConfig(AgentConfig):
    """Configuration for Execute Agent.

    Attributes:
        require_approval: Whether to require approval for all actions.
        auto_execute_low_risk: Whether to auto-execute low-risk actions.
        max_parallel_executions: Maximum parallel action executions.
        execution_timeout_seconds: Timeout for action execution.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "ExecuteAgent"
        self.role = AgentRole.EXECUTE
        self.description = "Executes recovery actions"
        self.require_approval = False
        self.auto_execute_low_risk = True
        self.max_parallel_executions = 3
        self.execution_timeout_seconds = 300.0


class ExecuteAgent(Agent):
    """Agent responsible for executing recovery actions.

    This agent executes the recovery actions decided by the Decide Agent,
    handling approval workflows and execution tracking.

    Attributes:
        config: Execute agent configuration.
        _action_executor: Executor for recovery actions.
    """

    def __init__(
        self,
        action_executor: ActionExecutor,
        config: ExecuteAgentConfig | None = None,
    ) -> None:
        """Initialize the execute agent.

        Args:
            action_executor: Executor for recovery actions.
            config: Agent configuration. Uses defaults if None.
        """
        super().__init__(config or ExecuteAgentConfig())
        self.execute_config = config or ExecuteAgentConfig()
        self._action_executor = action_executor

    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute recovery actions.

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
                    error="Agent cannot execute: no recovery actions in context",
                    agent_name=self.get_name(),
                )

            recovery_actions = context.recovery_actions

            if not recovery_actions:
                return AgentResult.success_result(
                    data={"message": "No recovery actions to execute", "results": []},
                    agent_name=self.get_name(),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Filter actions to execute
            actions_to_execute = self._filter_actions(recovery_actions)

            if not actions_to_execute:
                return AgentResult.success_result(
                    data={
                        "message": "No actions ready for execution (pending approval)",
                        "results": [],
                        "pending_approval": len(recovery_actions),
                    },
                    agent_name=self.get_name(),
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Execute actions
            results = await self._execute_actions(actions_to_execute)

            # Update context with execution results
            execution_results = [r.to_dict() for r in results]
            context.update(execution_results=execution_results)

            self._set_status(self.get_status().SUCCESS)

            execution_time_ms = (time.time() - start_time) * 1000

            # Determine overall success
            success_count = sum(1 for r in results if r.success)

            return AgentResult.success_result(
                data={
                    "results": execution_results,
                    "total_actions": len(actions_to_execute),
                    "successful": success_count,
                    "failed": len(actions_to_execute) - success_count,
                },
                agent_name=self.get_name(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            self._set_status(self.get_status().FAILED)
            return AgentResult.failure_result(
                error=f"Execute agent failed: {str(e)}",
                agent_name=self.get_name(),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _filter_actions(
        self,
        recovery_actions: list[dict[str, Any]],
    ) -> list[RecoveryAction]:
        """Filter actions that are ready for execution.

        Args:
            recovery_actions: List of recovery actions with assessments.

        Returns:
            List of actions ready for execution.
        """
        actions: list[RecoveryAction] = []

        for item in recovery_actions:
            action_dict = item.get("action", {})
            risk_assessment = item.get("risk_assessment", {})

            # Check if action requires approval
            requires_approval = action_dict.get("requires_approval", False)
            approved = risk_assessment.get("approved", False)
            risk_level = risk_assessment.get("risk_level", "medium")

            # Determine if we can execute
            can_execute = False

            if not requires_approval:
                can_execute = True
            elif approved:
                can_execute = True
            elif (
                self.execute_config.auto_execute_low_risk
                and risk_level in ["low", "medium"]
            ):
                can_execute = True

            if can_execute:
                # Reconstruct RecoveryAction from dict
                from nyxai.recovery.strategies.base import ActionType

                action = RecoveryAction(
                    id=action_dict.get("id", ""),
                    action_type=ActionType(action_dict.get("action_type", "custom")),
                    target=action_dict.get("target", ""),
                    parameters=action_dict.get("parameters", {}),
                    risk_level=item.get("risk_level", "medium"),
                    estimated_duration=action_dict.get("estimated_duration", 60.0),
                    requires_approval=requires_approval,
                )
                actions.append(action)

        return actions

    async def _execute_actions(
        self,
        actions: list[RecoveryAction],
    ) -> list[ExecutionResult]:
        """Execute the recovery actions.

        Args:
            actions: List of actions to execute.

        Returns:
            List of execution results.
        """
        results: list[ExecutionResult] = []

        # Execute sequentially for safety
        for action in actions:
            result = await self._action_executor.execute(
                action,
                timeout=self.execute_config.execution_timeout_seconds,
            )
            results.append(result)

            # Stop on failure if action is critical
            if not result.success and action.risk_level.value == "critical":
                break

        return results

    async def approve_and_execute(
        self,
        context: AgentContext,
        action_ids: list[str],
    ) -> AgentResult:
        """Approve and execute specific actions.

        Args:
            context: Execution context.
            action_ids: IDs of actions to approve and execute.

        Returns:
            Agent execution result.
        """
        start_time = time.time()

        recovery_actions = context.recovery_actions

        # Find actions to approve
        actions_to_execute: list[RecoveryAction] = []
        for item in recovery_actions:
            action_dict = item.get("action", {})
            if action_dict.get("id") in action_ids:
                from nyxai.recovery.strategies.base import ActionType

                action = RecoveryAction(
                    id=action_dict.get("id", ""),
                    action_type=ActionType(action_dict.get("action_type", "custom")),
                    target=action_dict.get("target", ""),
                    parameters=action_dict.get("parameters", {}),
                    risk_level=item.get("risk_level", "medium"),
                    estimated_duration=action_dict.get("estimated_duration", 60.0),
                    requires_approval=False,  # Override approval
                )
                actions_to_execute.append(action)

        if not actions_to_execute:
            return AgentResult.failure_result(
                error="No matching actions found for approval",
                agent_name=self.get_name(),
            )

        # Execute approved actions
        results = await self._execute_actions(actions_to_execute)

        # Update context
        execution_results = [r.to_dict() for r in results]
        context.update(execution_results=execution_results)

        execution_time_ms = (time.time() - start_time) * 1000

        success_count = sum(1 for r in results if r.success)

        return AgentResult.success_result(
            data={
                "results": execution_results,
                "total_actions": len(actions_to_execute),
                "successful": success_count,
                "failed": len(actions_to_execute) - success_count,
            },
            agent_name=self.get_name(),
            execution_time_ms=execution_time_ms,
        )

    def get_execution_statistics(self) -> dict[str, Any]:
        """Get execution statistics.

        Returns:
            Dictionary with execution statistics.
        """
        return self._action_executor.get_statistics()
