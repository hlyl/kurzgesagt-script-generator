"""Logging configuration utilities."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from ..config import settings


def configure_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Configure application-wide logging."""
    level_name = (log_level or settings.log_level).upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger("kurzgesagt")
    if logger.handlers:
        has_file_handler = any(
            isinstance(handler, RotatingFileHandler)
            for handler in logger.handlers
        )
        if not has_file_handler:
            log_path = Path(log_file) if log_file else Path(settings.log_file)
            if log_path:
                log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = RotatingFileHandler(
                    log_path, maxBytes=1_000_000, backupCount=3
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                    )
                )
                logger.addHandler(file_handler)
        return logger

    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = log_file
    else:
        log_path = Path(settings.log_file)

    if log_path:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path, maxBytes=1_000_000, backupCount=3
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the app namespace."""
    return logging.getLogger("kurzgesagt").getChild(name)
