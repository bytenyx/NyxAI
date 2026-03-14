"""Anthropic LLM provider implementation.

This module provides the Anthropic provider for LLM integration.
"""

from __future__ import annotations

import os
from typing import Any, AsyncIterator

from nyxai.llm.providers.base import LLMMessage, LLMProvider, LLMResponse, ProviderConfig


class AnthropicConfig(ProviderConfig):
    """Configuration for Anthropic provider.

    Attributes:
        api_key: Anthropic API key.
        base_url: Base URL for API requests.
    """

    api_key: str = ""
    base_url: str | None = None


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider.

    This provider integrates with Anthropic's Claude API for chat completions.

    Attributes:
        config: Anthropic configuration.
        _client: Anthropic client instance.
    """

    def __init__(self, config: AnthropicConfig | None = None) -> None:
        """Initialize the Anthropic provider.

        Args:
            config: Anthropic configuration. Uses defaults if None.
        """
        super().__init__(config or AnthropicConfig())
        self.anthropic_config = config or AnthropicConfig()
        self._client = None
        self._async_client = None

    def _get_client(self) -> Any:
        """Get or create the Anthropic client.

        Returns:
            Anthropic client instance.
        """
        if self._client is None:
            try:
                import anthropic
            except ImportError as e:
                raise ImportError(
                    "Anthropic package not installed. Install with: pip install anthropic"
                ) from e

            api_key = self.anthropic_config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided")

            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if self.anthropic_config.base_url:
                client_kwargs["base_url"] = self.anthropic_config.base_url

            self._client = anthropic.Anthropic(**client_kwargs)

        return self._client

    def _get_async_client(self) -> Any:
        """Get or create the async Anthropic client.

        Returns:
            Async Anthropic client instance.
        """
        if self._async_client is None:
            try:
                import anthropic
            except ImportError as e:
                raise ImportError(
                    "Anthropic package not installed. Install with: pip install anthropic"
                ) from e

            api_key = self.anthropic_config.api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not provided")

            client_kwargs: dict[str, Any] = {"api_key": api_key}
            if self.anthropic_config.base_url:
                client_kwargs["base_url"] = self.anthropic_config.base_url

            self._async_client = anthropic.AsyncAnthropic(**client_kwargs)

        return self._async_client

    def _convert_messages(self, messages: list[LLMMessage]) -> tuple[str, list[dict]]:
        """Convert messages to Anthropic format.

        Anthropic uses a system prompt and a list of message content.

        Args:
            messages: List of LLM messages.

        Returns:
            Tuple of (system_prompt, anthropic_messages).
        """
        system_prompt = ""
        anthropic_messages = []

        for msg in messages:
            if msg.role.value == "system":
                system_prompt = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })

        return system_prompt, anthropic_messages

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
        system_prompt, anthropic_messages = self._convert_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        if system_prompt:
            request_params["system"] = system_prompt
        if self.config.max_tokens:
            request_params["max_tokens"] = self.config.max_tokens

        # Add any additional kwargs
        request_params.update(kwargs)

        # Make the request
        response = client.messages.create(**request_params)

        # Extract the response content
        content = ""
        if response.content:
            content = response.content[0].text if response.content[0].type == "text" else ""

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason or "",
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
        system_prompt, anthropic_messages = self._convert_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
        }
        if system_prompt:
            request_params["system"] = system_prompt
        if self.config.max_tokens:
            request_params["max_tokens"] = self.config.max_tokens

        # Add any additional kwargs
        request_params.update(kwargs)

        # Make the request
        response = await client.messages.create(**request_params)

        # Extract the response content
        content = ""
        if response.content:
            content = response.content[0].text if response.content[0].type == "text" else ""

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason or "",
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
        system_prompt, anthropic_messages = self._convert_messages(messages)

        # Build request parameters
        request_params: dict[str, Any] = {
            "model": self.config.model,
            "messages": anthropic_messages,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "stream": True,
        }
        if system_prompt:
            request_params["system"] = system_prompt
        if self.config.max_tokens:
            request_params["max_tokens"] = self.config.max_tokens

        # Add any additional kwargs
        request_params.update(kwargs)

        # Make the streaming request
        async with client.messages.stream(**request_params) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text
