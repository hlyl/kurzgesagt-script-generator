"""Application configuration using pydantic-settings."""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Kurzgesagt Script Generator"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API Keys
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    
    # Paths
    projects_dir: Path = Field(default=Path("./projects"))
    templates_dir: Path = Field(default=Path("./templates"))
    exports_dir: Path = Field(default=Path("./exports"))
    
    # API Settings
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4000
    anthropic_timeout: int = 60
    
    # Streamlit
    streamlit_server_port: int = 8501
    streamlit_server_address: str = "localhost"
    
    @field_validator("projects_dir", "templates_dir", "exports_dir")
    @classmethod
    def ensure_path_exists(cls, v: Path) -> Path:
        """Ensure directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @field_validator("anthropic_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or v == "your_api_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY must be set in .env file. "
                "Copy .env.example to .env and add your key."
            )
        return v


# Global settings instance
settings = Settings()