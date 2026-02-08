"""Anthropic provider implementation."""

from __future__ import annotations

from typing import Any, List, Optional

from anthropic import Anthropic, APIError

from ...config import settings
from .base import ProviderConfigError, SceneParsingProvider


class AnthropicSceneProvider(SceneParsingProvider):
    """Anthropic-based provider for scene parsing."""

    def __init__(self, api_key: Optional[str] = None):
        resolved_key = api_key or settings.anthropic_api_key
        if not resolved_key or resolved_key == "your_api_key_here":
            raise ProviderConfigError(
                "ANTHROPIC_API_KEY must be set to use Claude scene parsing."
            )
        self.client = Anthropic(api_key=resolved_key)
        self.model = settings.anthropic_model
        self.max_tokens = settings.anthropic_max_tokens

    def complete(self, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
        except APIError as exc:
            raise RuntimeError(f"Claude API error: {exc}") from exc

        return self._extract_text(response.content)

    @staticmethod
    def _extract_text(content: List[Any]) -> str:
        for block in content:
            text = getattr(block, "text", None)
            if isinstance(text, str):
                return text
        raise RuntimeError("Claude response did not contain text content.")
