"""Compare page: multi-volcano overlay and 4×3 small-multiples grid."""

from mounts_project.constants import (
    SO2_UNIT,
    THERMAL_UNIT,
    RECENT_DAYS_DEFAULT,
)
from mounts_project.dashboard.data import load_data, recent_slice
from mounts_project.dashboard.components import render_empty_state

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _default_selection(df: pd.DataFrame, data_type: str, n: int = 4) -> list[str]:
    """Pick the ``n`` most-active volcanoes for ``data_type`` over the recent window."""
    recent = recent_slice(df, RECENT_DAYS_DEFAULT)
    sub = recent[recent["type"] == data_type]
    if sub.empty:
        return sorted(df["name"].unique())[:n]
    ranking = sub.groupby("name")["value"].max().sort_values(ascending=False)
    return ranking.head(n).index.tolist()


def _overlay_figure(
    df: pd.DataFrame,
    selected: list[str],
    data_type: str,
) -> go.Figure:
    """One Scatter trace per selected volcano."""
    unit = SO2_UNIT if data_type == "SO2" else THERMAL_UNIT
    fig = go.Figure()
    for name in selected:
        sub = df[(df["name"] == name) & (df["type"] == data_type)]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub.index,
                y=sub["value"],
                mode="lines+markers",
                name=name,
                marker={"size": 5},
                hovertemplate=(
                    f"%{{x|%Y-%m-%d %H:%M}}<br><b>%{{y:,.2f}}</b> {unit}<extra>{name}</extra>"
                ),
            )
        )
    fig.update_layout(
        title=f"Overlay — {data_type}",
        xaxis_title="Date",
        yaxis_title=f"{data_type} ({unit})",
        height=520,
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
    )
    return fig


def _small_multiples_figure(df: pd.DataFrame, data_type: str) -> go.Figure:
    """4×3 grid of all volcanoes for the selected type, with a shared x-axis."""
    unit = SO2_UNIT if data_type == "SO2" else THERMAL_UNIT
    volcanoes = sorted(df["name"].unique())
    n = len(volcanoes)
    cols = 3
    rows = (n + cols - 1) // cols
    fig = make_subplots(
        rows=rows,
        cols=cols,
        shared_xaxes=True,
        subplot_titles=volcanoes,
        vertical_spacing=0.06,
        horizontal_spacing=0.04,
    )
    for i, name in enumerate(volcanoes):
        row = i // cols + 1
        col = i % cols + 1
        sub = df[(df["name"] == name) & (df["type"] == data_type)]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub.index,
                y=sub["value"],
                mode="lines",
                name=name,
                line={"width": 1.2},
                hovertemplate=(
                    f"%{{x|%Y-%m-%d}}<br><b>%{{y:,.2f}}</b> {unit}<extra>{name}</extra>"
                ),
                showlegend=False,
            ),
            row=row,
            col=col,
        )
    fig.update_layout(
        title=f"Small multiples — {data_type} ({unit})",
        height=180 * rows,
        margin={"t": 60, "b": 30, "l": 40, "r": 20},
    )
    return fig


def render_compare_page() -> None:
    """Entry point for the Compare page."""
    df = load_data()
    if df is None:
        render_empty_state()
        return

    data_type = st.sidebar.radio(
        "Data type", ["SO2", "Thermal"], horizontal=True, key="compare_type"
    )
    volcanoes = sorted(df["name"].unique())
    default = _default_selection(df, data_type)
    selected = st.sidebar.multiselect(
        "Volcanoes (overlay)",
        options=volcanoes,
        default=default,
    )
    min_date = df.index.min().date()
    max_date = df.index.max().date()
    date_range = st.sidebar.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="compare_date_range",
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        ts_start = pd.Timestamp(start)
        ts_end = pd.Timestamp(end) + pd.Timedelta(days=1)
        df = df[(df.index >= ts_start) & (df.index < ts_end)]

    st.title("Compare")
    st.caption(
        f"{data_type} · {len(selected)} of {len(volcanoes)} selected for overlay"
    )

    overlay_tab, small_tab = st.tabs(["Overlay", "Small multiples"])
    with overlay_tab:
        if not selected:
            st.info("Pick at least one volcano in the sidebar to draw the overlay.")
        else:
            st.plotly_chart(
                _overlay_figure(df, selected, data_type), width="stretch"
            )
    with small_tab:
        st.plotly_chart(_small_multiples_figure(df, data_type), width="stretch")
