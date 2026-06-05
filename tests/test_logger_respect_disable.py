"""set_log_level / set_log_directory must respect a disabled logger."""

import importlib

import pytest


def _reload_logger() -> "object":
    import mounts.logger as logger_mod

    return importlib.reload(logger_mod)


def test_set_log_level_does_not_reattach_handlers_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DISABLE_LOGGING", raising=False)
    mod = _reload_logger()
    mod.set_log_directory(str(tmp_path))

    mod.disable_logging()
    assert mod.logger._core.handlers == {}

    mod.set_log_level("DEBUG")

    assert mod._console_level == "DEBUG"
    assert mod.logger._core.handlers == {}


def test_set_log_directory_does_not_reattach_handlers_when_disabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DISABLE_LOGGING", raising=False)
    mod = _reload_logger()
    mod.set_log_directory(str(tmp_path))

    mod.disable_logging()
    assert mod.logger._core.handlers == {}

    new_dir = tmp_path / "other"
    mod.set_log_directory(str(new_dir))

    assert mod.DEFAULT_LOG_DIR == str(new_dir)
    assert mod.logger._core.handlers == {}


def test_pending_level_and_dir_apply_after_enable(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.delenv("DISABLE_LOGGING", raising=False)
    mod = _reload_logger()

    mod.disable_logging()
    new_dir = tmp_path / "queued"
    mod.set_log_directory(str(new_dir))
    mod.set_log_level("WARNING")

    mod.enable_logging()

    assert mod.DEFAULT_LOG_DIR == str(new_dir)
    assert mod._console_level == "WARNING"
    assert len(mod.logger._core.handlers) > 0
