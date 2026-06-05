"""Tests for atomic cache writes in MountsProject._get_json."""

import os
import json

import pytest

from mounts.core import MountsProject


class _FakeResponse:
    status_code = 200
    text = ""

    def raise_for_status(self) -> None:
        return None


def test_failed_write_leaves_no_corrupt_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """If json.dump raises mid-write, the final cache path must not exist."""
    monkeypatch.setattr(
        "mounts.core.requests.get", lambda url, timeout: _FakeResponse()
    )
    monkeypatch.setattr(
        "mounts.core.get_json_from_javascript", lambda r: {"data": []}
    )

    def boom(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("mounts.core.json.dump", boom)

    mp = MountsProject(output_dir=str(tmp_path))
    with pytest.raises(OSError, match="disk full"):
        mp._get_json("alpha", "1")

    json_dir = tmp_path / "json"
    final_files = [p for p in json_dir.iterdir() if p.suffix == ".json"]
    assert final_files == []


def test_utf8_roundtrip_through_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Non-ASCII characters survive the write/read cache round-trip on Windows."""
    payload = {"data": [{"name": "Soufrière", "label": "°C"}]}

    monkeypatch.setattr(
        "mounts.core.requests.get", lambda url, timeout: _FakeResponse()
    )
    monkeypatch.setattr("mounts.core.get_json_from_javascript", lambda r: payload)

    mp = MountsProject(output_dir=str(tmp_path), overwrite=False)
    assert mp._get_json("alpha", "1") == payload

    cache_path = tmp_path / "json" / "alpha-1.json"
    assert cache_path.exists()

    with open(cache_path, encoding="utf-8") as f:
        on_disk = json.load(f)
    assert on_disk == payload


def test_atomic_replace_uses_tmp_then_rename(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """Confirm that the cache write goes through a .tmp + os.replace path."""
    calls: list[str] = []

    real_replace = os.replace

    def tracking_replace(src, dst):
        calls.append(f"replace({src} -> {dst})")
        return real_replace(src, dst)

    monkeypatch.setattr(
        "mounts.core.requests.get", lambda url, timeout: _FakeResponse()
    )
    monkeypatch.setattr(
        "mounts.core.get_json_from_javascript", lambda r: {"data": []}
    )
    monkeypatch.setattr("mounts.core.os.replace", tracking_replace)

    mp = MountsProject(output_dir=str(tmp_path))
    mp._get_json("alpha", "1")

    assert any(".tmp" in c for c in calls)
