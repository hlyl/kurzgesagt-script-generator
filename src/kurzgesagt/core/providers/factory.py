"""Provider factory utilities."""

from __future__ import annotations

from typing import Optional

from ...config import settings
from .anthropic_provider import AnthropicSceneProvider
from .base import ProviderConfigError, SceneParsingProvider
from .openai_provider import OpenAISceneProvider


def get_scene_provider(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
) -> SceneParsingProvider:
    """Return a scene parsing provider by name."""
    name = (provider_name or settings.scene_parser_provider).lower()

    if name in {"anthropic", "claude"}:
        return AnthropicSceneProvider(api_key=api_key)
    if name in {"openai", "chatgpt"}:
        return OpenAISceneProvider(api_key=api_key)

    raise ProviderConfigError(f"Unknown scene parser provider: {name}")
