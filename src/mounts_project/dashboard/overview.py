"""Overview page: ranking leaderboard, cross-volcano heatmap, spikes feed."""

from mounts_project.constants import (
    SO2_UNIT,
    THERMAL_UNIT,
    RECENT_DAYS_DEFAULT,
    ANOMALY_SIGMA_DEFAULT,
    ANOMALY_WINDOW_DEFAULT,
)
from mounts_project.dashboard.data import (
    load_data,
    recent_slice,
    refresh_data,
    compute_anomalies,
)
from mounts_project.dashboard.components import render_empty_state

import pandas as pd
import streamlit as st
import plotly.graph_objects as go


def _ranking_table(recent: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """Build the per-volcano leaderboard for one measurement type."""
    sub = recent[recent["type"] == data_type]
    if sub.empty:
        return pd.DataFrame(columns=["volcano", "latest", "max", "mean", "n_obs"])
    grouped = sub.groupby("name")["value"]
    table = pd.DataFrame(
        {
            "latest": sub.sort_index().groupby("name").last()["value"],
            "max": grouped.max(),
            "mean": grouped.mean(),
            "n_obs": grouped.count(),
        }
    )
    table.index.name = "volcano"
    return table.sort_values("max", ascending=False).round(2)


def _cross_volcano_heatmap(recent: pd.DataFrame, data_type: str) -> go.Figure:
    """Build a daily-max heatmap (volcano × date) for one measurement type."""
    sub = recent[recent["type"] == data_type]
    unit = SO2_UNIT if data_type == "SO2" else THERMAL_UNIT
    if sub.empty:
        return go.Figure().update_layout(
            title=f"No {data_type} observations in this window", height=360
        )
    daily = (
        sub.assign(day=sub.index.normalize())
        .pivot_table(index="name", columns="day", values="value", aggfunc="max")
        .sort_index()
    )
    fig = go.Figure(
        data=go.Heatmap(
            z=daily.to_numpy(),
            x=daily.columns,
            y=daily.index,
            colorscale="Oranges" if data_type == "SO2" else "Reds",
            colorbar={"title": unit},
            hovertemplate=(
                f"%{{y}}<br>%{{x|%Y-%m-%d}}<br><b>%{{z:,.2f}}</b> {unit}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"{data_type} daily max — last {len(daily.columns)} days",
        xaxis_title="Date",
        yaxis_title="Volcano",
        height=420,
    )
    return fig


def _spikes_feed(recent: pd.DataFrame, window: int, sigma: float) -> pd.DataFrame:
    """Return the most recent flagged spikes within the overview window."""
    if recent.empty:
        return pd.DataFrame()
    anom = compute_anomalies(recent, window, sigma)
    spikes = anom[anom["is_spike"]].copy()
    if spikes.empty:
        return spikes
    spikes = spikes.sort_index(ascending=False).head(50)
    out = spikes[["name", "type", "value", "upper"]].copy()
    out.insert(0, "datetime", spikes.index)
    out = out.rename(columns={"upper": "threshold"}).round(2)
    return out.reset_index(drop=True)


def render_overview_page() -> None:
    """Entry point for the Overview page."""
    df = load_data()
    if df is None:
        render_empty_state()
        return

    days = st.sidebar.slider(
        "Recent window (days)",
        min_value=7,
        max_value=90,
        value=RECENT_DAYS_DEFAULT,
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("Refresh data"):
        refresh_data()
        st.rerun()

    recent = recent_slice(df, days)
    st.title("Overview")
    st.caption(
        f"Last {days} days · {len(df['name'].unique())} volcanoes · "
        f"{len(recent):,} observations"
    )

    st.subheader("Activity leaderboard")
    cols = st.columns(2)
    for col, data_type, unit in (
        (cols[0], "SO2", SO2_UNIT),
        (cols[1], "Thermal", THERMAL_UNIT),
    ):
        with col:
            st.markdown(f"**{data_type}** ({unit})")
            st.dataframe(_ranking_table(recent, data_type), width="stretch")

    st.subheader("Cross-volcano heatmap")
    so2_tab, thermal_tab = st.tabs(["SO2", "Thermal"])
    with so2_tab:
        st.plotly_chart(_cross_volcano_heatmap(recent, "SO2"), width="stretch")
    with thermal_tab:
        st.plotly_chart(_cross_volcano_heatmap(recent, "Thermal"), width="stretch")

    st.subheader("Recent spikes")
    feed = _spikes_feed(recent, ANOMALY_WINDOW_DEFAULT, ANOMALY_SIGMA_DEFAULT)
    if feed.empty:
        st.info(
            f"No spikes flagged in the last {days} days "
            f"(window={ANOMALY_WINDOW_DEFAULT}, σ={ANOMALY_SIGMA_DEFAULT})."
        )
    else:
        st.caption(
            f"Rolling z-score (window={ANOMALY_WINDOW_DEFAULT}, "
            f"σ={ANOMALY_SIGMA_DEFAULT}). Top {len(feed)} of the last 50."
        )
        st.dataframe(feed, width="stretch", hide_index=True)
