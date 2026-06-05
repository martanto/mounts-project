"""Same-name volcanoes with distinct codes must survive extract+save."""

import pandas as pd
import pytest

from mounts.core import MountsProject


def test_same_name_different_codes_keep_separate_entries(
    monkeypatch: pytest.MonkeyPatch, fake_df: pd.DataFrame, tmp_path
) -> None:
    """Two volcanoes named identically but with different codes must not collide."""
    mp = MountsProject(output_dir=str(tmp_path), filter_values=None)

    def fake_single(name: str, code: str) -> pd.DataFrame:
        df = fake_df.copy()
        df["code"] = code
        return df

    monkeypatch.setattr(mp, "extract_single_volcano", fake_single)

    mp.extract(
        volcanoes=[
            {"name": "Krakatau", "code": "A"},
            {"name": "Krakatau", "code": "B"},
        ]
    )

    assert set(mp.data.keys()) == {"krakatau-a", "krakatau-b"}

    mp.save()
    written = sorted(p.name for p in (tmp_path / "csv").iterdir())
    assert written == ["krakatau-a.csv", "krakatau-b.csv"]
