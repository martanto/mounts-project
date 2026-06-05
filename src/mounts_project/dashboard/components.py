"""Shared rendering helpers used by every dashboard page."""

from mounts_project import __url__, __author__, __version__
from mounts_project.constants import (
    SO2_UNIT,
    SO2_COLOR,
    OUTPUT_DIR,
    THERMAL_UNIT,
    THERMAL_COLOR,
)
from mounts_project.dashboard.data import refresh_data

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def render_sidebar_header() -> None:
    """Render the sidebar title + version/author/GitHub caption."""
    st.sidebar.title("MOUNTS Dashboard")
    st.sidebar.caption(f"v{__version__} · {__author__} · [GitHub]({__url__})")


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


def _add_anomaly_traces(
    fig: go.Figure,
    df: pd.DataFrame,
    color: str,
    secondary_y: bool | None = None,
) -> None:
    """Append rolling mean, upper band, and spike markers to ``fig``."""
    kwargs: dict = {}
    if secondary_y is not None:
        kwargs["secondary_y"] = secondary_y
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["roll_mean"],
            mode="lines",
            name="Rolling mean",
            line={"color": color, "dash": "dash", "width": 1},
            hoverinfo="skip",
            showlegend=False,
        ),
        **kwargs,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["upper"],
            mode="lines",
            name="Upper (μ + N·σ)",
            line={"color": color, "dash": "dot", "width": 1},
            opacity=0.5,
            hoverinfo="skip",
            showlegend=False,
        ),
        **kwargs,
    )
    spikes = df[df["is_spike"]]
    if not spikes.empty:
        fig.add_trace(
            go.Scatter(
                x=spikes.index,
                y=spikes["value"],
                mode="markers",
                name="Spike",
                marker={
                    "color": "crimson",
                    "size": 12,
                    "symbol": "diamond-open",
                    "line": {"width": 2},
                },
                hovertemplate="%{x|%Y-%m-%d %H:%M}<br><b>%{y:,.2f}</b><extra>Spike</extra>",
                showlegend=False,
            ),
            **kwargs,
        )


def render_chart(
    df: pd.DataFrame,
    data_type: str,
    volcano: str,
    mode: str,
    marker_size: int,
    anomaly_df: pd.DataFrame | None = None,
) -> None:
    """Render the Plotly time series for the selected type(s).

    When ``anomaly_df`` is provided (already restricted to the same volcano +
    date window as ``df``), the rolling mean, upper threshold band, and spike
    markers are overlaid on the figure. For the dual-axis ``"Both"`` view, the
    overlay is split per axis using the existing ``type`` column.
    """
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
        if anomaly_df is not None and not anomaly_df.empty:
            _add_anomaly_traces(fig, anomaly_df, color)
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
        if anomaly_df is not None and not anomaly_df.empty:
            so2_anom = anomaly_df[anomaly_df["type"] == "SO2"]
            thermal_anom = anomaly_df[anomaly_df["type"] == "Thermal"]
            if not so2_anom.empty:
                _add_anomaly_traces(fig, so2_anom, SO2_COLOR, secondary_y=False)
            if not thermal_anom.empty:
                _add_anomaly_traces(fig, thermal_anom, THERMAL_COLOR, secondary_y=True)
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
