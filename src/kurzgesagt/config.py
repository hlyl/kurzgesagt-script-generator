"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Application
    app_name: str = "Kurzgesagt Script Generator"
    app_version: str = "0.1.0"
    debug: bool = True

    # API Keys
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")

    # Paths
    projects_dir: Path = Field(default=Path("./projects"))
    templates_dir: Path = Field(default=Path("./templates"))
    exports_dir: Path = Field(default=Path("./exports"))

    # API Settings
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4000
    anthropic_timeout: int = 60

    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4000
    openai_timeout: int = 60

    openai_image_model: str = "gpt-image-1"
    openai_image_size: str = "1024x1024"

    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_image_size: str = "1024x1024"
    gemini_image_model_alt: str = "gemini-3-pro-image-preview"
    gemini_image_aspect_ratio: str = "1:1"
    gemini_image_resolution: str = "1K"

    scene_parser_provider: str = "anthropic"

    # Streamlit
    streamlit_server_port: int = 8501
    streamlit_server_address: str = "localhost"

    # Logging
    log_level: str = "DEBUG"
    log_file: str = "logs/app.log"

    @field_validator("projects_dir", "templates_dir", "exports_dir")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key when provided."""
        if v is None:
            return None
        if not v or v == "your_api_key_here":
            return None
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate OpenAI API key when provided."""
        if v is None:
            return None
        if not v or v == "your_api_key_here":
            return None
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate Gemini API key when provided."""
        if v is None:
            return None
        if not v or v == "your_gemini_api_key_here":
            return None
        return v


# Global settings instance
settings = Settings()
