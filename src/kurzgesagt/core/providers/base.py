"""Provider interfaces for scene parsing."""

from __future__ import annotations

from typing import Protocol


class ProviderConfigError(RuntimeError):
    """Raised when a provider is not properly configured."""


class SceneParsingProvider(Protocol):
    """Interface for provider-specific completion calls."""

    def complete(self, prompt: str) -> str:
        """Return the provider response text for the prompt."""
        ...
