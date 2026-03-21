from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import get_settings

settings = get_settings()


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]
    model: str


class LLMService:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> LLMResponse:
        if self.config.provider == "mock":
            return LLMResponse(
                content="Mock response for: " + prompt[:100],
                usage={"prompt_tokens": 0, "completion_tokens": 1},
                model=self.config.model,
            )
        
        if self.config.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, history)
        
        raise ValueError(f"Unsupported provider: {self.config.provider}")

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[List[Dict[str, str]]],
    ) -> LLMResponse:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            },
            model=response.model,
        )
