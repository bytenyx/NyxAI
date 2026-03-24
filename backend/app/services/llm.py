import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)


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
    parsed_json: Optional[Dict[str, Any]] = field(default=None, init=False)


class LLMService:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig(
            provider=settings.LLM_PROVIDER,
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self._openai_client = None

    def _get_openai_client(self):
        if self._openai_client is None and self.config.provider == "openai":
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._openai_client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        expect_json: bool = False,
    ) -> LLMResponse:
        request_id = f"llm_{int(time.time() * 1000)}"
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info(f"[LLM Request] request_id={request_id}")
        logger.info(f"[LLM Request] provider={self.config.provider} model={self.config.model}")
        logger.info(f"[LLM Request] expect_json={expect_json}")
        logger.debug(f"[LLM Request] prompt_length={len(prompt)} chars")
        if system_prompt:
            logger.debug(f"[LLM Request] system_prompt_length={len(system_prompt)} chars")
        if history:
            logger.debug(f"[LLM Request] history_length={len(history)} messages")
        
        if system_prompt:
            logger.debug(f"[LLM System Prompt]\n{system_prompt[:500]}{'...' if len(system_prompt) > 500 else system_prompt}")
        logger.debug(f"[LLM Prompt]\n{prompt[:1000]}{'...' if len(prompt) > 1000 else prompt}")
        
        try:
            if self.config.provider == "mock":
                logger.info(f"[LLM] Using mock provider")
                response = LLMResponse(
                    content=self._get_mock_response(prompt, expect_json),
                    usage={"prompt_tokens": 0, "completion_tokens": 1},
                    model=self.config.model,
                )
            elif self.config.provider == "openai":
                logger.info(f"[LLM] Calling OpenAI API")
                response = await self._generate_openai(prompt, system_prompt, history)
            else:
                error_msg = f"Unsupported provider: {self.config.provider}"
                logger.error(f"[LLM Error] {error_msg}")
                raise ValueError(error_msg)
            
            if expect_json:
                parse_start = time.time()
                response.parsed_json = self._parse_json_response(response.content)
                parse_duration = time.time() - parse_start
                logger.debug(f"[LLM] JSON parsing completed in {parse_duration:.3f}s")
            
            duration = time.time() - start_time
            logger.info(f"[LLM Response] request_id={request_id} duration={duration:.2f}s")
            logger.info(f"[LLM Response] usage={response.usage}")
            logger.debug(f"[LLM Response] content_length={len(response.content)} chars")
            logger.debug(f"[LLM Content]\n{response.content[:1000]}{'...' if len(response.content) > 1000 else response.content}")
            if response.parsed_json:
                logger.debug(f"[LLM Parsed JSON]\n{json.dumps(response.parsed_json, ensure_ascii=False, indent=2)[:500]}")
            logger.info("=" * 60)
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[LLM Error] request_id={request_id} duration={duration:.2f}s error={e}", exc_info=True)
            logger.error("=" * 60)
            raise

    def _get_mock_response(self, prompt: str, expect_json: bool) -> str:
        if expect_json:
            return json.dumps({
                "summary": "Mock调查摘要",
                "anomalies": [{"name": "mock_anomaly", "severity": "medium"}],
                "evidence": [{"description": "mock证据", "source": "mock"}],
                "root_cause": "Mock根因分析结果",
                "confidence": 0.85,
                "affected_components": ["component_a"],
                "reasoning_report": "Mock推理报告",
                "actions": [{"action_type": "investigate", "description": "进一步调查", "risk_level": "low"}],
                "risk_level": "low",
                "requires_confirmation": False,
                "rollback_plan": "Mock回滚方案",
            }, ensure_ascii=False)
        return "Mock response for: " + prompt[:100]

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None
        
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
        matches = re.findall(json_pattern, content)
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        json_objects = re.findall(r'\{[\s\S]*\}', content)
        for obj in json_objects:
            try:
                return json.loads(obj)
            except json.JSONDecodeError:
                continue
        
        return None

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        history: Optional[List[Dict[str, str]]],
    ) -> LLMResponse:
        client = self._get_openai_client()
        
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
