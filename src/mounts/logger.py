"""Package-wide loguru logging configuration.

Sets up three handlers at import time (console + daily-rotated general log +
daily-rotated error log under ``./logs/``). Configuration is centralised in
:func:`_configure_handlers` so :func:`set_log_level`, :func:`set_log_directory`,
:func:`disable_logging`, and :func:`enable_logging` all rebuild the same handler
set. Set ``DISABLE_LOGGING=1`` in the environment to skip handler setup (used so
subprocess workers inherit the disabled state).
"""

import os
import sys

from mounts.utils import ensure_dir

from loguru import logger


# Retention periods for log files.
_GENERAL_LOG_RETENTION = "30 days"
_ERROR_LOG_RETENTION = "90 days"

# Tracks whether logging is currently enabled. Initialised from DISABLE_LOGGING
# so a subprocess that inherits the env var doesn't end up with the flag and the
# environment disagreeing (which made enable_logging() a silent no-op).
_logging_enabled: bool = os.environ.get("DISABLE_LOGGING") != "1"

# Current console log level. set_log_level() updates this; every other
# reconfigure path (set_log_directory, enable_logging) reads it so a prior
# level choice is preserved across reconfigures.
_console_level: str = "INFO"

DEFAULT_LOG_DIR: str = str(ensure_dir(os.path.join(os.getcwd(), "logs")))

_FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.remove()


def _configure_handlers(log_dir: str, console_level: str = "INFO") -> None:
    """Remove all existing handlers and re-add console + file handlers.

    Centralises handler configuration so that module-level setup, set_log_level(),
    and set_log_directory() all use the same retention periods and formats.

    Args:
        log_dir (str): Directory path for log file output.
        console_level (str, optional): Log level for the console handler.
            Defaults to "INFO".
    """
    logger.remove()

    logger.add(
        sys.stderr,
        format=_CONSOLE_FORMAT,
        level=console_level.upper(),
        colorize=True,
    )

    logger.add(
        os.path.join(log_dir, "mounts_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=_GENERAL_LOG_RETENTION,
        compression="zip",
        format=_FILE_FORMAT,
        level="DEBUG",
        enqueue=True,
    )

    logger.add(
        os.path.join(log_dir, "errors_{time:YYYY-MM-DD}.log"),
        rotation="00:00",
        retention=_ERROR_LOG_RETENTION,
        compression="zip",
        format=_FILE_FORMAT,
        level="ERROR",
        enqueue=True,
    )


# Skip if the parent process disabled logging (env var is inherited by workers).
if os.environ.get("DISABLE_LOGGING") != "1":
    _configure_handlers(DEFAULT_LOG_DIR, console_level=_console_level)


def get_logger():
    """Return the package-wide loguru logger instance.

    Returns:
        loguru.Logger: The configured logger instance with console and file handlers.
    """
    return logger


def set_log_level(level: str) -> None:
    """Change the console log level dynamically.

    Removes all existing handlers and re-adds them with the new console level.
    File handlers retain their original levels.

    Args:
        level (str): Desired log level for the console handler. One of
            ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``, or
            ``"CRITICAL"``. Case-insensitive.

    Note:
        When logging is currently disabled (via :func:`disable_logging`), the
        new level is recorded for the next :func:`enable_logging` call but no
        handlers are added — the disable contract is preserved.
    """
    global _console_level
    _console_level = level.upper()
    if not _logging_enabled:
        return
    _configure_handlers(DEFAULT_LOG_DIR, console_level=_console_level)


def set_log_directory(log_dir: str) -> None:
    """Change the log file directory dynamically.

    Updates the global ``DEFAULT_LOG_DIR``, creates the directory if needed,
    then reconfigures all handlers to write to the new location.

    Args:
        log_dir (str): Absolute or relative path to the new log directory.
            Created automatically if it does not exist.

    Note:
        When logging is currently disabled (via :func:`disable_logging`), the
        new directory is recorded for the next :func:`enable_logging` call but
        no handlers are added — the disable contract is preserved.
    """
    global DEFAULT_LOG_DIR
    DEFAULT_LOG_DIR = str(ensure_dir(os.path.abspath(log_dir)))
    if not _logging_enabled:
        return
    _configure_handlers(DEFAULT_LOG_DIR, console_level=_console_level)
    logger.info(f"Log directory changed to: {DEFAULT_LOG_DIR}")


def disable_logging() -> None:
    """Disable all logging output globally.

    Remove all active loguru handlers so no messages are written to the
    console or log files. Call :func:`enable_logging` to restore handlers.
    """
    global _logging_enabled
    _logging_enabled = False
    os.environ["DISABLE_LOGGING"] = "1"
    logger.remove()


def enable_logging() -> None:
    """Re-enable logging after a previous :func:`disable_logging` call.

    Restore console and file handlers using the current ``DEFAULT_LOG_DIR``.
    Has no effect if logging is already enabled.
    """
    global _logging_enabled
    if not _logging_enabled:
        _logging_enabled = True
        os.environ.pop("DISABLE_LOGGING", None)
        _configure_handlers(DEFAULT_LOG_DIR, console_level=_console_level)
