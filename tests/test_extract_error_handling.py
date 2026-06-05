"""Tests for MountsProject.extract() per-volcano error isolation."""

import pandas as pd
import pytest

from mounts_project.core import MountsProject


def test_extract_isolates_per_volcano_failures(
    monkeypatch: pytest.MonkeyPatch, fake_df: pd.DataFrame, tmp_path
) -> None:
    """One failing volcano must not discard prior successes."""
    mp = MountsProject(output_dir=str(tmp_path), filter_values=None)

    calls: list[str] = []

    def fake_single(name: str, code: str) -> pd.DataFrame:
        calls.append(name)
        if name == "boom":
            raise RuntimeError("simulated network failure")
        return fake_df

    monkeypatch.setattr(mp, "extract_single_volcano", fake_single)

    mp.extract(
        volcanoes=[
            {"name": "alpha", "code": "1"},
            {"name": "boom", "code": "2"},
            {"name": "gamma", "code": "3"},
        ]
    )

    assert calls == ["alpha", "boom", "gamma"]
    assert set(mp.data.keys()) == {"alpha", "gamma"}
    assert [c["name"] for c in mp.catalogs] == ["alpha", "gamma"]
