"""Volcano detail page: per-volcano time series with anomaly, distribution, calendar."""

from mounts_project.constants import (
    SO2_UNIT,
    SO2_COLOR,
    THERMAL_UNIT,
    THERMAL_COLOR,
    ANOMALY_SIGMA_DEFAULT,
    ANOMALY_WINDOW_DEFAULT,
)
from mounts_project.dashboard.data import (
    load_data,
    refresh_data,
    compute_anomalies,
)
from mounts_project.dashboard.components import (
    render_chart,
    render_metrics,
    render_empty_state,
)

import pandas as pd
import streamlit as st
import plotly.graph_objects as go


_DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _distribution_section(df: pd.DataFrame, data_type: str) -> None:
    """Render histogram + box plot of ``value`` per type."""
    st.subheader("Distribution")
    types = ["SO2", "Thermal"] if data_type == "Both" else [data_type]
    cols = st.columns(2)
    with cols[0]:
        hist = go.Figure()
        for t in types:
            sub = df[df["type"] == t]
            if sub.empty:
                continue
            color = SO2_COLOR if t == "SO2" else THERMAL_COLOR
            unit = SO2_UNIT if t == "SO2" else THERMAL_UNIT
            hist.add_trace(
                go.Histogram(
                    x=sub["value"],
                    name=f"{t} ({unit})",
                    marker_color=color,
                    opacity=0.7,
                    nbinsx=40,
                )
            )
        hist.update_layout(
            title="Histogram",
            barmode="overlay",
            height=320,
            xaxis_title="Value",
            yaxis_title="Count",
        )
        st.plotly_chart(hist, width="stretch")
    with cols[1]:
        box = go.Figure()
        for t in types:
            sub = df[df["type"] == t]
            if sub.empty:
                continue
            color = SO2_COLOR if t == "SO2" else THERMAL_COLOR
            unit = SO2_UNIT if t == "SO2" else THERMAL_UNIT
            box.add_trace(
                go.Box(
                    y=sub["value"],
                    name=f"{t} ({unit})",
                    marker_color=color,
                    boxmean=True,
                )
            )
        box.update_layout(title="Box plot", height=320, yaxis_title="Value")
        st.plotly_chart(box, width="stretch")


def _calendar_heatmap(df: pd.DataFrame, data_type: str) -> go.Figure:
    """ISO-week × day-of-week heatmap of daily max value."""
    unit = SO2_UNIT if data_type == "SO2" else THERMAL_UNIT
    sub = df[df["type"] == data_type]
    if sub.empty:
        return go.Figure().update_layout(
            title=f"No {data_type} observations", height=260
        )
    daily = sub.assign(day=sub.index.normalize()).groupby("day")["value"].max()
    iso = daily.index.isocalendar()
    pivot = (
        pd.DataFrame(
            {
                "year_week": iso["year"].astype(str)
                + "-W"
                + iso["week"].astype(str).str.zfill(2),
                "dow": iso["day"] - 1,
                "value": daily.to_numpy(),
            }
        )
        .pivot_table(index="dow", columns="year_week", values="value", aggfunc="max")
        .reindex(range(7))
    )
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=[_DOW_LABELS[i] for i in pivot.index],
            colorscale="Oranges" if data_type == "SO2" else "Reds",
            colorbar={"title": unit},
            hovertemplate=(
                f"%{{x}} · %{{y}}<br><b>%{{z:,.2f}}</b> {unit}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"{data_type} — daily max calendar",
        xaxis_title="ISO week",
        yaxis_title="Day",
        height=260,
    )
    return fig


def render_detail_page() -> None:
    """Entry point for the Volcano detail page."""
    df = load_data()
    if df is None:
        render_empty_state()
        return

    volcanoes = sorted(df["name"].unique())

    volcano = st.sidebar.selectbox("Volcano", volcanoes)
    data_type = st.sidebar.radio(
        "Data type", ["Both", "SO2", "Thermal"], horizontal=True
    )
    chart_style = st.sidebar.radio(
        "Chart style", ["Line", "Scatter"], horizontal=True
    )
    chart_mode = "lines+markers" if chart_style == "Line" else "markers"
    marker_size = st.sidebar.slider("Marker size", min_value=4, max_value=30, value=10)

    volcano_df = df[df["name"] == volcano]
    min_date = volcano_df.index.min().date()
    max_date = volcano_df.index.max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        key=f"date_range_{volcano}",
    )

    st.sidebar.markdown("---")
    show_anomaly = st.sidebar.toggle("Anomaly overlay", value=False)
    anomaly_window = ANOMALY_WINDOW_DEFAULT
    anomaly_sigma = ANOMALY_SIGMA_DEFAULT
    if show_anomaly:
        anomaly_window = st.sidebar.slider(
            "Rolling window (obs)",
            min_value=5,
            max_value=60,
            value=ANOMALY_WINDOW_DEFAULT,
        )
        anomaly_sigma = st.sidebar.slider(
            "Sigma (σ)",
            min_value=1.0,
            max_value=4.0,
            value=ANOMALY_SIGMA_DEFAULT,
            step=0.1,
        )

    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh data"):
        refresh_data()
        st.rerun()

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        ts_start = pd.Timestamp(start)
        ts_end = pd.Timestamp(end) + pd.Timedelta(days=1)
        volcano_df = volcano_df[
            (volcano_df.index >= ts_start) & (volcano_df.index < ts_end)
        ]

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

    anomaly_df: pd.DataFrame | None = None
    if show_anomaly:
        anomaly_df = compute_anomalies(filtered, anomaly_window, anomaly_sigma)

    render_chart(filtered, data_type, volcano, chart_mode, marker_size, anomaly_df)

    _distribution_section(filtered, data_type)

    st.subheader("Calendar heatmap")
    types = ["SO2", "Thermal"] if data_type == "Both" else [data_type]
    for t in types:
        st.plotly_chart(_calendar_heatmap(filtered, t), width="stretch")

    with st.expander("Underlying data", expanded=False):
        st.dataframe(filtered, width="stretch")
