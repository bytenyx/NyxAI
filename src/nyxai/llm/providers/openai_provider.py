"""OpenAI LLM provider implementation.

This module provides the OpenAI provider for LLM integration.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from nyxai.llm.providers.base import LLMMessage, LLMProvider, LLMResponse, ProviderConfig


class OpenAIConfig(ProviderConfig):
    """Configuration for OpenAI provider.

    Attributes:
        api_key: OpenAI API key.
        base_url: Base URL for API requests.
        organization: OpenAI organization ID.
    """

    api_key: str = ""
    base_url: str | None = None
    organization: str | None = None


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider.

    This provider integrates with OpenAI's API for chat completions.

    Attributes:
        config: OpenAI configuration.
        _client: OpenAI client instance.
    """

    def __init__(self, config: OpenAIConfig | None = None) -> None:
        """Initialize the OpenAI provider.

        Args:
            config: OpenAI configuration. Uses defaults if None.
        """
        super().__init__(config or OpenAIConfig())
        self.openai_config = config or OpenAIConfig()
        self._client = None
        self._async_client = None

    def _get_client(self) -> Any:
        """Get or create the OpenAI client.

        Returns:
            OpenAI client instance.
        """
        if self._client is None:
            try:
                import openai
            except ImportError as e:
                raise ImportError(
                    "OpenAI package not installed. Install with: pip install openai"
                ) from e

            api_key = self.openai_config.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided")

            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if self.openai_config.base_url:
                client_kwargs["base_url"] = self.openai_config.base_url
            if self.openai_config.organization:
                client_kwargs["organization"] = self.openai_config.organization

            self._client = openai.OpenAI(**client_kwargs)

        return self._client

    def _get_async_client(self) -> Any:
        """Get or create the async OpenAI client.

        Returns:
            Async OpenAI client instance.
        """
        if self._async_client is None:
            try:
                import openai
            except ImportError as e:
                raise ImportError(
                    "OpenAI package not installed. Install with: pip install openai"
                ) from e

            api_key = self.openai_config.api_key or os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not provided")

            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if self.openai_config.base_url:
                client_kwargs["base_url"] = self.openai_config.base_url
            if self.openai_config.organization:
                client_kwargs["organization"] = self.openai_config.organization

            self._async_client = openai.AsyncOpenAI(**client_kwargs)

        return self._async_client

    def chat(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request (synchronous).

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters.

        Returns:
            LLM response.
        """
        client = self._get_client()
        prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": prepared_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        if self.config.max_tokens:
            request_params["max_tokens"] = self.config.max_tokens

        # Add any additional kwargs
        request_params.update(kwargs)

        # Make the request
        response = client.chat.completions.create(**request_params)

        # Extract the response content
        choice = response.choices[0]
        content = choice.message.content or ""

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason or "",
        )

    async def achat(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request (asynchronous).

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters.

        Returns:
            LLM response.
        """
        client = self._get_async_client()
        prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": prepared_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        if self.config.max_tokens:
            request_params["max_tokens"] = self.config.max_tokens

        # Add any additional kwargs
        request_params.update(kwargs)

        # Make the request
        response = await client.chat.completions.create(**request_params)

        # Extract the response content
        choice = response.choices[0]
        content = choice.message.content or ""

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
            finish_reason=choice.finish_reason or "",
        )

    async def astream(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response (asynchronous).

        Args:
            messages: List of messages in the conversation.
            **kwargs: Additional parameters.

        Yields:
            Chunks of the response content.
        """
        client = self._get_async_client()
        prepared_messages = self._prepare_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": prepared_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "stream": True,
        }
        if self.config.max_tokens:
            request_params["max_tokens"] = self.config.max_tokens

        # Add any additional kwargs
        request_params.update(kwargs)

        # Make the streaming request
        stream = await client.chat.completions.create(**request_params)

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
