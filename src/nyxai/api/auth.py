"""Authentication and authorization for NyxAI API.

This module provides authentication and authorization mechanisms
for the NyxAI REST API and WebSocket endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from nyxai.config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(BaseModel):
    """User model."""

    id: str
    username: str
    email: str | None = None
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TokenData(BaseModel):
    """Token data model."""

    user_id: str | None = None
    username: str | None = None
    role: UserRole | None = None
    scopes: list[str] = Field(default_factory=list)


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class APIKey(BaseModel):
    """API key model."""

    key: str
    name: str
    user_id: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    last_used_at: datetime | None = None


# In-memory storage for demonstration
# In production, use a database
_users: dict[str, User] = {}
_api_keys: dict[str, APIKey] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password.
        hashed_password: Hashed password.

    Returns:
        True if password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password.

    Args:
        password: Plain text password.

    Returns:
        Hashed password.
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token.
        expires_delta: Token expiration time.

    Returns:
        JWT token string.
    """
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )

    return encoded_jwt


def decode_token(token: str) -> TokenData | None:
    """Decode a JWT token.

    Args:
        token: JWT token string.

    Returns:
        Token data if valid, None otherwise.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=["HS256"],
        )

        user_id: str | None = payload.get("sub")
        username: str | None = payload.get("username")
        role_str: str | None = payload.get("role")
        scopes: list[str] = payload.get("scopes", [])

        if user_id is None:
            return None

        role = UserRole(role_str) if role_str else None

        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            scopes=scopes,
        )

    except JWTError:
        return None


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials | None = Security(http_bearer),
) -> User | None:
    """Get current user from JWT token.

    Args:
        credentials: HTTP bearer credentials.

    Returns:
        User if authenticated, None otherwise.
    """
    if credentials is None:
        return None

    token_data = decode_token(credentials.credentials)

    if token_data is None or token_data.user_id is None:
        return None

    return _users.get(token_data.user_id)


async def get_current_user_from_api_key(
    api_key: str | None = Security(api_key_header),
) -> User | None:
    """Get current user from API key.

    Args:
        api_key: API key from header.

    Returns:
        User if authenticated, None otherwise.
    """
    if api_key is None:
        return None

    key_data = _api_keys.get(api_key)

    if key_data is None or not key_data.is_active:
        return None

    # Check expiration
    if key_data.expires_at and datetime.utcnow() > key_data.expires_at:
        return None

    # Update last used
    key_data.last_used_at = datetime.utcnow()

    return _users.get(key_data.user_id)


async def get_current_user(
    token_user: Annotated[User | None, Depends(get_current_user_from_token)],
    api_key_user: Annotated[User | None, Depends(get_current_user_from_api_key)],
) -> User | None:
    """Get current user from either token or API key.

    Args:
        token_user: User from JWT token.
        api_key_user: User from API key.

    Returns:
        User if authenticated, None otherwise.
    """
    return token_user or api_key_user


async def require_auth(
    current_user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """Require authentication.

    Args:
        current_user: Current user from authentication.

    Returns:
        Authenticated user.

    Raises:
        HTTPException: If not authenticated.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return current_user


class RoleChecker:
    """Check if user has required role."""

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        """Initialize role checker.

        Args:
            allowed_roles: List of allowed roles.
        """
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[User, Depends(require_auth)]) -> User:
        """Check user role.

        Args:
            user: Current user.

        Returns:
            User if authorized.

        Raises:
            HTTPException: If not authorized.
        """
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user


# Role-based dependencies
require_admin = RoleChecker([UserRole.ADMIN])
require_operator = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR])
require_viewer = RoleChecker([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])


def create_user(
    username: str,
    email: str | None,
    role: UserRole,
    password: str | None = None,
) -> User:
    """Create a new user.

    Args:
        username: Username.
        email: Email address.
        role: User role.
        password: Optional password.

    Returns:
        Created user.
    """
    import uuid

    user_id = str(uuid.uuid4())

    user = User(
        id=user_id,
        username=username,
        email=email,
        role=role,
    )

    _users[user_id] = user

    return user


def create_api_key(
    name: str,
    user_id: str,
    role: UserRole,
    expires_days: int | None = None,
) -> str:
    """Create a new API key.

    Args:
        name: Key name.
        user_id: User ID.
        role: Role for the key.
        expires_days: Expiration in days.

    Returns:
        API key string.
    """
    import secrets
    import uuid

    key = f"nyx_{secrets.token_urlsafe(32)}"

    expires_at = None
    if expires_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    api_key = APIKey(
        key=key,
        name=name,
        user_id=user_id,
        role=role,
        expires_at=expires_at,
    )

    _api_keys[key] = api_key

    return key


def revoke_api_key(key: str) -> bool:
    """Revoke an API key.

    Args:
        key: API key to revoke.

    Returns:
        True if revoked, False if not found.
    """
    if key in _api_keys:
        _api_keys[key].is_active = False
        return True
    return False


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user with username and password.

    Args:
        username: Username.
        password: Password.

    Returns:
        User if authenticated, None otherwise.
    """
    # In production, this would query the database
    # For demonstration, we check in-memory storage
    for user in _users.values():
        if user.username == username:
            # In a real implementation, we'd verify the password hash
            # For now, we just return the user
            return user

    return None


# Initialize default users for demonstration
def init_default_users() -> None:
    """Initialize default users for demonstration."""
    # Create admin user
    admin = create_user(
        username="admin",
        email="admin@nyxai.local",
        role=UserRole.ADMIN,
    )

    # Create operator user
    operator = create_user(
        username="operator",
        email="operator@nyxai.local",
        role=UserRole.OPERATOR,
    )

    # Create viewer user
    viewer = create_user(
        username="viewer",
        email="viewer@nyxai.local",
        role=UserRole.VIEWER,
    )

    # Create default API key for admin
    create_api_key(
        name="Default Admin Key",
        user_id=admin.id,
        role=UserRole.ADMIN,
    )
