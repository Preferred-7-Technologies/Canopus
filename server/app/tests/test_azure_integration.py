import pytest
from unittest.mock import AsyncMock, Mock, patch
from ..services.azure_ai import AzureAIService, ModelType
from typing import Dict, Any

@pytest.fixture
def mock_text_response():
    response = Mock()
    response.sentiment = "positive"
    response.confidence_scores = Mock(positive=0.9, neutral=0.1, negative=0.0)
    return response

@pytest.fixture
def mock_ai_response():
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test response"
    response.choices[0].finish_reason = "stop"
    return response

class TestAzureAIService:
    @pytest.mark.asyncio
    async def test_process_request(self, mock_ai_response):
        service = AzureAIService()
        
        with patch.object(service.clients[ModelType.CODESTRAL.value], 'complete', 
                         return_value=mock_ai_response):
            result = await service.process_request(
                messages=[{"role": "user", "content": "Hello"}],
                model_type=ModelType.CODESTRAL
            )
            
            assert "result" in result
            assert result["result"]["content"] == "Test response"
