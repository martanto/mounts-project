"""Streamlit dashboard for the MOUNTS scrape outputs.

Reads ``output/all-volcanoes.csv`` (falling back to the XLSX) and lets the user
explore SO2 and thermal time series per volcano. Run with:

    uv run streamlit run app.py
"""

import os

from mounts_project import MountsProject, __url__, __author__, __version__
from mounts_project.constants import (
    CSV_PATH,
    SO2_UNIT,
    SO2_COLOR,
    XLSX_PATH,
    OUTPUT_DIR,
    THERMAL_UNIT,
    THERMAL_COLOR,
)

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


@st.cache_data
def load_data() -> pd.DataFrame | None:
    """Read the merged all-volcanoes export into a single DataFrame.

    Returns ``None`` when neither the CSV nor the XLSX export exists so the UI
    can render an empty-state panel with a Refresh button.
    """
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH, parse_dates=["datetime"])
    elif os.path.exists(XLSX_PATH):
        df = pd.read_excel(XLSX_PATH, parse_dates=["datetime"])
    else:
        return None

    df = df.set_index("datetime").sort_index()
    df["code"] = df["code"].astype(str)
    return df


def refresh_data() -> None:
    """Re-run extraction, persist to CSV, and clear the Streamlit data cache."""
    with st.spinner("Fetching latest MOUNTS data (this can take ~1 minute)…"):
        MountsProject(overwrite=True).extract().save(filetype="csv")
    st.cache_data.clear()
    st.toast("Data refreshed.")


def render_empty_state() -> None:
    """Panel shown when no extracted data is available on disk."""
    st.title("MOUNTS Dashboard")
    st.info(
        f"No extracted data found in `{OUTPUT_DIR}`. "
        "Click **Refresh data** to fetch from mounts-project.com, or run "
        "`MountsProject().extract().save('csv')` from a Python shell first."
    )
    if st.button("Refresh data", type="primary"):
        refresh_data()
        st.rerun()


def render_metrics(df: pd.DataFrame, data_type: str) -> None:
    """Render a row of summary metrics for one type's slice."""
    unit = SO2_UNIT if data_type == "SO2" else THERMAL_UNIT
    cols = st.columns(4)
    cols[0].metric(f"{data_type} observations", f"{len(df):,}")
    cols[1].metric(
        f"{data_type} last observation",
        df.index.max().strftime("%Y-%m-%d %H:%M") if len(df) else "—",
    )
    cols[2].metric(
        f"{data_type} max ({unit})", f"{df['value'].max():,.2f}" if len(df) else "—"
    )
    cols[3].metric(
        f"{data_type} mean ({unit})", f"{df['value'].mean():,.2f}" if len(df) else "—"
    )


def render_chart(
    df: pd.DataFrame,
    data_type: str,
    volcano: str,
    mode: str,
    marker_size: int,
) -> None:
    """Render the Plotly time series for the selected type(s)."""
    if data_type in ("SO2", "Thermal"):
        unit = SO2_UNIT if data_type == "SO2" else THERMAL_UNIT
        color = SO2_COLOR if data_type == "SO2" else THERMAL_COLOR
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["value"],
                mode=mode,
                name=data_type,
                line={"color": color},
                marker={"color": color, "size": marker_size},
                hovertemplate=(
                    f"%{{x|%Y-%m-%d %H:%M}}<br><b>%{{y:,.2f}}</b> {unit}<extra></extra>"
                ),
            )
        )
        fig.update_layout(
            title=f"{volcano} — {data_type}",
            xaxis_title="Date",
            yaxis_title=f"{data_type} ({unit})",
            height=480,
            hovermode="x unified",
        )
    else:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        so2 = df[df["type"] == "SO2"]
        thermal = df[df["type"] == "Thermal"]
        fig.add_trace(
            go.Scatter(
                x=so2.index,
                y=so2["value"],
                mode=mode,
                name="SO2",
                line={"color": SO2_COLOR},
                marker={"color": SO2_COLOR, "size": marker_size},
                hovertemplate=(
                    f"%{{x|%Y-%m-%d %H:%M}}<br><b>%{{y:,.2f}}</b> {SO2_UNIT}<extra>SO2</extra>"
                ),
            ),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(
                x=thermal.index,
                y=thermal["value"],
                mode=mode,
                name="Thermal",
                line={"color": THERMAL_COLOR},
                marker={"color": THERMAL_COLOR, "size": marker_size},
                hovertemplate=(
                    f"%{{x|%Y-%m-%d %H:%M}}<br><b>%{{y:,.2f}}</b> {THERMAL_UNIT}"
                    "<extra>Thermal</extra>"
                ),
            ),
            secondary_y=True,
        )
        fig.update_yaxes(title_text=f"SO2 ({SO2_UNIT})", secondary_y=False)
        fig.update_yaxes(title_text=f"Thermal ({THERMAL_UNIT})", secondary_y=True)
        fig.update_layout(
            title=f"{volcano} — SO2 vs Thermal",
            xaxis_title="Date",
            height=480,
            hovermode="x unified",
        )

    fig.update_layout(
        modebar={"orientation": "v"},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
    )

    st.plotly_chart(fig, width="stretch")


def main() -> None:
    st.set_page_config(page_title="MOUNTS Dashboard", layout="wide")
    st.markdown(
        '<style>[data-testid="stSidebar"] h1 { padding: 0; }</style>',
        unsafe_allow_html=True,
    )

    df = load_data()
    if df is None:
        render_empty_state()
        return

    volcanoes = sorted(df["name"].unique())

    st.sidebar.title("MOUNTS Dashboard")
    st.sidebar.caption(
        f"v{__version__} · {__author__} · [GitHub]({__url__})"
    )
    volcano = st.sidebar.selectbox("Volcano", volcanoes)
    data_type = st.sidebar.radio(
        "Data type", ["Both", "SO2", "Thermal"], horizontal=True
    )
    chart_style = st.sidebar.radio(
        "Chart style", ["Line", "Scatter"], horizontal=True
    )
    chart_mode = "lines+markers" if chart_style == "Line" else "markers"
    marker_size = st.sidebar.slider(
        "Marker size", min_value=4, max_value=30, value=10
    )

    volcano_df = df[df["name"] == volcano]
    min_date = volcano_df.index.min().date()
    max_date = volcano_df.index.max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        key=f"date_range_{volcano}",
    )

    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh data"):
        refresh_data()
        st.rerun()

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        mask = (volcano_df.index.date >= start) & (volcano_df.index.date <= end)
        volcano_df = volcano_df[mask]

    if data_type != "Both":
        filtered = volcano_df[volcano_df["type"] == data_type]
    else:
        filtered = volcano_df

    code = volcano_df["code"].iloc[0] if len(volcano_df) else "—"
    st.title(f"{volcano}")
    st.caption(f"MOUNTS code: `{code}`")

    if data_type == "Both":
        render_metrics(volcano_df[volcano_df["type"] == "SO2"], "SO2")
        render_metrics(volcano_df[volcano_df["type"] == "Thermal"], "Thermal")
    else:
        render_metrics(filtered, data_type)

    if filtered.empty:
        st.warning("No observations match the current filters.")
        return

    render_chart(filtered, data_type, volcano, chart_mode, marker_size)

    with st.expander("Underlying data", expanded=False):
        st.dataframe(filtered, width="stretch")


if __name__ == "__main__":
    main()
