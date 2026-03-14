"""Base class for LLM providers.

This module defines the abstract base class and data models
for LLM providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Roles for LLM messages."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class LLMMessage:
    """Represents a message in the conversation.

    Attributes:
        role: Role of the message sender.
        content: Message content.
        metadata: Additional message metadata.
    """

    role: MessageRole
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the message.
        """
        return {
            "role": self.role.value,
            "content": self.content,
        }


@dataclass
class LLMResponse:
    """Represents a response from the LLM.

    Attributes:
        content: Response content.
        model: Model used for generation.
        usage: Token usage information.
        finish_reason: Reason for finishing generation.
        metadata: Additional response metadata.
        created_at: Response timestamp.
    """

    content: str
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation of the response.
        """
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProviderConfig(BaseModel):
    """Base configuration for LLM providers.

    Attributes:
        model: Model name to use.
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum tokens to generate.
        top_p: Nucleus sampling parameter.
        timeout_seconds: Request timeout in seconds.
        max_retries: Maximum number of retries.
    """

    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int | None = Field(default=2048, ge=1, description="Maximum tokens")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling")
    timeout_seconds: float = Field(default=60.0, ge=1.0, description="Timeout")
    max_retries: int = Field(default=3, ge=0, description="Maximum retries")


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must inherit from this class and implement
the chat() and achat() methods.

    Attributes:
        config: Provider configuration.
    """

    def __init__(self, config: ProviderConfig | None = None) -> None:
        """Initialize the LLM provider.

        Args:
            config: Provider configuration. Uses defaults if None.
        """
        self.config = config or ProviderConfig()

    @abstractmethod
    def chat(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request (synchronous).

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLM response.
        """
        ...

    @abstractmethod
    async def achat(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request (asynchronous).

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLM response.
        """
        ...

    @abstractmethod
    async def astream(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response (asynchronous).

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Chunks of the response content.
        """
        ...

    def create_system_message(self, content: str) -> LLMMessage:
        """Create a system message.

        Args:
            content: Message content.

        Returns:
            System message.
        """
        return LLMMessage(role=MessageRole.SYSTEM, content=content)

    def create_user_message(self, content: str) -> LLMMessage:
        """Create a user message.

        Args:
            content: Message content.

        Returns:
            User message.
        """
        return LLMMessage(role=MessageRole.USER, content=content)

    def create_assistant_message(self, content: str) -> LLMMessage:
        """Create an assistant message.

        Args:
            content: Message content.

        Returns:
            Assistant message.
        """
        return LLMMessage(role=MessageRole.ASSISTANT, content=content)

    def get_model(self) -> str:
        """Get the model name.

        Returns:
            Model name.
        """
        return self.config.model

    def _prepare_messages(
        self, messages: list[LLMMessage]
    ) -> list[dict[str, str]]:
        """Prepare messages for API request.

        Args:
            messages: List of LLM messages.

        Returns:
            List of message dictionaries.
        """
        return [msg.to_dict() for msg in messages]
