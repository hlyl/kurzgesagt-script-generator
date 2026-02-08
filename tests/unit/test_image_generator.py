"""Unit tests for image generation."""

from types import SimpleNamespace

import pytest

from src.kurzgesagt.config import settings
from src.kurzgesagt.core.image_generator import ImageGenerator


class _MockImage:
    def save(self, buffer, format="PNG"):
        buffer.write(b"image-bytes")


class _MockPart:
    inline_data = True

    def as_image(self):
        return _MockImage()


class _MockModels:
    def generate_content(self, **_kwargs):
        return SimpleNamespace(parts=[_MockPart()])


class _MockGenAIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.models = _MockModels()


def test_generate_image_bytes(monkeypatch):
    monkeypatch.setattr(
        "src.kurzgesagt.core.image_generator.genai.Client",
        _MockGenAIClient,
    )
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    generator = ImageGenerator()
    assert generator.generate_image_bytes("prompt") == b"image-bytes"


def test_save_shot_image(monkeypatch, temp_dir):
    monkeypatch.setattr(
        "src.kurzgesagt.core.image_generator.genai.Client",
        _MockGenAIClient,
    )
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    generator = ImageGenerator()
    image_path = generator.save_shot_image(
        project_dir=temp_dir,
        scene_number=1,
        shot_number=2,
        prompt="prompt",
    )

    assert image_path.exists()
    assert image_path.read_bytes() == b"image-bytes"


def test_generate_image_bytes_includes_style_context(monkeypatch):
    captured = {}

    class _CapturingModels:
        def generate_content(self, **kwargs):
            captured["contents"] = kwargs.get("contents")
            return SimpleNamespace(parts=[_MockPart()])

    class _CapturingClient:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.models = _CapturingModels()

    monkeypatch.setattr(
        "src.kurzgesagt.core.image_generator.genai.Client",
        _CapturingClient,
    )
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")

    generator = ImageGenerator()
    generator.generate_image_bytes(
        "base prompt",
        style_context="Layered scene, parallax-ready. No text.",
    )

    assert captured["contents"][0] == (
        "base prompt\n\n"
        "Style guide: Layered scene, parallax-ready. No text."
    )
