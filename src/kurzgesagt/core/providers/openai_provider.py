"""OpenAI provider implementation."""

from __future__ import annotations

from typing import Optional

from openai import OpenAI

from ...config import settings
from .base import ProviderConfigError, SceneParsingProvider


class OpenAISceneProvider(SceneParsingProvider):
    """OpenAI-based provider for scene parsing."""

    def __init__(self, api_key: Optional[str] = None):
        resolved_key = api_key or settings.openai_api_key
        if not resolved_key or resolved_key == "your_api_key_here":
            raise ProviderConfigError(
                "OPENAI_API_KEY must be set to use ChatGPT scene parsing."
            )
        self.client = OpenAI(api_key=resolved_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens

    def complete(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        message = response.choices[0].message
        if not message or not message.content:
            raise RuntimeError("OpenAI response did not contain message content.")
        return message.content
