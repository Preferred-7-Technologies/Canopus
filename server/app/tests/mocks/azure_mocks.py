from unittest.mock import Mock, AsyncMock

class MockTextAnalyticsClient:
    def analyze_sentiment(self, texts):
        mock_response = Mock()
        mock_response.sentiment = "positive"
        mock_response.confidence_scores = Mock(positive=0.9, neutral=0.1, negative=0.0)
        return [mock_response]

    def recognize_entities(self, texts):
        mock_response = Mock()
        mock_response.entities = []
        return [mock_response]

class MockChatCompletionsClient:
    def complete(self, messages, tools=None, model=None):
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        return mock_response

def get_mock_azure_clients():
    return {
        'text_analytics': MockTextAnalyticsClient(),
        'chat_completions': MockChatCompletionsClient()
    }
