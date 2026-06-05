"""filter_values semantics: inclusive lower bound, zero keeps zeros."""

import pandas as pd
import pytest

from mounts.core import MountsProject


def _payload() -> dict:
    return {
        "data": [
            {
                "name": "Thermal",
                "x": ["2025-01-01", "2025-01-02", "2025-01-03"],
                "y": [0.0, 0.05, 0.2],
                "text": ["a", "b", "c"],
            },
            {
                "name": "SO2",
                "x": ["2025-01-04"],
                "y": [0.1],
                "text": ["d"],
            },
        ]
    }


def test_filter_values_zero_keeps_zero_rows(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    mp = MountsProject(output_dir=str(tmp_path), filter_values=0)
    monkeypatch.setattr(mp, "_get_json", lambda name, code: _payload())

    df = mp.extract_single_volcano("alpha", "1")
    assert sorted(df["value"].tolist()) == [0.0, 0.05, 0.1, 0.2]


def test_filter_values_default_drops_low_readings(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    mp = MountsProject(output_dir=str(tmp_path))  # default 0.1
    monkeypatch.setattr(mp, "_get_json", lambda name, code: _payload())

    df = mp.extract_single_volcano("alpha", "1")
    assert sorted(df["value"].tolist()) == [0.1, 0.2]


def test_filter_values_none_keeps_everything(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    mp = MountsProject(output_dir=str(tmp_path), filter_values=None)
    monkeypatch.setattr(mp, "_get_json", lambda name, code: _payload())

    df = mp.extract_single_volcano("alpha", "1")
    assert len(df) == 4
