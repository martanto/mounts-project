"""Tests for the name-based trace lookup in mounts.utils."""

import pytest

from mounts.utils import get_so2_values, get_thermal_values


def test_get_so2_values_finds_trace_after_reorder() -> None:
    """SO2 lookup must work regardless of the trace's position in data[]."""
    payload = {
        "data": [
            {"x": [], "y": [], "text": [], "name": "filler"},
            {"x": ["2025"], "y": [0.5], "text": ["s1"], "name": "SO2 column"},
            {"x": ["2025"], "y": [1.0], "text": ["t1"], "name": "Thermal alert"},
        ]
    }

    df = get_so2_values(payload)
    assert df["value"].tolist() == [0.5]
    assert df["type"].iloc[0] == "SO2"


def test_get_thermal_values_finds_trace_after_reorder() -> None:
    """Thermal lookup must work regardless of trace order."""
    payload = {
        "data": [
            {"x": ["2025"], "y": [9.9], "text": ["s1"], "name": "so2"},
            {"x": [], "y": [], "text": [], "name": "other"},
            {"x": ["2025"], "y": [2.0], "text": ["t1"], "name": "Thermal"},
        ]
    }

    df = get_thermal_values(payload)
    assert df["value"].tolist() == [2.0]
    assert df["type"].iloc[0] == "Thermal"


def test_missing_trace_raises_keyerror() -> None:
    """Loud failure when MOUNTS changes its trace naming."""
    payload = {"data": [{"x": [], "y": [], "text": [], "name": "Cloud cover"}]}

    with pytest.raises(KeyError, match="so2"):
        get_so2_values(payload)
