"""Mock for Anthropic API."""

from unittest.mock import Mock
import json


class MockAnthropicResponse:
    """Mock Anthropic API response."""
    
    def __init__(self, content_text: str):
        self.content = [Mock(text=content_text)]


class MockAnthropicClient:
    """Mock Anthropic client for testing."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.messages = Mock()
        self.messages.create = Mock(side_effect=self._mock_create)
    
    def _mock_create(self, **kwargs):
        """Mock message creation with sample response."""
        sample_response = {
            "scenes": [
                {
                    "number": 1,
                    "title": "TEST SCENE",
                    "purpose": "Test purpose",
                    "duration": 10,
                    "shots": [
                        {
                            "number": 1,
                            "narration": "Test narration",
                            "duration": 5,
                            "description": "Test description",
                            "key_elements": ["element1"],
                            "image_prompt": "Test image prompt",
                            "video_prompt": "Test video prompt",
                            "is_nested": False
                        }
                    ]
                }
            ]
        }
        
        return MockAnthropicResponse(json.dumps(sample_response))


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    """Fixture to mock Anthropic client."""
    monkeypatch.setattr("anthropic.Anthropic", MockAnthropicClient)