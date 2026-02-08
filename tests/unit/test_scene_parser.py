"""Unit tests for SceneParser key requirements."""

import pytest

from src.kurzgesagt.config import settings
from src.kurzgesagt.core import SceneParser


def test_scene_parser_requires_api_key_when_used(monkeypatch):
    """SceneParser should fail fast without an API key."""
    monkeypatch.setattr(settings, "anthropic_api_key", None)
    with pytest.raises(ValueError):
        SceneParser()


def test_scene_parser_accepts_explicit_api_key(mock_anthropic_client):
    """SceneParser should initialize when an API key is provided."""
    parser = SceneParser(api_key="test_key")
    assert parser.provider.client.api_key == "test_key"
