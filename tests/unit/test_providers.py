"""Unit tests for provider implementations."""

from types import SimpleNamespace

from src.kurzgesagt.config import settings
from src.kurzgesagt.core.providers import get_scene_provider
from src.kurzgesagt.core.providers.anthropic_provider import AnthropicSceneProvider
from src.kurzgesagt.core.providers.openai_provider import OpenAISceneProvider


class _MockAnthropicResponse:
    def __init__(self, text: str):
        self.content = [SimpleNamespace(text=text)]


class _MockAnthropicClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **_kwargs):
        return _MockAnthropicResponse("ok")


class _MockOpenAIChat:
    def __init__(self):
        self.completions = SimpleNamespace(create=self._create)

    def _create(self, **_kwargs):
        message = SimpleNamespace(content="ok")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _MockOpenAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chat = _MockOpenAIChat()


def test_anthropic_provider_complete(monkeypatch):
    monkeypatch.setattr(
        "src.kurzgesagt.core.providers.anthropic_provider.Anthropic",
        _MockAnthropicClient,
    )
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")

    provider = AnthropicSceneProvider()
    assert provider.complete("prompt") == "ok"


def test_openai_provider_complete(monkeypatch):
    monkeypatch.setattr(
        "src.kurzgesagt.core.providers.openai_provider.OpenAI",
        _MockOpenAIClient,
    )
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    provider = OpenAISceneProvider()
    assert provider.complete("prompt") == "ok"


def test_provider_factory(monkeypatch):
    monkeypatch.setattr(
        "src.kurzgesagt.core.providers.anthropic_provider.Anthropic",
        _MockAnthropicClient,
    )
    monkeypatch.setattr(settings, "anthropic_api_key", "test-key")

    provider = get_scene_provider("anthropic")
    assert provider.complete("prompt") == "ok"
