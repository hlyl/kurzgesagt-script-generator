"""Unit tests for utility helpers."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from src.kurzgesagt.utils.logging import configure_logging, get_logger
from src.kurzgesagt.utils.validators import (
    ValidationError,
    estimate_reading_time,
    validate_file_path,
    validate_optional_text,
    validate_project_identifier,
    validate_project_name,
    validate_voice_over_script,
)


def _reset_logger() -> logging.Logger:
    logger = logging.getLogger("kurzgesagt")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    return logger


def test_configure_logging_adds_handlers(tmp_path: Path) -> None:
    _reset_logger()
    log_file = tmp_path / "app.log"

    logger = configure_logging(log_level="INFO", log_file=log_file)

    assert logger.name == "kurzgesagt"
    assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    assert any(
        h.__class__.__name__ == "RotatingFileHandler" for h in logger.handlers
    )
    logger.info("hello")
    assert log_file.exists()


def test_configure_logging_is_idempotent(tmp_path: Path) -> None:
    _reset_logger()
    logger = configure_logging(log_level="INFO", log_file=tmp_path / "app.log")
    handler_count = len(logger.handlers)

    logger_again = configure_logging(log_level="DEBUG")
    assert logger_again is logger
    assert len(logger_again.handlers) == handler_count


def test_get_logger_child() -> None:
    _reset_logger()
    configure_logging(log_level="INFO")

    child = get_logger("unit")
    assert child.name.endswith("kurzgesagt.unit")


def test_validate_project_name() -> None:
    assert validate_project_name("My Project") == "My-Project"
    assert validate_project_name("clean_name") == "clean_name"
    assert validate_project_name("a" * 120) == "a" * 100

    with pytest.raises(ValidationError):
        validate_project_name("   ")


def test_validate_project_identifier() -> None:
    assert validate_project_identifier("project_1") == "project_1"

    with pytest.raises(ValidationError):
        validate_project_identifier("../project")
    with pytest.raises(ValidationError):
        validate_project_identifier("project name")


def test_validate_optional_text() -> None:
    assert validate_optional_text(None, "Notes") is None
    assert validate_optional_text("   ", "Notes") is None
    assert validate_optional_text("  ok ", "Notes") == "ok"

    with pytest.raises(ValidationError):
        validate_optional_text("x" * 201, "Notes", max_length=200)


def test_validate_voice_over_script() -> None:
    validate_voice_over_script("Valid script with enough length", min_length=10)

    with pytest.raises(ValidationError):
        validate_voice_over_script("", min_length=10)
    with pytest.raises(ValidationError):
        validate_voice_over_script("short", min_length=10)


def test_validate_file_path(tmp_path: Path) -> None:
    file_path = tmp_path / "config.yaml"
    file_path.write_text("test")

    assert validate_file_path(file_path, must_exist=True, extension=".yaml") == file_path

    with pytest.raises(ValidationError):
        validate_file_path(tmp_path / "missing.yaml", must_exist=True)
    with pytest.raises(ValidationError):
        validate_file_path(file_path, extension=".json")


def test_estimate_reading_time() -> None:
    text = "word " * 150
    assert estimate_reading_time(text, words_per_minute=150) == 60