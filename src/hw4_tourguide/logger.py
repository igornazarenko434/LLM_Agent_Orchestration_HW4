"""
Logging Infrastructure (Mission M3.2)

Provides structured logging with rotating file handlers, optional error-only stream,
and console output. Ensures every LogRecord has an `event_tag` attribute to satisfy
the configured log format.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class _EventTagFilter(logging.Filter):
    """Ensure every log record has an event_tag attribute."""

    def __init__(self, default_tag: str = "General") -> None:
        super().__init__()
        self.default_tag = default_tag

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        if not hasattr(record, "event_tag"):
            record.event_tag = self.default_tag
        return True


def _ensure_parent(path: Path) -> None:
    """Create parent directories for the given file path."""
    path.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(config: Dict[str, Any], reset_existing: bool = True, log_base_dir: Optional[Path] = None) -> logging.Logger:
    """
    Configure the package logger using rotating file handlers and optional console output.
    Supports module-specific log files for agents, judge, apis, etc.

    Args:
        config: Logging configuration dictionary.
        reset_existing: Remove existing handlers before applying new configuration.
        log_base_dir: Optional base directory for log files (for run-specific logging).
                     If None, uses paths from config as-is.

    Returns:
        Configured package logger.
    """
    logger = logging.getLogger("hw4_tourguide")
    logger.setLevel(_parse_level(config.get("level", "INFO")))
    logger.propagate = False

    if reset_existing:
        logger.handlers.clear()

    fmt = config.get(
        "format",
        "%(asctime)s | %(levelname)-8s | %(name)s | %(event_tag)s | %(message)s",
    )
    formatter = logging.Formatter(fmt)
    filter_with_tag = _EventTagFilter()

    # Main rotating file handler
    if log_base_dir:
        main_path = log_base_dir / "logs" / "system.log"
    else:
        main_path = Path(config.get("file", "logs/system.log"))
    _ensure_parent(main_path)
    main_handler = RotatingFileHandler(
        filename=main_path,
        maxBytes=int(config.get("max_file_size_mb", 10)) * 1024 * 1024,
        backupCount=int(config.get("backup_count", 5)),
        encoding="utf-8",
    )
    main_handler.setFormatter(formatter)
    main_handler.addFilter(filter_with_tag)
    logger.addHandler(main_handler)

    # Error-only handler (file)
    if log_base_dir:
        error_path = log_base_dir / "logs" / "errors.log"
    else:
        error_path = Path(config.get("error_file", "logs/errors.log"))
    _ensure_parent(error_path)
    error_handler = RotatingFileHandler(
        filename=error_path,
        maxBytes=int(config.get("max_file_size_mb", 10)) * 1024 * 1024,
        backupCount=int(config.get("backup_count", 5)),
        encoding="utf-8",
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(filter_with_tag)
    logger.addHandler(error_handler)

    # Optional console handler
    if config.get("console_enabled", True):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.addFilter(filter_with_tag)
        logger.addHandler(console_handler)

    # Module-specific log files (agents, judge, apis, route_provider)
    modules_config = config.get("modules", {})
    _setup_module_loggers(modules_config, formatter, filter_with_tag, log_base_dir)

    return logger


def _setup_module_loggers(
    modules_config: Dict[str, Any],
    formatter: logging.Formatter,
    filter_with_tag: _EventTagFilter,
    log_base_dir: Optional[Path] = None
) -> None:
    """
    Set up module-specific loggers with dedicated log files.

    Args:
        modules_config: Module-specific logging configuration
        formatter: Log formatter to use
        filter_with_tag: Event tag filter to apply
        log_base_dir: Optional base directory for log files
    """
    module_mappings = {
        "agents": ["agent.video", "agent.song", "agent.knowledge"],
        "judge": ["judge"],
        "apis": ["api"],
        "route_provider": ["route_provider.google", "route_provider.cached", "route_provider.live"],
    }

    for module_key, logger_names in module_mappings.items():
        module_cfg = modules_config.get(module_key, {})
        if not module_cfg.get("enabled", True):
            continue

        if log_base_dir:
            log_path = log_base_dir / "logs" / f"{module_key}.log"
        else:
            log_file = module_cfg.get("file", f"logs/{module_key}.log")
            log_path = Path(log_file)
        _ensure_parent(log_path)

        level = _parse_level(module_cfg.get("level", "INFO"))
        max_bytes = int(module_cfg.get("max_bytes", 10485760))  # 10MB default
        backup_count = int(module_cfg.get("backup_count", 5))

        handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        handler.addFilter(filter_with_tag)

        # Attach handler to each module logger
        for logger_name in logger_names:
            full_name = f"hw4_tourguide.{logger_name}"
            child_logger = logging.getLogger(full_name)
            # Don't propagate to parent to avoid duplicate log entries
            child_logger.propagate = True  # Keep propagation for system.log
            child_logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a child logger under the package logger to inherit handlers.

    Args:
        name: Optional child name. If None, returns the package logger.
    """
    base = "hw4_tourguide"
    full_name = base if not name else f"{base}.{name}"
    return logging.getLogger(full_name)


def _parse_level(level: str) -> int:
    """Convert level string to logging level int."""
    return getattr(logging, level.upper(), logging.INFO)
