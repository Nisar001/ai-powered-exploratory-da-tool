"""
Structured Logging Module

Provides centralized, structured logging with context enrichment,
log rotation, and multiple output formats.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger

from src.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds additional context to log records
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """Add custom fields to log record"""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record["app_name"] = settings.app.app_name
        log_record["app_version"] = settings.app.app_version
        log_record["environment"] = settings.app.app_env

        # Add context if available
        if hasattr(record, "job_id"):
            log_record["job_id"] = record.job_id
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id


class LoggerManager:
    """
    Centralized logger management system
    """

    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def get_logger(
        cls, name: str, context: Optional[Dict[str, Any]] = None
    ) -> logging.Logger:
        """
        Get or create a logger with the specified name

        Args:
            name: Logger name (typically module name)
            context: Optional context to be added to all log records

        Returns:
            Configured logger instance
        """
        if name in cls._loggers:
            return cls._loggers[name]

        logger = logging.getLogger(name)
        logger.setLevel(settings.app.log_level)

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.app.log_level)

        if settings.app.app_env == "production":
            # JSON format for production
            json_formatter = CustomJsonFormatter(
                "%(timestamp)s %(level)s %(name)s %(message)s"
            )
            console_handler.setFormatter(json_formatter)
        else:
            # Human-readable format for development
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # File handler if configured
        if settings.monitoring.log_file_path:
            try:
                file_handler = logging.FileHandler(
                    settings.monitoring.log_file_path, encoding="utf-8"
                )
                file_handler.setLevel(settings.app.log_level)

                if settings.app.app_env == "production":
                    file_handler.setFormatter(json_formatter)
                else:
                    file_handler.setFormatter(formatter)

                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Failed to create file handler: {e}")

        # Add context adapter if provided
        if context:
            logger = logging.LoggerAdapter(logger, context)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def add_context(
        cls, logger: logging.Logger, **kwargs: Any
    ) -> logging.LoggerAdapter:
        """
        Add context to an existing logger

        Args:
            logger: Logger to add context to
            **kwargs: Context key-value pairs

        Returns:
            LoggerAdapter with context
        """
        return logging.LoggerAdapter(logger, kwargs)


def get_logger(name: str, **context: Any) -> logging.Logger:
    """
    Convenience function to get a logger

    Args:
        name: Logger name (typically __name__)
        **context: Optional context to be added to all log records

    Returns:
        Configured logger instance
    """
    return LoggerManager.get_logger(name, context or None)


# Configure root logger
def configure_logging() -> None:
    """
    Configure application-wide logging settings
    """
    logging.basicConfig(
        level=settings.app.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)


# Initialize logging on module import
configure_logging()
