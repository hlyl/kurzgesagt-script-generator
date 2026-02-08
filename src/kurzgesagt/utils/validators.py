"""Validation utilities."""

import re
from pathlib import Path
from typing import Optional


class ValidationError(Exception):
    """Custom validation error."""

    pass


def validate_project_name(name: str) -> str:
    """
    Validate and sanitize project name.

    Rules:
    - Only alphanumeric, hyphens, underscores
    - No spaces (replaced with hyphens)
    - Maximum 100 characters
    - Not empty

    Args:
        name: Project name to validate

    Returns:
        Sanitized project name

    Raises:
        ValidationError: If name is invalid
    """
    if not name or not name.strip():
        raise ValidationError("Project name cannot be empty")

    # Replace spaces with hyphens
    sanitized = name.strip().replace(" ", "-")

    # Remove invalid characters
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "", sanitized)

    # Limit length
    if len(sanitized) > 100:
        sanitized = sanitized[:100]

    if not sanitized:
        raise ValidationError("Project name contains no valid characters")

    return sanitized


def validate_project_identifier(name: str) -> str:
    """
    Validate a project identifier used in file paths.

    Args:
        name: Project identifier

    Returns:
        Sanitized project name

    Raises:
        ValidationError: If identifier is unsafe
    """
    sanitized = validate_project_name(name)
    path = Path(name)
    if path.name != name or len(path.parts) != 1:
        raise ValidationError("Project identifier must be a single path segment")
    if sanitized != name:
        raise ValidationError("Project identifier contains invalid characters")
    return sanitized


def validate_optional_text(
    value: Optional[str], field_name: str, max_length: int = 200
) -> Optional[str]:
    """Validate optional text input with max length and trimming."""
    if value is None:
        return None
    trimmed = value.strip()
    if not trimmed:
        return None
    if len(trimmed) > max_length:
        raise ValidationError(
            f"{field_name} must be {max_length} characters or fewer"
        )
    return trimmed


def validate_voice_over_script(script: str, min_length: int = 10) -> None:
    """
    Validate voice-over script.

    Args:
        script: Script text
        min_length: Minimum character length

    Raises:
        ValidationError: If script is invalid
    """
    if not script or not script.strip():
        raise ValidationError("Voice-over script cannot be empty")

    if len(script.strip()) < min_length:
        raise ValidationError(
            f"Voice-over script must be at least {min_length} characters"
        )


def validate_file_path(
    path: Path, must_exist: bool = False, extension: Optional[str] = None
) -> Path:
    """
    Validate file path.

    Args:
        path: Path to validate
        must_exist: Whether file must exist
        extension: Required file extension (e.g., '.yaml')

    Returns:
        Validated path

    Raises:
        ValidationError: If path is invalid
    """
    if must_exist and not path.exists():
        raise ValidationError(f"File does not exist: {path}")

    if extension and path.suffix.lower() != extension.lower():
        raise ValidationError(
            f"File must have {extension} extension, got {path.suffix}"
        )

    return path


def estimate_reading_time(text: str, words_per_minute: int = 150) -> int:
    """
    Estimate time needed to read text aloud.

    Args:
        text: Text to estimate
        words_per_minute: Average speaking rate

    Returns:
        Estimated duration in seconds
    """
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return int(minutes * 60)
