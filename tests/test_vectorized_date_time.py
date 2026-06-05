"""date/time columns must use vectorized .dt.strftime so NaT is handled."""

import pandas as pd
import pytest

from mounts.core import MountsProject


def test_nat_in_datetime_does_not_crash(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    """A NaT in either trace must propagate as NaN in date/time, not crash."""
    payload = {
        "data": [
            {
                "name": "Thermal",
                "x": ["2025-01-01T00:00:00", None],
                "y": [1.0, 2.0],
                "text": ["t1", "t2"],
            },
            {
                "name": "SO2",
                "x": ["2025-01-02T12:00:00"],
                "y": [0.5],
                "text": ["s1"],
            },
        ]
    }

    mp = MountsProject(output_dir=str(tmp_path), filter_values=None)
    monkeypatch.setattr(mp, "_get_json", lambda name, code: payload)

    df = mp.extract_single_volcano("alpha", "1")

    assert "date" in df.columns
    assert "time" in df.columns

    nat_rows = df[df.index.isna()] if df.index.hasnans else df.iloc[0:0]
    assert all(pd.isna(v) for v in nat_rows["date"])
    assert all(pd.isna(v) for v in nat_rows["time"])
