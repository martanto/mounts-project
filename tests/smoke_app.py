"""Smoke test the Streamlit dashboard via AppTest (no browser needed)."""
from importlib.resources import files

from streamlit.testing.v1 import AppTest


def main() -> None:
    dashboard_path = str(files("mounts").joinpath("dashboard.py"))
    at = AppTest.from_file(dashboard_path, default_timeout=30).run()

    assert not at.exception, f"App raised: {[str(e) for e in at.exception]}"
    assert at.title, "expected a st.title call"
    print("TITLE:", at.title[0].value)
    print("SIDEBAR_SELECTBOXES:", [s.label for s in at.sidebar.selectbox])
    print("SIDEBAR_RADIOS:", [r.label for r in at.sidebar.radio])
    print("METRICS:", len(at.metric))
    print("DATAFRAMES:", len(at.dataframe))

    radios = list(at.sidebar.radio)
    if radios:
        radios[0].set_value("SO2")
        at.run()
        assert not at.exception, f"After SO2 select: {[str(e) for e in at.exception]}"
        print("AFTER_SO2_OK metrics=", len(at.metric))

        list(at.sidebar.radio)[0].set_value("Thermal")
        at.run()
        assert not at.exception, f"After Thermal select: {[str(e) for e in at.exception]}"
        print("AFTER_THERMAL_OK metrics=", len(at.metric))

    print("ALL_OK")


if __name__ == "__main__":
    main()
