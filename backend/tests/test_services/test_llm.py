import pytest
import json

from app.services.llm import LLMService, LLMConfig


class TestLLMService:
    @pytest.fixture
    def mock_service(self):
        return LLMService(LLMConfig(provider="mock", model="mock"))

    @pytest.fixture
    def mock_service_with_delay(self):
        return LLMService(LLMConfig(provider="mock", model="mock", mock_delay=0.1))

    @pytest.mark.asyncio
    async def test_generate_returns_response(self, mock_service):
        response = await mock_service.generate(
            prompt="测试提示",
        )
        
        assert response.content is not None
        assert response.model == "mock"

    @pytest.mark.asyncio
    async def test_generate_with_expect_json(self, mock_service):
        response = await mock_service.generate(
            prompt="测试提示",
            expect_json=True,
        )
        
        assert response.parsed_json is not None
        assert isinstance(response.parsed_json, dict)

    @pytest.mark.asyncio
    async def test_mock_investigation_response(self, mock_service):
        response = await mock_service.generate(
            prompt="请调查以下问题：服务响应缓慢",
            expect_json=True,
        )
        
        assert response.parsed_json is not None
        assert "anomalies" in response.parsed_json
        assert "evidence" in response.parsed_json
        assert "summary" in response.parsed_json
        assert "confidence" in response.parsed_json
        assert len(response.parsed_json["anomalies"]) > 0

    @pytest.mark.asyncio
    async def test_mock_diagnosis_response(self, mock_service):
        response = await mock_service.generate(
            prompt="请分析以下问题的根因：服务异常",
            expect_json=True,
        )
        
        assert response.parsed_json is not None
        assert "root_cause" in response.parsed_json
        assert "confidence" in response.parsed_json
        assert "affected_components" in response.parsed_json
        assert "evidence_chain" in response.parsed_json

    @pytest.mark.asyncio
    async def test_mock_recovery_response(self, mock_service):
        response = await mock_service.generate(
            prompt="请为以下问题制定恢复方案：数据库连接池耗尽",
            expect_json=True,
        )
        
        assert response.parsed_json is not None
        assert "actions" in response.parsed_json
        assert "risk_level" in response.parsed_json
        assert "rollback_plan" in response.parsed_json
        assert len(response.parsed_json["actions"]) > 0

    @pytest.mark.asyncio
    async def test_mock_response_with_delay(self, mock_service_with_delay):
        import time
        start = time.time()
        response = await mock_service_with_delay.generate(
            prompt="测试延迟",
            expect_json=True,
        )
        elapsed = time.time() - start
        
        assert elapsed >= 0.1
        assert response.parsed_json is not None

    @pytest.mark.asyncio
    async def test_mock_default_response(self, mock_service):
        response = await mock_service.generate(
            prompt="普通问题",
            expect_json=True,
        )
        
        assert response.parsed_json is not None
        assert "summary" in response.parsed_json
        assert "anomalies" in response.parsed_json
        assert "root_cause" in response.parsed_json

    def test_parse_json_from_plain_json(self, mock_service):
        json_str = '{"key": "value", "number": 123}'
        result = mock_service._parse_json_response(json_str)
        
        assert result == {"key": "value", "number": 123}

    def test_parse_json_from_markdown_code_block(self, mock_service):
        content = '''```json
{"key": "value", "number": 123}
```'''
        result = mock_service._parse_json_response(content)
        
        assert result == {"key": "value", "number": 123}

    def test_parse_json_from_text_with_json(self, mock_service):
        content = '这是一些文本 {"key": "value"} 更多文本'
        result = mock_service._parse_json_response(content)
        
        assert result == {"key": "value"}

    def test_parse_json_returns_none_for_invalid(self, mock_service):
        content = "这不是JSON"
        result = mock_service._parse_json_response(content)
        
        assert result is None

    def test_parse_json_returns_none_for_empty(self, mock_service):
        result = mock_service._parse_json_response("")
        
        assert result is None

    def test_client_reuse(self, mock_service):
        assert mock_service._openai_client is None
        
        mock_service.config.provider = "openai"
        mock_service.config.api_key = "test-key"
        client1 = mock_service._get_openai_client()
        client2 = mock_service._get_openai_client()
        
        assert client1 is client2
