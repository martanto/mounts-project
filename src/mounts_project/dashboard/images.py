"""Resolve downloaded MOUNTS image paths from the dashboard DataFrame."""

import os

from mounts_project.utils import slugify

import pandas as pd
import streamlit as st


@st.cache_data
def resolve_image_paths(df: pd.DataFrame, images_root: str) -> pd.DataFrame:
    """Add ``local_path`` and ``exists`` columns to ``df``.

    Builds the on-disk image path for every row whose ``graph`` column is
    non-empty, mirroring the layout produced by
    :func:`mounts_project.download.download_images_from_dict`::

        <images_root>/<slugify(name)>/<type.lower()>/<basename(graph)>

    Then stamps an ``exists`` flag from :func:`os.path.exists` so the caller
    can silently skip files that were never downloaded or have been removed.

    Args:
        df: Slice of the dashboard DataFrame with ``name``, ``type``, and
            ``graph`` columns. Typically already filtered by volcano, date
            range, and data type.
        images_root: Absolute path of the ``output/images`` directory.

    Returns:
        A copy of ``df`` with two extra columns: ``local_path`` (str) and
        ``exists`` (bool). Rows whose ``graph`` value is null or empty are
        dropped. If ``df`` has no ``graph`` column, the input is returned with
        ``local_path=None`` and ``exists=False`` so older CSV exports still load.
    """
    if "graph" not in df.columns:
        return df.assign(local_path=None, exists=False)

    out = df[df["graph"].notna() & (df["graph"] != "")].copy()
    out["local_path"] = [
        os.path.join(
            images_root,
            slugify(name),
            kind.lower(),
            os.path.basename(graph),
        )
        for name, kind, graph in zip(
            out["name"], out["type"], out["graph"], strict=True
        )
    ]
    out["exists"] = out["local_path"].apply(os.path.exists)
    return out
