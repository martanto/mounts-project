"""Tests for the HTTP behaviour of MountsProject._get_json."""

import pytest
import requests

from mounts.core import MountsProject, _REQUEST_TIMEOUT


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code}")


def test_get_json_passes_timeout(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """requests.get must be called with the module-level timeout constant."""
    seen: dict = {}

    def fake_get(url, timeout):
        seen["url"] = url
        seen["timeout"] = timeout
        raise requests.exceptions.Timeout("boom")

    monkeypatch.setattr("mounts.core.requests.get", fake_get)

    mp = MountsProject(output_dir=str(tmp_path))
    with pytest.raises(requests.exceptions.Timeout):
        mp._get_json("alpha", "1")

    assert seen["timeout"] == _REQUEST_TIMEOUT


def test_get_json_raises_on_non_2xx(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """A 500 response must raise HTTPError before any parsing is attempted."""

    def fake_get(url, timeout):
        return _FakeResponse(status_code=500, text="<html>oops</html>")

    monkeypatch.setattr("mounts.core.requests.get", fake_get)

    mp = MountsProject(output_dir=str(tmp_path))
    with pytest.raises(requests.exceptions.HTTPError):
        mp._get_json("alpha", "1")
