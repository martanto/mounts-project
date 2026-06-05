"""The public SO2/thermal extractors must keep their existing contract."""

from mounts.utils import get_so2_values, get_thermal_values


def test_so2_and_thermal_share_extractor() -> None:
    payload = {
        "data": [
            {"name": "Thermal", "x": ["t1"], "y": [1.0], "text": ["a"]},
            {"name": "SO2", "x": ["s1"], "y": [0.5], "text": ["b"]},
        ]
    }

    so2 = get_so2_values(payload)
    thermal = get_thermal_values(payload)

    assert list(so2.columns) == ["datetime", "value", "graph", "type"]
    assert list(thermal.columns) == ["datetime", "value", "graph", "type"]
    assert so2["type"].iloc[0] == "SO2"
    assert thermal["type"].iloc[0] == "Thermal"
