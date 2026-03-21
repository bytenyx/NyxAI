import pytest
import json

from app.services.llm import LLMService, LLMConfig


class TestLLMService:
    @pytest.fixture
    def mock_service(self):
        return LLMService(LLMConfig(provider="mock", model="mock"))

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
    async def test_mock_response_contains_expected_fields(self, mock_service):
        response = await mock_service.generate(
            prompt="测试",
            expect_json=True,
        )
        
        assert "summary" in response.parsed_json
        assert "anomalies" in response.parsed_json
        assert "confidence" in response.parsed_json

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
