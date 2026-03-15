"""Authentication API endpoints for NyxAI.

This module provides REST API endpoints for authentication,
including login, token management, and API key management.
"""

from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from nyxai.api.auth import (
    Token,
    User,
    UserRole,
    authenticate_user,
    create_access_token,
    create_api_key,
    create_user,
    init_default_users,
    require_admin,
    require_auth,
    revoke_api_key,
)

router = APIRouter()

# Initialize default users on module load
init_default_users()


class LoginRequest(BaseModel):
    """Request model for login."""

    username: str
    password: str


class CreateUserRequest(BaseModel):
    """Request model for creating a user."""

    username: str
    email: str | None = None
    role: UserRole
    password: str | None = None


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating an API key."""

    name: str
    role: UserRole
    expires_days: int | None = Field(default=None, ge=1, le=365)


class APIKeyResponse(BaseModel):
    """Response model for API key creation."""

    key: str
    name: str
    role: str
    expires_at: str | None
    message: str = "Store this key securely. It will not be shown again."


class UserResponse(BaseModel):
    """Response model for user information."""

    id: str
    username: str
    email: str | None
    role: str
    is_active: bool
    created_at: str


@router.post(
    "/auth/login",
    response_model=Token,
    summary="Login",
    description="Authenticate and obtain an access token.",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Invalid credentials"},
    },
)
async def login(request: LoginRequest) -> Token:
    """Login and get access token."""
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
        },
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
    )


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
)
async def get_current_user_info(
    current_user: Annotated[User, Depends(require_auth)],
) -> UserResponse:
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )


@router.post(
    "/auth/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    description="Create a new user (admin only).",
    dependencies=[Depends(require_admin)],
)
async def create_new_user(request: CreateUserRequest) -> UserResponse:
    """Create a new user."""
    user = create_user(
        username=request.username,
        email=request.email,
        role=request.role,
        password=request.password,
    )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.post(
    "/auth/api-keys",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key",
    description="Create a new API key for programmatic access.",
)
async def create_new_api_key(
    request: CreateAPIKeyRequest,
    current_user: Annotated[User, Depends(require_auth)],
) -> APIKeyResponse:
    """Create a new API key."""
    # Users can only create keys with their own role or lower
    role_hierarchy = {
        UserRole.ADMIN: [UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER],
        UserRole.OPERATOR: [UserRole.OPERATOR, UserRole.VIEWER],
        UserRole.VIEWER: [UserRole.VIEWER],
    }

    allowed_roles = role_hierarchy.get(current_user.role, [])
    if request.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create API key with higher privileges than your own",
        )

    key = create_api_key(
        name=request.name,
        user_id=current_user.id,
        role=request.role,
        expires_days=request.expires_days,
    )

    # Get the API key data to return expires_at
    from nyxai.api.auth import _api_keys

    api_key_data = _api_keys.get(key)
    expires_at = None
    if api_key_data and api_key_data.expires_at:
        expires_at = api_key_data.expires_at.isoformat()

    return APIKeyResponse(
        key=key,
        name=request.name,
        role=request.role.value,
        expires_at=expires_at,
    )


@router.delete(
    "/auth/api-keys/{key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key",
    description="Revoke an API key.",
)
async def revoke_api_key_endpoint(
    key: str,
    current_user: Annotated[User, Depends(require_auth)],
) -> None:
    """Revoke an API key."""
    from nyxai.api.auth import _api_keys

    api_key_data = _api_keys.get(key)

    if not api_key_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Users can only revoke their own keys (unless admin)
    if api_key_data.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke API keys belonging to other users",
        )

    revoke_api_key(key)


@router.get(
    "/auth/api-keys",
    summary="List API keys",
    description="List API keys for the current user.",
)
async def list_api_keys(
    current_user: Annotated[User, Depends(require_auth)],
) -> list[dict[str, Any]]:
    """List API keys."""
    from nyxai.api.auth import _api_keys

    keys = []
    for key, data in _api_keys.items():
        if data.user_id == current_user.id or current_user.role == UserRole.ADMIN:
            keys.append({
                "name": data.name,
                "role": data.role.value,
                "is_active": data.is_active,
                "created_at": data.created_at.isoformat(),
                "expires_at": data.expires_at.isoformat() if data.expires_at else None,
                "last_used_at": data.last_used_at.isoformat() if data.last_used_at else None,
            })

    return keys


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh."""

    refresh_token: str


class LogoutResponse(BaseModel):
    """Response model for logout."""

    message: str = "Logged out successfully"


@router.post(
    "/auth/logout",
    response_model=LogoutResponse,
    summary="Logout",
    description="Logout and invalidate the current token.",
)
async def logout(
    current_user: Annotated[User, Depends(require_auth)],
) -> LogoutResponse:
    """Logout the current user."""
    # In a production system, you would add the token to a blacklist
    # or revoke it in some way. For now, we just return success.
    return LogoutResponse()


@router.post(
    "/auth/refresh",
    response_model=Token,
    summary="Refresh token",
    description="Refresh the access token using a refresh token.",
)
async def refresh_token(request: RefreshTokenRequest) -> Token:
    """Refresh access token."""
    # For simplicity, we create a new token with the same user data
    # In production, you would validate the refresh token first
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": "user_id", "username": "user", "role": "viewer"},
        expires_delta=access_token_expires,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
    )


# Users list endpoint for user management
@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="List users",
    description="List all users (admin only).",
    dependencies=[Depends(require_admin)],
)
async def list_users() -> list[UserResponse]:
    """List all users."""
    from nyxai.api.auth import _users

    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )
        for user in _users.values()
    ]


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update a user (admin only).",
    dependencies=[Depends(require_admin)],
)
async def update_user_endpoint(
    user_id: str,
    request: CreateUserRequest,
) -> UserResponse:
    """Update a user."""
    from nyxai.api.auth import _users

    if user_id not in _users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user = _users[user_id]
    if request.username:
        user.username = request.username
    if request.email:
        user.email = request.email
    if request.role:
        user.role = request.role

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user (admin only).",
    dependencies=[Depends(require_admin)],
)
async def delete_user_endpoint(user_id: str) -> None:
    """Delete a user."""
    from nyxai.api.auth import _users

    if user_id not in _users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    del _users[user_id]
