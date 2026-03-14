"""Recovery action API endpoints for NyxAI.

This module provides REST API endpoints for managing recovery actions,
including listing, executing, and tracking recovery actions.
"""

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from nyxai.api.models.common import PaginationParams
from nyxai.recovery.strategies.base import ActionStatus, ActionType, RiskLevel

router = APIRouter()

# In-memory storage for demonstration
_recovery_actions: dict[str, dict[str, Any]] = {}
_execution_history: list[dict[str, Any]] = []


class RecoveryActionCreateRequest(BaseModel):
    """Request model for creating a recovery action."""

    action_type: ActionType
    target: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    estimated_duration: float = 60.0
    requires_approval: bool = False


class RecoveryActionResponse(BaseModel):
    """Response model for a recovery action."""

    id: str
    action_type: str
    target: str
    parameters: dict[str, Any]
    risk_level: str
    estimated_duration: float
    requires_approval: bool
    status: str
    result: dict[str, Any] | None
    created_at: datetime
    executed_at: datetime | None
    completed_at: datetime | None


class RecoveryActionListResponse(BaseModel):
    """Response model for a list of recovery actions."""

    items: list[RecoveryActionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RecoveryActionFilterParams(BaseModel):
    """Filter parameters for recovery actions."""

    action_type: ActionType | None = None
    target: str | None = None
    status: ActionStatus | None = None
    risk_level: RiskLevel | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None


class ExecuteActionRequest(BaseModel):
    """Request model for executing a recovery action."""

    dry_run: bool = Field(default=False, description="Execute in dry-run mode")
    timeout: float | None = Field(default=None, description="Execution timeout in seconds")


class ExecuteActionResponse(BaseModel):
    """Response model for action execution."""

    success: bool
    action_id: str
    status: str
    output: dict[str, Any] | None
    error: str | None
    execution_time_ms: float
    executed_at: datetime


@router.get(
    "/recovery/actions",
    response_model=RecoveryActionListResponse,
    summary="List recovery actions",
    description="Get a paginated list of recovery actions with optional filtering.",
)
async def list_recovery_actions(
    pagination: Annotated[PaginationParams, Query()],
    filters: Annotated[RecoveryActionFilterParams, Query()],
) -> RecoveryActionListResponse:
    """Get a list of recovery actions with pagination and filtering."""
    filtered = list(_recovery_actions.values())

    if filters.action_type:
        filtered = [a for a in filtered if a["action_type"] == filters.action_type.value]

    if filters.target:
        filtered = [a for a in filtered if filters.target in a["target"]]

    if filters.status:
        filtered = [a for a in filtered if a["status"] == filters.status.value]

    if filters.risk_level:
        filtered = [a for a in filtered if a["risk_level"] == filters.risk_level.value]

    if filters.start_date:
        filtered = [a for a in filtered if a["created_at"] >= filters.start_date]

    if filters.end_date:
        filtered = [a for a in filtered if a["created_at"] <= filters.end_date]

    # Sort by created_at descending
    filtered.sort(key=lambda a: a["created_at"], reverse=True)

    total = len(filtered)
    total_pages = (total + pagination.page_size - 1) // pagination.page_size
    offset = pagination.offset
    paginated = filtered[offset : offset + pagination.page_size]

    items = [RecoveryActionResponse.model_validate(a) for a in paginated]

    return RecoveryActionListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get(
    "/recovery/actions/{action_id}",
    response_model=RecoveryActionResponse,
    summary="Get recovery action details",
    description="Get detailed information about a specific recovery action.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Action not found"},
    },
)
async def get_recovery_action(action_id: str) -> RecoveryActionResponse:
    """Get details of a specific recovery action."""
    if action_id not in _recovery_actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery action with ID '{action_id}' not found",
        )

    return RecoveryActionResponse.model_validate(_recovery_actions[action_id])


