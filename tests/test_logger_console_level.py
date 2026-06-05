"""Tests that the console log level is preserved across reconfigures."""

import importlib

import pytest


def _reload_logger() -> "object":
    import mounts.logger as logger_mod

    return importlib.reload(logger_mod)


def _stream_handlers(mod: "object") -> list:
    """Return loguru handlers whose sink is a stream (e.g. stderr), not a file."""
    return [
        h
        for h in mod.logger._core.handlers.values()
        if str(getattr(h, "_name", "")).startswith("<")
    ]


def test_set_log_directory_preserves_console_level(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """set_log_directory must keep the level chosen by a prior set_log_level."""
    monkeypatch.delenv("DISABLE_LOGGING", raising=False)
    mod = _reload_logger()

    mod.set_log_level("DEBUG")
    mod.set_log_directory(str(tmp_path))

    assert mod._console_level == "DEBUG"

    stream = _stream_handlers(mod)
    assert stream, "expected at least one stream handler"
    assert all(h.levelno == 10 for h in stream)  # DEBUG = 10


def test_enable_logging_preserves_console_level(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """enable_logging() after disable must restore handlers at the prior level."""
    monkeypatch.delenv("DISABLE_LOGGING", raising=False)
    mod = _reload_logger()
    mod.set_log_directory(str(tmp_path))

    mod.set_log_level("WARNING")
    mod.disable_logging()
    mod.enable_logging()

    assert mod._console_level == "WARNING"

    stream = _stream_handlers(mod)
    assert stream
    assert all(h.levelno == 30 for h in stream)  # WARNING = 30
