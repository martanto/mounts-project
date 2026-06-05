"""Tests for logger._logging_enabled / DISABLE_LOGGING env-var synchronisation."""

import importlib

import pytest


def test_logging_enabled_mirrors_env_at_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When DISABLE_LOGGING=1 is set before import, _logging_enabled must be False."""
    monkeypatch.setenv("DISABLE_LOGGING", "1")

    import mounts.logger as logger_mod

    reloaded = importlib.reload(logger_mod)

    assert reloaded._logging_enabled is False


def test_enable_logging_installs_handlers_after_env_disable(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """enable_logging() must install handlers even when DISABLE_LOGGING was set at import."""
    monkeypatch.setenv("DISABLE_LOGGING", "1")

    import mounts.logger as logger_mod

    reloaded = importlib.reload(logger_mod)
    reloaded.set_log_directory(str(tmp_path))

    reloaded.enable_logging()

    assert reloaded._logging_enabled is True
    assert len(reloaded.logger._core.handlers) > 0