@router.post(
    "/recovery/actions",
    response_model=RecoveryActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create recovery action",
    description="Create a new recovery action.",
)
async def create_recovery_action(
    request: RecoveryActionCreateRequest,
) -> RecoveryActionResponse:
    """Create a new recovery action."""
    import uuid

    action_id = str(uuid.uuid4())
    action = {
        "id": action_id,
        "action_type": request.action_type.value,
        "target": request.target,
        "parameters": request.parameters,
        "risk_level": request.risk_level.value,
        "estimated_duration": request.estimated_duration,
        "requires_approval": request.requires_approval,
        "status": ActionStatus.PENDING.value,
        "result": None,
        "created_at": datetime.utcnow(),
        "executed_at": None,
        "completed_at": None,
    }

    _recovery_actions[action_id] = action

    return RecoveryActionResponse.model_validate(action)


@router.post(
    "/recovery/actions/{action_id}/execute",
    response_model=ExecuteActionResponse,
    summary="Execute recovery action",
    description="Execute a recovery action.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Action not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Action cannot be executed"},
    },
)
async def execute_recovery_action(
    action_id: str,
    request: ExecuteActionRequest,
) -> ExecuteActionResponse:
    """Execute a recovery action."""
    if action_id not in _recovery_actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery action with ID '{action_id}' not found",
        )

    action = _recovery_actions[action_id]

    if action["status"] not in [ActionStatus.PENDING.value, ActionStatus.FAILED.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Action cannot be executed in status: {action['status']}",
        )

    # Simulate execution
    action["status"] = ActionStatus.IN_PROGRESS.value
    action["executed_at"] = datetime.utcnow()

    # In real implementation, this would call the ActionExecutor
    # For now, simulate success
    action["status"] = ActionStatus.SUCCESS.value
    action["completed_at"] = datetime.utcnow()
    action["result"] = {
        "simulated": True,
        "dry_run": request.dry_run,
        "message": "Action executed successfully (simulated)",
    }

    # Record in execution history
    _execution_history.append({
        "action_id": action_id,
        "executed_at": action["executed_at"],
        "completed_at": action["completed_at"],
        "status": action["status"],
        "dry_run": request.dry_run,
    })

    return ExecuteActionResponse(
        success=True,
        action_id=action_id,
        status=action["status"],
        output=action["result"],
        error=None,
        execution_time_ms=1000.0,
        executed_at=action["executed_at"],
    )


@router.post(
    "/recovery/actions/{action_id}/cancel",
    response_model=RecoveryActionResponse,
    summary="Cancel recovery action",
    description="Cancel a pending recovery action.",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Action not found"},
        status.HTTP_400_BAD_REQUEST: {"description": "Action cannot be cancelled"},
    },
)
async def cancel_recovery_action(action_id: str) -> RecoveryActionResponse:
    """Cancel a pending recovery action."""
    if action_id not in _recovery_actions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recovery action with ID '{action_id}' not found",
        )

    action = _recovery_actions[action_id]

    if action["status"] != ActionStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel action in status: {action['status']}",
        )

    action["status"] = ActionStatus.CANCELLED.value
    action["completed_at"] = datetime.utcnow()

    return RecoveryActionResponse.model_validate(action)


@router.get(
    "/recovery/execution-history",
    summary="Get execution history",
    description="Get the execution history of recovery actions.",
)
async def get_execution_history(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    action_id: str | None = None,
) -> list[dict[str, Any]]:
    """Get execution history."""
    history = _execution_history

    if action_id:
        history = [h for h in history if h["action_id"] == action_id]

    # Sort by executed_at descending
    history.sort(key=lambda h: h["executed_at"], reverse=True)

    return history[:limit]


@router.get(
    "/recovery/statistics",
    summary="Get recovery statistics",
    description="Get statistics about recovery actions.",
)
async def get_recovery_statistics() -> dict[str, Any]:
    """Get recovery statistics."""
    actions = list(_recovery_actions.values())

    total = len(actions)
    pending = sum(1 for a in actions if a["status"] == ActionStatus.PENDING.value)
    in_progress = sum(1 for a in actions if a["status"] == ActionStatus.IN_PROGRESS.value)
    successful = sum(1 for a in actions if a["status"] == ActionStatus.SUCCESS.value)
    failed = sum(1 for a in actions if a["status"] == ActionStatus.FAILED.value)

    return {
        "total_actions": total,
        "pending": pending,
        "in_progress": in_progress,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total if total > 0 else 0.0,
    }
