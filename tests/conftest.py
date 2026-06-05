"""Shared pytest fixtures for the mounts test suite."""

import pandas as pd
import pytest


@pytest.fixture
def graph_json() -> dict:
    """Minimal MOUNTS graph payload with thermal at index 0 and SO2 at index 2."""
    return {
        "data": [
            {
                "x": ["2025-01-01T00:00:00", "2025-01-02T00:00:00"],
                "y": [1.0, 2.0],
                "text": ["t1", "t2"],
                "name": "Thermal",
            },
            {"x": [], "y": [], "text": [], "name": "other"},
            {
                "x": ["2025-01-01T00:00:00", "2025-01-02T00:00:00"],
                "y": [0.5, 1.5],
                "text": ["s1", "s2"],
                "name": "SO2",
            },
        ]
    }


@pytest.fixture
def fake_df() -> pd.DataFrame:
    """Tiny DataFrame shaped like extract_single_volcano output."""
    idx = pd.to_datetime(["2025-01-01", "2025-01-02"])
    return pd.DataFrame(
        {"value": [1.0, 2.0], "graph": ["a", "b"], "type": ["Thermal", "SO2"]},
        index=pd.Index(idx, name="datetime"),
    )
