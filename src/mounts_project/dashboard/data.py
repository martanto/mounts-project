"""Data loading, refresh, and anomaly helpers for the dashboard."""

import os

from mounts_project import MountsProject
from mounts_project.constants import CSV_PATH, XLSX_PATH

import pandas as pd
import streamlit as st


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


@st.cache_data
def compute_anomalies(
    df: pd.DataFrame,
    window: int,
    sigma: float,
) -> pd.DataFrame:
    """Add rolling z-score columns and a spike flag per ``(name, type)`` group.

    Args:
        df: DataFrame indexed by ``datetime`` with at least ``name``, ``type``,
            and ``value`` columns.
        window: Rolling window size in observations.
        sigma: Z-score threshold; rows where ``value > roll_mean + sigma *
            roll_std`` are flagged as spikes.

    Returns:
        A copy of ``df`` with extra ``roll_mean``, ``roll_std``, ``upper``,
        ``is_spike`` columns. Rows with insufficient history (NaN std) are not
        flagged.
    """
    out = df.copy()
    grouped = out.groupby(["name", "type"], group_keys=False)["value"]
    out["roll_mean"] = grouped.transform(lambda s: s.rolling(window).mean())
    out["roll_std"] = grouped.transform(lambda s: s.rolling(window).std())
    out["upper"] = out["roll_mean"] + sigma * out["roll_std"]
    out["is_spike"] = (out["value"] > out["upper"]).fillna(False)
    return out


def recent_slice(df: pd.DataFrame, days: int) -> pd.DataFrame:
    """Return rows from the last ``days`` days, relative to ``df.index.max()``."""
    if df.empty:
        return df
    cutoff = df.index.max() - pd.Timedelta(days=days)
    return df.loc[df.index >= cutoff]
