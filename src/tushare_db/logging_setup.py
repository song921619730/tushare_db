"""Structured logging setup using structlog.

Two log handlers:
- app.log: application events (50MB x 20 rotation)
- api_audit.log: API call audit trail (mirrors _meta.api_calls)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import structlog


def setup_logging(log_dir: str = "data/logs", level: str = "INFO") -> None:
    """Configure structlog with dual file + console handlers."""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

    # Console handler (human readable)
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging, level))
    console.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    )

    # File handler for app.log
    app_handler = RotatingFileHandler(
        log_path / "app.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=20,
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(logging.Formatter("%(message)s"))

    # File handler for api_audit.log
    audit_handler = RotatingFileHandler(
        log_path / "api_audit.log",
        maxBytes=50 * 1024 * 1024,
        backupCount=20,
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(logging.Formatter("%(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(console)
    root.addHandler(app_handler)
    root.addHandler(audit_handler)
